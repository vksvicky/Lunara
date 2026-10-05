"""Rasterize the Lunara dial and its moon-phase disc.

The bitmap is the ivory ground plus the supplied rings. Month, weekday,
the Lunara name, and the battery are drawn later, on the watch.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from battery_style import battery_color
from dial_layout import BRAND, DialLayout, clock_angle

IVORY = (246, 240, 228, 255)
INK = (28, 26, 22, 255)
# A 64-color sky blue. Near-black navy quantizes to black on these watches.
SKY = (0, 85, 170, 255)

_TIMES = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
_SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"


def render_dial(size: int) -> Image.Image:
    """Ivory dial bitmap. `size` is the even screen width in pixels.

    The ground is supersampled. The minute ring, Roman numerals, hour
    indices, and date ring are the per-size artwork, pasted at the same
    pixel size with no resample.
    """
    layout = DialLayout(size)
    big = _paint_ground(DialLayout(size * 3))
    image = big.resize((layout.size, layout.size), Image.Resampling.LANCZOS)
    date_ring = _load_exact(f"date_ring_{size}.png", image.size)
    _fill_date_hole(image, layout, date_ring)
    shift = _date_ring_shift(date_ring, layout)
    image.alpha_composite(date_ring, shift)
    image.alpha_composite(_load_exact(f"outer_dial_{size}.png", image.size))
    return image


def _darken_hour_bars(image: Image.Image, layout: DialLayout) -> None:
    """The supplied indices are light gray, so they vanish on the cream dial."""
    draw = ImageDraw.Draw(image)
    width = max(2, int(round(layout.radius * 0.016)))
    cx, cy = layout.center
    for hour in (1, 2, 4, 5, 7, 8, 10, 11):
        angle = -math.pi / 2.0 + hour * (math.tau / 12.0)
        inner = layout.radius * 0.60
        outer = layout.radius * 0.75
        draw.line(
            (
                cx + math.cos(angle) * inner,
                cy + math.sin(angle) * inner,
                cx + math.cos(angle) * outer,
                cy + math.sin(angle) * outer,
            ),
            fill=(0, 0, 0, 255),
            width=width,
        )


_ROOT = Path(__file__).resolve().parents[1]
_ARTWORK = _ROOT / "resources" / "artwork"
_BATTERY_FILE = _ROOT / "resources" / "battery.png"
_BATTERY_ART: Image.Image | None = None
_MOON_TEXTURE_FILE = _ARTWORK / "moon_texture.png"
_MOON_TEXTURE: Image.Image | None = None


def _get_moon_texture() -> Image.Image:
    global _MOON_TEXTURE
    if _MOON_TEXTURE is None:
        _MOON_TEXTURE = Image.open(_MOON_TEXTURE_FILE).convert("RGBA")
    return _MOON_TEXTURE


def _load_exact(name: str, size: tuple[int, int]) -> Image.Image:
    """Open a placed ring. A different canvas size is an error, not a resize."""
    art = Image.open(_ARTWORK / name).convert("RGBA")
    if art.size != size:
        raise ValueError(f"{name} is {art.size[0]}x{art.size[1]}; the dial is {size[0]}x{size[1]}")
    return art


def date_hole_diameter(size: int) -> int:
    """Pixel diameter of the clear center in the placed date ring."""
    art = _load_exact(f"date_ring_{size}.png", (size, size))
    hole = _date_hole_radius(art)
    return max(8, int(round(hole * 2)))


def _date_ring_center(date_ring: Image.Image) -> tuple[float, float]:
    box = date_ring.getbbox()
    if box is None:
        raise ValueError("date ring has no pixels")
    return ((box[0] + box[2] - 1) / 2.0, (box[1] + box[3] - 1) / 2.0)


def _date_ring_shift(date_ring: Image.Image, layout: DialLayout) -> tuple[int, int]:
    """Integer move that lands the artwork's ring on the sub-dial. No resample."""
    baked_x, baked_y = _date_ring_center(date_ring)
    target_x, target_y = layout.subdial_center
    return (int(round(target_x - baked_x)), int(round(target_y - baked_y)))


def _date_hole_radius(date_ring: Image.Image) -> float:
    pixels = date_ring.load()
    cx, cy = _date_ring_center(date_ring)
    x = int(round(cx))
    y = int(round(cy))
    limit = date_ring.width - 1
    while x < limit and pixels[x, y][3] < 16:
        x += 1
    return x - cx


