"""Rasterize the Lunara dial and its moon-phase disc.

The bitmap holds everything that does not change with the day or the
language: the ivory ground, hour batons, Roman numerals, window frames,
the LUNARA name, and the moon sub-dial. Month, weekday, date, the
perpetual legend, and the battery are drawn later, on the watch.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

from battery_style import battery_color
from dial_layout import BRAND, DialLayout, clock_angle

IVORY = (246, 240, 228, 255)
INK = (28, 26, 22, 255)
RING = (48, 44, 38, 255)
NAVY = (8, 18, 42, 255)
GOLD = (196, 164, 106, 255)

_TIMES = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
_TIMES_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"

_BRAND_SIZE = 0.054
_BRAND_TRACK = 0.004

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def render_dial(size: int) -> Image.Image:
    """Ivory dial bitmap. `size` is the even screen width in pixels.

    The ground is supersampled. Type and frame edges are drawn at final
    size so the numerals stay crisp.
    """
    layout = DialLayout(size)
    big = _paint_ground(DialLayout(size * 3))
    image = big.resize((layout.size, layout.size), Image.Resampling.LANCZOS)
    _windows(ImageDraw.Draw(image), layout)
    _romans(image, layout)
    _brand(image, layout)
    _date_numerals(image, layout)
    return image


def render_moon(size: int, phase: float) -> Image.Image:
    """Moon disc behind the round window. 0 is new, 0.5 is full.

    The disc slides left to right over the month, so it is hidden outside the
    window at new moon and sits fully inside at full moon. Only the lit face
    is drawn; the dark side is the same sky as the well.
    """
    if size < 2:
        raise ValueError(f"moon size must be at least 2, got {size!r}")
    phase = phase % 1.0
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _paint_moon(image.load(), size, phase)
    _paint_stars(image.load(), size, phase)
    return image


def paint_hands(image: Image.Image, layout: DialLayout) -> None:
    """10:10 feuille hands. Long enough to reach the hour batons, clear of the windows."""
    scale = 3
    big = Image.new("RGBA", (image.width * scale, image.height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    cx = layout.center[0] * scale
    cy = layout.center[1] * scale
    radius = layout.radius * scale
    minute = -math.pi / 2.0 + (10.0 / 60.0) * math.tau
    hour = -math.pi / 2.0 + (10.0 / 12.0) * math.tau + (10.0 / 60.0) * (math.pi / 6.0)
    _taper(draw, cx, cy, hour, radius * 0.58, radius * 0.14, radius * 0.012)
    _taper(draw, cx, cy, minute, radius * 0.74, radius * 0.16, radius * 0.007)
    cap = max(2.0, radius * 0.016)
    draw.ellipse((cx - cap, cy - cap, cx + cap, cy + cap), fill=GOLD)
    image.alpha_composite(big.resize(image.size, Image.Resampling.LANCZOS))


def _paint_ground(layout: DialLayout) -> Image.Image:
    image = Image.new("RGBA", (layout.size, layout.size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, layout.size - 1, layout.size - 1), fill=IVORY)
    _hour_ticks(draw, layout)
    _window_floors(draw, layout)
    _subdial_rings(draw, layout)
    return image


def _hour_ticks(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    outer = layout.radius * 0.88
    inner = layout.radius * 0.74
    width = max(2, int(layout.radius * 0.012))
    for hour in (1, 2, 4, 5, 7, 8, 10, 11):
        _tick(draw, layout.center, clock_angle(hour, 12), inner, outer, width, INK)


def _romans(image: Image.Image, layout: DialLayout) -> None:
    font = _font("roman", layout.radius * 0.105)
    shade = (186, 176, 160, 255)
    shift = max(1, int(layout.radius * 0.004))
    for mark in layout.romans():
        _text(image, mark.text, (mark.x + shift, mark.y + shift), font, shade)
        _text(image, mark.text, (mark.x, mark.y), font, INK)


def _window_box(window) -> tuple[float, float, float, float]:
    return (
        window.left,
        window.center[1] - window.half_h,
        window.right,
        window.center[1] + window.half_h,
    )


def _window_floors(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    for window in (layout.month_window, layout.weekday_window):
        x0, y0, x1, y1 = _window_box(window)
        edge = max(1, int(layout.radius * 0.006))
        draw.rectangle((x0, y0, x1, y1), fill=(236, 230, 216, 255))
        draw.line((x0, y0, x1, y0), fill=(120, 108, 92, 255), width=edge)
        draw.line((x0, y0, x0, y1), fill=(120, 108, 92, 255), width=edge)
        draw.line((x0, y1, x1, y1), fill=(255, 252, 246, 255), width=edge)
        draw.line((x1, y0, x1, y1), fill=(255, 252, 246, 255), width=edge)


def _windows(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    """One-pixel frame, drawn at final size so the recess stays sharp."""
    for window in (layout.month_window, layout.weekday_window):
        draw.rectangle(_window_box(window), outline=INK, width=1)


def brand_half_width(layout: DialLayout) -> float:
    """Half the tracked width of LUNARA, in pixels."""
    font = _font("roman", layout.radius * _BRAND_SIZE)
    tracking = layout.radius * _BRAND_TRACK
    widths = [font.getbbox(char)[2] - font.getbbox(char)[0] for char in BRAND]
    return (sum(widths) + tracking * (len(BRAND) - 1)) / 2.0


def _brand(image: Image.Image, layout: DialLayout) -> None:
    font = _font("roman", layout.radius * _BRAND_SIZE)
    tracking = layout.radius * _BRAND_TRACK
    _tracked(image, BRAND, layout.brand_center, font, INK, tracking)


_ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def _subdial_rings(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    cx, cy = layout.subdial_center
    ring = layout.date_ring_radius
    well = layout.moon_well_radius
    outer = ring + layout.radius * 0.048
    draw.ellipse((cx - well, cy - well, cx + well, cy + well), fill=NAVY)
    draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), outline=INK, width=max(1, int(layout.radius * 0.004)))


def _date_numerals(image: Image.Image, layout: DialLayout) -> None:
    cx, cy = layout.subdial_center
    ring = layout.date_ring_radius
    font = _font("sans", layout.radius * 0.038)
    inset = ring - layout.radius * 0.020
    for mark in layout.date_numerals():
        scale = inset / ring
        _text(image, mark.text, (cx + (mark.x - cx) * scale, cy + (mark.y - cy) * scale), font, INK)


# The disc is smaller than the window so full moon still shows a rim of sky.
# Travel of one window radius plus the moon radius parks a new moon just outside.
_MOON_RADIUS = 0.62
_MOON_TRAVEL = 1.62
_STAR = (248, 220, 150, 255)
# Darker patches, in moon-radius units, so the face reads as a moon.
_MARIA = (
    (-0.22, -0.10, 0.28, 0.18, 0.28),
    (0.18, 0.16, 0.20, 0.14, 0.22),
    (-0.05, 0.28, 0.16, 0.10, 0.16),
    (0.30, -0.22, 0.12, 0.10, 0.18),
)

_STARS = (
    (0.22, 0.28),
    (0.78, 0.24),
    (0.50, 0.16),
    (0.30, 0.72),
    (0.72, 0.70),
    (0.16, 0.52),
    (0.84, 0.48),
)


def _paint_moon(pixels, size: int, phase: float) -> None:
    """Navy window. The moon is clipped by it, and the unlit side is left as sky."""
    cx = cy = (size - 1) / 2.0
    radius = (size - 1) / 2.0
    moon_x, moon_y, moon_radius = _moon_place(cx, cy, radius, phase)
    radius2 = radius * radius
    moon2 = moon_radius * moon_radius
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy > radius2:
                continue
            pixels[x, y] = NAVY
            mx = x - moon_x
            my = y - moon_y
            if moon_radius <= 0 or mx * mx + my * my > moon2:
                continue
            u = mx / moon_radius
            v = my / moon_radius
            if _phase_lit(u, v, phase):
                pixels[x, y] = _moon_tone(u, v)


def _phase_lit(u: float, v: float, phase: float) -> bool:
    """Northern-hemisphere limb. Waxing lights the right side, waning the left."""
    edge = math.sqrt(max(0.0, 1.0 - v * v))
    sweep = math.cos(2.0 * math.pi * phase)
    if phase <= 0.5:
        return u > sweep * edge
    return u < -sweep * edge


def _moon_tone(u: float, v: float):
    """Warm gray face with a few darker maria and a darker limb."""
    disc = math.sqrt(u * u + v * v)
    shade = 0.78 + 0.22 * math.sqrt(max(0.0, 1.0 - disc * disc))
    for mx, my, rx, ry, depth in _MARIA:
        nx = (u - mx) / rx
        ny = (v - my) / ry
        inside = nx * nx + ny * ny
        if inside < 1.0:
            shade -= depth * (1.0 - inside)
    shade = max(0.55, min(1.0, shade))
    return (int(236 * shade), int(226 * shade), int(198 * shade), 255)


def _moon_place(cx, cy, radius, phase):
    travel = radius * _MOON_TRAVEL
    moon_x = cx + (phase - 0.5) * 2.0 * travel
    return moon_x, cy, radius * _MOON_RADIUS


def _paint_stars(pixels, size: int, phase: float) -> None:
    cx = cy = (size - 1) / 2.0
    radius = (size - 1) / 2.0
    moon_x, moon_y, moon_radius = _moon_place(cx, cy, radius, phase)
    for fx, fy in _STARS:
        sx = int(round(fx * (size - 1)))
        sy = int(round(fy * (size - 1)))
        if (sx - moon_x) ** 2 + (sy - moon_y) ** 2 < (moon_radius * 1.05) ** 2:
            continue
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            px = sx + dx
            py = sy + dy
            if not (0 <= px < size and 0 <= py < size):
                continue
            if (px - cx) ** 2 + (py - cy) ** 2 > (radius * 0.90) ** 2:
                continue
            pixels[px, py] = _STAR


def paint_embossed(image: Image.Image, text: str, xy, font, fill, tracking: float = 0) -> None:
    """Raised letters: a light edge above-left and a shadow below-right."""
    shift = max(1, int(getattr(font, "size", 12) * 0.08))
    highlight = (255, 252, 246, 255)
    shadow = (150, 138, 120, 255)
    if tracking:
        _tracked(image, text, (xy[0] - shift, xy[1] - shift), font, highlight, tracking)
        _tracked(image, text, (xy[0] + shift, xy[1] + shift), font, shadow, tracking)
        _tracked(image, text, xy, font, fill, tracking)
    else:
        _text(image, text, (xy[0] - shift, xy[1] - shift), font, highlight)
        _text(image, text, (xy[0] + shift, xy[1] + shift), font, shadow)
        _text(image, text, xy, font, fill)


def paint_battery(image: Image.Image, layout: DialLayout, percent) -> None:
    """A battery outline filled from the left, in the charge color."""
    draw = ImageDraw.Draw(image)
    cx, cy = layout.battery_center
    radius = layout.radius
    width = radius * 0.20
    height = radius * 0.072
    x0 = cx - width / 2
    y0 = cy - height / 2
    x1 = cx + width / 2
    y1 = cy + height / 2
    stroke = max(1, int(radius * 0.006))
    draw.rounded_rectangle((x0, y0, x1, y1), radius=height * 0.22, outline=INK, width=stroke)
    nub_h = height * 0.38
    nub_w = radius * 0.016
    draw.rectangle((x1, cy - nub_h / 2, x1 + nub_w, cy + nub_h / 2), fill=INK)
    if percent is None:
        return
    clamped = max(0.0, min(100.0, float(percent)))
    pad = stroke + 1
    inner = (width - 2 * pad) * clamped / 100.0
    if inner <= 0:
        return
    color = battery_color(clamped, 1, 12)
    draw.rectangle((x0 + pad, y0 + pad, x0 + pad + inner, y1 - pad), fill=color + (255,))


def paint_date_hand(image: Image.Image, layout: DialLayout, day: int) -> None:
    """A short mark in the date ring, pointing at today's number. It stays off the moon."""
    draw = ImageDraw.Draw(image)
    angle = clock_angle(day - 1, 31)
    inner = layout.moon_well_radius + layout.radius * 0.018
    outer = math.dist(layout.subdial_center, layout.date_hand_tip(day))
    start = DialLayout._polar(layout.subdial_center, inner, angle)
    end = DialLayout._polar(layout.subdial_center, outer, angle)
    width = max(2, int(layout.radius * 0.010))
    draw.line((start[0], start[1], end[0], end[1]), fill=INK, width=width)


def _taper(draw, cx, cy, angle, length, tail, width) -> None:
    ux = math.cos(angle)
    uy = math.sin(angle)
    px = -uy
    py = ux
    tip = (cx + ux * length, cy + uy * length)
    left = (cx - ux * tail + px * width, cy - uy * tail + py * width)
    right = (cx - ux * tail - px * width, cy - uy * tail - py * width)
    draw.polygon((tip, left, right), fill=INK)


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
    if kind == "roman":
        path = _TIMES_BOLD
    elif kind == "sans":
        path = _ARIAL_BOLD
    else:
        path = _TIMES
    font = ImageFont.truetype(path, pixels)
    _FONT_CACHE[key] = font
    return font
