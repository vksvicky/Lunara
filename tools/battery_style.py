"""Charge color for the battery percentage.

Style 0 follows the hour. Style 1 is always green, amber, red.
Styles 2–5 lock morning, day, evening, or night.
"""

from __future__ import annotations

import math

INK = (0x26, 0x22, 0x1E)

# Full, middle, empty. Day uses the classic green / amber / red stops.
CLASSIC = ((0x2E, 0x9A, 0x4A), (0xE0, 0x8C, 0x18), (0xC6, 0x28, 0x28))
MORNING = ((0x3E, 0x8C, 0x5A), (0xD4, 0xA0, 0x17), (0xE0, 0x7A, 0x4C))
EVENING = ((0xC4, 0xA3, 0x5A), (0xE0, 0x7A, 0x2F), (0xA3, 0x20, 0x30))
NIGHT = ((0x3D, 0x6B, 0x62), (0xA6, 0x84, 0x3C), (0x8C, 0x3A, 0x3A))

_PALETTES = {
    2: MORNING,
    4: EVENING,
    5: NIGHT,
}


def period_for_hour(hour: int) -> int:
    """2 morning, 3 day, 4 evening, 5 night."""
    hour = int(hour) % 24
    if 5 <= hour <= 10:
        return 2
    if 11 <= hour <= 16:
        return 3
    if 17 <= hour <= 20:
        return 4
    return 5


def _resolve(style: int | None, hour: int) -> int:
    if style is None or style == 0:
        return period_for_hour(0 if hour is None else hour)
    if style in (1, 2, 3, 4, 5):
        return style
    return 1


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    mixed = []
    for origin, destination in zip(start, end):
        mixed.append(int(math.floor(origin + (destination - origin) * amount + 0.5)))
    return (mixed[0], mixed[1], mixed[2])


def battery_color(level: float | None, style: int | None, hour: int) -> tuple[int, int, int]:
    """RGB for a charge reading. None stays the dial ink."""
    if level is None:
        return INK
    percent = int(math.floor(float(level) + 0.5))
    percent = max(0, min(100, percent))
    full, middle, empty = _PALETTES.get(_resolve(style, hour), CLASSIC)
    if percent >= 50:
        return _mix(middle, full, (percent - 50) / 50.0)
    return _mix(empty, middle, percent / 50.0)