def _fill_date_hole(image: Image.Image, layout: DialLayout, date_ring: Image.Image) -> None:
    """Navy behind the date ring's clear center, so the moon has a sky."""
    hole = _date_hole_radius(date_ring)
    if hole < 4:
        return
    cx, cy = layout.subdial_center
    ImageDraw.Draw(image).ellipse((cx - hole, cy - hole, cx + hole, cy + hole), fill=SKY)


def render_moon(size: int, phase: float) -> Image.Image:
    """Photorealistic Moon disc with authentic lunar craters, maria, and terminator."""
    if size < 2:
        raise ValueError(f"moon size must be at least 2, got {size!r}")
    return _render_photographic_moon(size, phase)


def paint_hands(image: Image.Image, layout: DialLayout) -> None:
    """Slender faceted hands at 10:10. Light falls from the upper left."""
    scale = 4
    big = Image.new("RGBA", (image.width * scale, image.height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    cx = layout.center[0] * scale
    cy = layout.center[1] * scale
    radius = layout.radius * scale
    minute = -math.pi / 2.0 + (10.0 / 60.0) * math.tau
    hour = -math.pi / 2.0 + (10.0 / 12.0) * math.tau + (10.0 / 60.0) * (math.pi / 6.0)

    _dauphine_hand(draw, cx, cy, hour, radius * 0.60, radius * 0.11, radius * 0.018)
    _dauphine_hand(draw, cx, cy, minute, radius * 0.80, radius * 0.13, radius * 0.012)

    # Multi-tiered polished steel center cap
    cap_r = max(4.0, radius * 0.032)
    draw.ellipse((cx - cap_r - 1, cy - cap_r - 1, cx + cap_r + 1, cy + cap_r + 1), fill=(35, 32, 28, 255))
    draw.ellipse((cx - cap_r, cy - cap_r, cx + cap_r, cy + cap_r), fill=(215, 215, 220, 255))
    inner_r = cap_r * 0.55
    draw.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=(255, 255, 255, 255))
    axle_r = cap_r * 0.28
    draw.ellipse((cx - axle_r, cy - axle_r, cx + axle_r, cy + axle_r), fill=(38, 34, 30, 255))

    image.alpha_composite(big.resize(image.size, Image.Resampling.LANCZOS))


def _dauphine_hand(draw: ImageDraw.ImageDraw, cx, cy, angle, length, tail, width) -> None:
    ux = math.cos(angle)
    uy = math.sin(angle)
    px = -uy
    py = ux
    s_dist = length * 0.28

    tip = (cx + ux * length, cy + uy * length)
    base_l = (cx - ux * tail + px * (width * 0.35), cy - uy * tail + py * (width * 0.35))
    base_r = (cx - ux * tail - px * (width * 0.35), cy - uy * tail - py * (width * 0.35))
    shd_l = (cx + ux * s_dist + px * width, cy + uy * s_dist + py * width)
    shd_r = (cx + ux * s_dist - px * width, cy + uy * s_dist - py * width)
    center = (cx, cy)

    draw.polygon((tip, shd_l, base_l, center), fill=(244, 246, 248, 255))
    draw.polygon((tip, center, base_r, shd_r), fill=(132, 128, 122, 255))
    edge = max(1, int(width * 0.14))
    draw.line((tip, shd_l, base_l), fill=(48, 44, 40, 255), width=edge)
    draw.line((tip, shd_r, base_r), fill=(48, 44, 40, 255), width=edge)
    draw.line(((cx - ux * tail, cy - uy * tail), tip), fill=(70, 66, 60, 255), width=edge)


def _paint_ground(layout: DialLayout) -> Image.Image:
    image = Image.new("RGBA", (layout.size, layout.size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, layout.size - 1, layout.size - 1), fill=IVORY)
    _subdial_rings(draw, layout)
    return image


def face_px(size: int) -> int:
    """The one size used for the month, the weekday, and the Lunara name."""
    return 16 if size >= 390 else 11


_DEVA = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"


def open_label_limit(layout: DialLayout) -> float:
    """Width under XII that stays clear of the minute track."""
    return layout.radius * 0.96


def label_font(layout: DialLayout, language_key: str = "eng") -> ImageFont.FreeTypeFont:
    """One size for the month, the weekday, and LUNARA. Latin is a dial serif."""
    pixels = face_px(layout.size)
    if language_key == "hin":
        return ImageFont.truetype(_DEVA, pixels, index=1)
    if language_key == "zht":
        return ImageFont.truetype(_SONG, pixels, index=7)
    if language_key in ("zhs", "jpn_kanji", "jpn_hira", "jpn_kata"):
        return ImageFont.truetype(_SONG, pixels, index=6)
    return ImageFont.truetype(_TIMES, pixels)


def brand_half_width(layout: DialLayout) -> float:
    """Half the width of LUNARA in the shared face font."""
    return label_font(layout).getlength(BRAND) / 2.0


def _subdial_rings(draw: ImageDraw.ImageDraw, layout: DialLayout) -> None:
    cx, cy = layout.subdial_center
    well = layout.moon_well_radius
    outer = layout.radius * 0.27

    draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), fill=(240, 234, 222, 255))
    draw.ellipse((cx - well, cy - well, cx + well, cy + well), fill=SKY)


