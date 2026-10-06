"""Photorealistic Moon disc rendering for Lunara dials and sprite generation.

Renders authentic lunar craters, maria, terminator line, and earthshine.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

# A 64-color sky blue. Near-black navy quantizes to black on these watches.
SKY = (0, 85, 170, 255)
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

_ROOT = Path(__file__).resolve().parents[1]
_ARTWORK = _ROOT / "resources" / "artwork"
_MOON_TEXTURE_FILE = _ARTWORK / "moon_texture.png"
_MOON_TEXTURE: Image.Image | None = None


def _get_moon_texture() -> Image.Image:
    global _MOON_TEXTURE
    if _MOON_TEXTURE is None:
        if not _MOON_TEXTURE_FILE.exists():
            raise FileNotFoundError(f"Required lunar texture not found at {_MOON_TEXTURE_FILE}")
        _MOON_TEXTURE = Image.open(_MOON_TEXTURE_FILE).convert("RGBA")
    return _MOON_TEXTURE


def render_moon(size: int, phase: float) -> Image.Image:
    """Photorealistic Moon disc with authentic lunar craters, maria, and terminator."""
    if size < 2:
        raise ValueError(f"moon size must be at least 2, got {size!r}")
    return _render_photographic_moon(size, phase)


def _render_photographic_moon(size: int, phase: float) -> Image.Image:
    """Photorealistic Moon disc with authentic lunar craters, maria, and terminator."""
    wrapped_phase = float(phase) % 1.0
    if wrapped_phase < 0.0:
        wrapped_phase += 1.0

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

    sweep = math.cos(2.0 * math.pi * wrapped_phase)

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
            term_u = sweep * edge if wrapped_phase <= 0.5 else -sweep * edge
            dist = (u - term_u) if wrapped_phase <= 0.5 else (term_u - u)
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
