"""Rasterize the Lunara dial and its moon-phase disc.

The bitmap holds everything that does not change with the day or the
language: the ivory ground, hour track, Roman numerals, window frames,
the LUNARA name, and the moon sub-dial chrome. Month, weekday, date,
side legends, and battery are drawn later, on the watch.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

from dial_layout import BRAND, DialLayout, clock_angle

IVORY = (244, 237, 224, 255)
INK = (42, 38, 34, 255)
QUIET = (96, 88, 78, 255)
HAIRLINE = (120, 112, 102, 255)
NAVY = (10, 22, 48, 255)
GOLD = (228, 206, 164, 255)

_DIDOT_BOLD = "/System/Library/Fonts/Supplemental/Didot.ttc"
_BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def render_dial(size: int) -> Image.Image:
    """Ivory dial bitmap. `size` is the even screen width in pixels."""
    layout = DialLayout(size)
    scale = 3
    big = _paint_dial(DialLayout(size * scale))
    return big.resize((layout.size, layout.size), Image.Resampling.LANCZOS)


def render_moon(size: int, phase: float) -> Image.Image:
    """The moon well for one phase. 0 is new, 0.5 is full. Values wrap into 0–1.

    The moon travels left to right through the month and is centered when full.
    """
    if size < 2:
        raise ValueError(f"moon size must be at least 2, got {size!r}")
    phase = phase % 1.0
    scale = 4
    big = _paint_moon(size * scale, phase)
    image = big.resize((size, size), Image.Resampling.LANCZOS)
    _paint_stars(image.load(), size, phase)
    return image


def _paint_dial(layout: DialLayout) -> Image.Image:
    image = Image.new("RGBA", (layout.size, layout.size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse((0, 0, layout.size - 1, layout.size - 1), fill=IVORY)

    _minute_ticks(draw, layout)
    _hour_ticks(draw, layout)
    _romans(image, layout)
    _windows(draw, layout)
    _brand(image, layout)
    _subdial(image, draw, layout)
    return image


def _minute_ticks(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    outer = layout.radius * 0.978
    inner = layout.radius * 0.958
    long_inner = layout.radius * 0.944
    for minute in range(60):
        angle = clock_angle(minute, 60)
        start = long_inner if minute % 5 == 0 else inner
        _tick(draw, layout.center, angle, start, outer, 1, QUIET)


def _hour_ticks(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    outer = layout.radius * 0.90
    inner = layout.radius * 0.855
    width = max(1, int(layout.radius * 0.005))
    for hour in (1, 2, 4, 5, 7, 8, 10, 11):
        _tick(draw, layout.center, clock_angle(hour, 12), inner, outer, width, INK)


def _romans(image: Image.Image, layout: DialLayout) -> None:
    font = _font("roman", layout.radius * 0.092)
    for mark in layout.romans():
        _text(image, mark.text, (mark.x, mark.y), font, INK)


def _windows(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    stroke = max(1, int(layout.radius * 0.0035))
    for window in (layout.weekday_window, layout.date_window):
        box = (
            window.left,
            window.center[1] - window.half_h,
            window.right,
            window.center[1] + window.half_h,
        )
        draw.rectangle(box, outline=INK, width=stroke)


def brand_half_width(layout: DialLayout) -> float:
    """Half the tracked width of LUNARA, in pixels."""
    font = _font("roman", layout.radius * 0.052)
    tracking = layout.radius * 0.020
    widths = [font.getbbox(char)[2] - font.getbbox(char)[0] for char in BRAND]
    return (sum(widths) + tracking * (len(BRAND) - 1)) / 2.0


def _brand(image: Image.Image, layout: DialLayout) -> None:
    font = _font("roman", layout.radius * 0.052)
    tracking = layout.radius * 0.020
    _tracked(image, BRAND, layout.brand_center, font, INK, tracking)


def _subdial(image: Image.Image, draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    cx, cy = layout.subdial_center
    ring = layout.date_ring_radius
    well = layout.moon_well_radius
    stroke = max(1, int(layout.radius * 0.007))

    numeral_font = _font("text", layout.radius * 0.030)
    sample = numeral_font.getbbox("30")
    numeral_pad = (sample[3] - sample[1]) * 0.55
    outer = ring + numeral_pad
    draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), outline=QUIET, width=stroke)
    draw.ellipse(
        (cx - well, cy - well, cx + well, cy + well),
        fill=NAVY,
        outline=HAIRLINE,
        width=max(1, stroke - 1),
    )

    for mark in layout.date_numerals():
        _text(image, mark.text, (mark.x, mark.y), numeral_font, QUIET)


_MOON_RADIUS = 0.36
_MOON_TRAVEL = 1.05

# A few points of light, not a field of stickers.
_STARS = (
    (0.28, 0.24, 0.7),
    (0.72, 0.22, 1.0),
    (0.18, 0.62, 0.45),
    (0.80, 0.58, 0.55),
    (0.40, 0.78, 0.8),
    (0.62, 0.74, 0.4),
)

# Dark maria, in moon-local coordinates from -1 to 1.
_MARIA = (
    (-0.12, -0.02, 0.40, 0.30, 0.28),
    (0.24, 0.16, 0.22, 0.16, 0.18),
    (-0.30, 0.34, 0.18, 0.14, 0.14),
    (0.04, -0.34, 0.22, 0.13, 0.12),
    (0.32, -0.22, 0.12, 0.10, 0.10),
)


def _paint_moon(size: int, phase: float) -> Image.Image:
    """Starry well. The moon crosses left to right; full moon sits in the middle."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()
    cx = cy = (size - 1) / 2.0
    radius = (size - 1) / 2.0
    moon_radius = radius * _MOON_RADIUS
    travel = radius * _MOON_TRAVEL
    moon_x = cx + (phase - 0.5) * 2.0 * travel
    moon_y = cy
    light_x = math.sin(2.0 * math.pi * phase)
    light_z = -math.cos(2.0 * math.pi * phase)
    radius2 = radius * radius
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist2 = dx * dx + dy * dy
            if dist2 > radius2:
                continue
            dist = math.sqrt(dist2)
            pixels[x, y] = _sky_pixel(dist / radius)
    _paint_moon_body(pixels, size, moon_x, moon_y, moon_radius, light_x, light_z, cx, cy, radius)
    return image