_STAR = (255, 255, 170, 255)

_STARS = (
    (0.950, 0.500),
    (0.864, 0.765),
    (0.639, 0.928),
    (0.361, 0.928),
    (0.136, 0.765),
    (0.050, 0.500),
    (0.136, 0.235),
    (0.361, 0.072),
    (0.639, 0.072),
    (0.864, 0.235),
)


def _render_photographic_moon(size: int, phase: float) -> Image.Image:
    """Photorealistic Moon disc with authentic lunar craters, maria, and terminator."""
    phase = phase % 1.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    cx = cy = (size - 1) / 2.0
    radius = (size - 1) / 2.0
    radius2 = radius * radius

    # Deep blue night sky background
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= radius2:
                pixels[x, y] = SKY

    # Scale photographic moon to 88% of well
    m_diam = max(4, int(round(size * 0.88)))
    scaled = _get_moon_texture().resize((m_diam, m_diam), Image.Resampling.LANCZOS)
    s_pix = scaled.load()
    m_cx = (m_diam - 1) / 2.0
    m_cy = (m_diam - 1) / 2.0
    m_rad = (m_diam - 1) / 2.0
    ox = int(round(cx - m_cx))
    oy = int(round(cy - m_cy))

    sweep = math.cos(2.0 * math.pi * phase)

    for my in range(m_diam):
        for mx in range(m_diam):
            u = (mx - m_cx) / m_rad
            v = (my - m_cy) / m_rad
            if u * u + v * v > 1.0:
                continue
            src = s_pix[mx, my]
            if src[3] < 30:
                continue

            edge = math.sqrt(max(0.0, 1.0 - v * v))
            # Northern hemisphere: waxing (0 < phase <= 0.5) lights right, waning lights left
            term_u = sweep * edge if phase <= 0.5 else -sweep * edge
            dist = (u - term_u) if phase <= 0.5 else (term_u - u)
            penumbra = 2.0 / m_rad
            t = max(0.0, min(1.0, (dist / penumbra) + 0.5))
            t = t * t * (3.0 - 2.0 * t)

            px = ox + mx
            py = oy + my
            if 0 <= px < size and 0 <= py < size:
                if (px - cx) ** 2 + (py - cy) ** 2 <= radius2:
                    # Crisp bright sunlit lunar surface
                    lr = min(255, int(src[0] * 1.15 + 10))
                    lg = min(255, int(src[1] * 1.12 + 10))
                    lb = min(255, int(src[2] * 1.10 + 10))
                    # Lighter, luminous earthshine showing craters and maria on unlit side
                    er = int(src[0] * 0.38 + 25)
                    eg = int(src[1] * 0.40 + 28)
                    eb = int(src[2] * 0.48 + 38)
                    r = int(round(er + (lr - er) * t))
                    g = int(round(eg + (lg - eg) * t))
                    b = int(round(eb + (lb - eb) * t))
                    pixels[px, py] = (r, g, b, 255)

    # Subtle star field in sky rim
    for fx, fy in _STARS:
        sx = int(round(fx * (size - 1)))
        sy = int(round(fy * (size - 1)))
        if 0 <= sx < size and 0 <= sy < size:
            if (sx - cx) ** 2 + (sy - cy) ** 2 <= (radius * 0.94) ** 2:
                pixels[sx, sy] = _STAR

    return img




def fit_font(text: str, path: str, start_px: int, max_width: float, index: int = 0, max_px: int | None = None):
    """Smallest step down from `start_px` whose text stays inside `max_width`."""
    size = max(6, int(start_px))
    if max_px is not None:
        size = min(size, max(6, int(max_px)))
    while True:
        font = ImageFont.truetype(path, size, index=index) if index else ImageFont.truetype(path, size)
        if size <= 6 or font.getlength(text) <= max_width:
            return font
        size -= 1


def month_text_limit(layout: DialLayout) -> float:
    """Inner width of the month bar, leaving a margin inside the frame."""
    return layout.month_window.half_w * 2 * 0.82


def month_text_px_cap(layout: DialLayout) -> int:
    """Largest font that stays inside the bar's height."""
    return max(6, int(layout.month_window.half_h * 2 * 0.80))


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
    """The placed battery icon, with the charge color showing through its interior."""
    icon = scaled_battery_icon(max(16, int(round(layout.radius * 0.24))))
    cx, cy = layout.battery_center
    origin = (int(round(cx - icon.width / 2)), int(round(cy - icon.height / 2)))
    image.alpha_composite(_charge_under_icon(icon, percent), origin)
    image.alpha_composite(icon, origin)


def scaled_battery_icon(width: int) -> Image.Image:
    """The battery artwork at `width` pixels, with the outline kept solid black."""
    icon = _battery_artwork()
    height = max(1, int(round(width * icon.height / icon.width * 0.82)))
    scaled = icon.resize((width, height), Image.Resampling.LANCZOS)
    pixels = scaled.load()
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 48 and red < 96 and green < 96 and blue < 96:
                pixels[x, y] = (0, 0, 0, 255)
            else:
                pixels[x, y] = (0, 0, 0, 0)
    return _battery_shell(scaled)


def _battery_shell(icon: Image.Image) -> Image.Image:
    """Keep the outline and the terminal. Drop the lightning mark inside the body."""
    pixels = icon.load()
    width, height = icon.size
    outside = [[False] * width for _ in range(height)]
    stack = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if pixels[x, y][3] < 128 and (x == 0 or y == 0 or x == width - 1 or y == height - 1)
    ]
    while stack:
        x, y = stack.pop()
        if outside[y][x] or pixels[x, y][3] >= 128:
            continue
        outside[y][x] = True
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and not outside[ny][nx]:
                stack.append((nx, ny))
    for y in range(height):
        for x in range(width):
            if pixels[x, y][3] < 128:
                continue
            if any(
                not (0 <= nx < width and 0 <= ny < height) or outside[ny][nx]
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            ):
                continue
            pixels[x, y] = (0, 0, 0, 0)
    return icon


def _battery_artwork() -> Image.Image:
    global _BATTERY_ART
    if _BATTERY_ART is None:
        image = Image.open(_BATTERY_FILE).convert("RGBA")
        bounds = image.getbbox()
        if bounds is None:
            raise ValueError("resources/battery.png has no opaque pixels")
        _BATTERY_ART = image.crop(bounds)
    return _BATTERY_ART


def _charge_under_icon(icon: Image.Image, percent) -> Image.Image:
    """Color the icon's clear interior from the left. The black outline stays on top."""
    layer = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    if percent is None:
        return layer
    clamped = max(0.0, min(100.0, float(percent)))
    if clamped <= 0:
        return layer
    color = battery_color(clamped, 1, 12) + (255,)
    src = icon.load()
    out = layer.load()
    width, height = icon.size
    body = int(width * 0.90)
    inset_x = max(1, int(width * 0.06))
    inset_y = max(1, int(height * 0.20))
    fill_right = inset_x + int((body - 2 * inset_x) * clamped / 100.0)
    for y in range(inset_y, height - inset_y):
        for x in range(inset_x, fill_right):
            if src[x, y][3] < 40 and _inside_outline(src, x, y, width, height):
                out[x, y] = color
    return layer


def _inside_outline(src, x: int, y: int, width: int, height: int) -> bool:
    left = any(src[i, y][3] > 128 for i in range(x - 1, -1, -1))
    right = any(src[i, y][3] > 128 for i in range(x + 1, width))
    up = any(src[x, j][3] > 128 for j in range(y - 1, -1, -1))
    down = any(src[x, j][3] > 128 for j in range(y + 1, height))
    return left and right and up and down


def paint_date_highlight(image: Image.Image, layout: DialLayout, day: int) -> None:
    """Terracotta accent ring centered over the day numeral on the date ring."""
    draw = ImageDraw.Draw(image)
    tip = layout.date_hand_tip(day)
    r = layout.radius * 0.024
    pen_w = max(1, int(round(layout.radius * 0.007)))
    ACCENT = (225, 75, 45, 255)  # 0xE14B2D terracotta orange
    draw.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), outline=ACCENT, width=pen_w)


def paint_date_hand(image: Image.Image, layout: DialLayout, day: int) -> None:
    paint_date_highlight(image, layout, day)


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