def _sky_pixel(unit: float) -> tuple[int, int, int, int]:
    zenith = (16, 32, 62)
    rim = (8, 16, 36)
    mix = unit * unit
    red = int(zenith[0] + (rim[0] - zenith[0]) * mix)
    green = int(zenith[1] + (rim[1] - zenith[1]) * mix)
    blue = int(zenith[2] + (rim[2] - zenith[2]) * mix)
    return (red, green, blue, 255)


def _paint_stars(pixels, size: int, phase: float) -> None:
    cx = cy = (size - 1) / 2.0
    radius = (size - 1) / 2.0
    moon_radius = radius * _MOON_RADIUS
    moon_x = cx + (phase - 0.5) * 2.0 * radius * _MOON_TRAVEL
    for fx, fy, brightness in _STARS:
        sx = int(round(fx * (size - 1)))
        sy = int(round(fy * (size - 1)))
        if (sx - cx) ** 2 + (sy - cy) ** 2 > (radius * 0.90) ** 2:
            continue
        if (sx - moon_x) ** 2 + (sy - cy) ** 2 < (moon_radius * 0.92) ** 2:
            continue
        if not (0 <= sx < size and 0 <= sy < size):
            continue
        shine = int(200 + 40 * brightness)
        pixels[sx, sy] = (shine, shine, min(255, shine + 8), 255)


def _paint_moon_body(pixels, size, moon_x, moon_y, moon_radius, light_x, light_z, cx, cy, well_radius) -> None:
    radius2 = moon_radius * moon_radius
    x0 = max(0, int(moon_x - moon_radius))
    y0 = max(0, int(moon_y - moon_radius))
    x1 = min(size - 1, int(moon_x + moon_radius) + 1)
    y1 = min(size - 1, int(moon_y + moon_radius) + 1)
    well2 = well_radius * well_radius
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 > well2:
                continue
            dx = x - moon_x
            dy = y - moon_y
            dist2 = dx * dx + dy * dy
            if dist2 > radius2:
                continue
            height = math.sqrt(radius2 - dist2)
            ndotl = (dx * light_x + height * light_z) / moon_radius
            sun = max(0.0, ndotl)
            soft = sun * sun * (3.0 - 2.0 * min(1.0, sun))
            limb = 0.62 + 0.38 * (height / moon_radius)
            tone = _moon_tone(dx / moon_radius, dy / moon_radius)
            value = soft * limb * tone
            # Pale gold, the way a moon complication is finished. The night side stays sky.
            sky = pixels[x, y]
            red = int(sky[0] + (236 - sky[0]) * value)
            green = int(sky[1] + (214 - sky[1]) * value)
            blue = int(sky[2] + (168 - sky[2]) * value)
            pixels[x, y] = (min(255, red), min(255, green), min(255, blue), 255)


def _moon_tone(u: float, v: float) -> float:
    shade = 1.0
    shade -= 0.06 * math.sin(u * 11.0 + 2.0) * math.sin(v * 8.0 - 1.0)
    for mx, my, rx, ry, depth in _MARIA:
        nx = (u - mx) / rx
        ny = (v - my) / ry
        disc = nx * nx + ny * ny
        if disc < 1.0:
            shade -= depth * (1.0 - disc)
    return max(0.62, min(1.08, shade))


def _tick(draw, origin, angle, inner, outer, width, color) -> None:
    x0 = origin[0] + inner * math.cos(angle)
    y0 = origin[1] + inner * math.sin(angle)
    x1 = origin[0] + outer * math.cos(angle)
    y1 = origin[1] + outer * math.sin(angle)
    draw.line((x0, y0, x1, y1), fill=color, width=width)


def _text(image, text, xy, font, fill) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).text(xy, text, font=font, fill=fill, anchor="mm")
    image.alpha_composite(overlay)


def _tracked(image, text, xy, font, fill, tracking) -> None:
    widths = []
    for char in text:
        box = font.getbbox(char)
        widths.append(box[2] - box[0])
    total = sum(widths) + tracking * (len(text) - 1)
    cursor = xy[0] - total / 2.0
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for char, width in zip(text, widths):
        draw.text((cursor + width / 2.0, xy[1]), char, font=font, fill=fill, anchor="mm")
        cursor += width + tracking
    image.alpha_composite(overlay)


def _font(kind: str, size: float) -> ImageFont.FreeTypeFont:
    pixels = max(8, int(round(size)))
    key = (kind, pixels)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    if kind == "display":
        font = ImageFont.truetype(_DIDOT_BOLD, pixels, index=2)
    elif kind == "roman":
        font = ImageFont.truetype(_DIDOT_BOLD, pixels, index=0)
    else:
        font = ImageFont.truetype(_BASKERVILLE, pixels, index=0)
    _FONT_CACHE[key] = font
    return font
