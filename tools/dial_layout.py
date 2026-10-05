"""Geometry for the Lunara cream calendar dial.

Positions are fractions of the screen radius unless a DialLayout method
returns pixels. Screen Y grows downward. Angles follow a clock: 0 is
12 o'clock and values increase clockwise.

The moon phase uses the same epoch the watch will use: the 6 Jan 2000
18:14 UTC new moon, and the mean synodic month.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

BRAND = "LUNARA"
AUTOMATIC = "AUTOMATIC"
PERPETUAL = ("PERPETUAL", "CALENDAR")

# Mean synodic month, days. Shared with source/Dial.mc.
SYNODIC_DAYS = 29.530588853
NEW_MOON_EPOCH = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
# Seconds since the Unix epoch. The watch uses this same integer.
NEW_MOON_EPOCH_SECONDS = 947182440

# Fractions of the dial radius, matched to the cream calendar mockup.
# Romans sit in from the edge. The month, the paired windows, and the
# name stack under XII. The moon ring fills the lower half and clears VI.
_ROMAN_RADIUS = 0.80
_SUBDIAL_CENTER_Y = 0.335
_DATE_RING_RADIUS = 0.2325
_MOON_WELL_RADIUS = 0.195
_DATE_HAND_RADIUS = 0.285
_MONTH_Y = -0.52
_MONTH_HALF_W = 0.27
_MONTH_HALF_H = 0.044
_WINDOW_Y = -0.41
_WINDOW_HALF_W = 0.145
_WINDOW_HALF_H = 0.050
_WINDOW_CX = 0.0
_BRAND_Y = -0.30
_BATTERY_X = -0.42
_BATTERY_Y = -0.16
_BATTERY_TEXT_DY = 0.10


@dataclass(frozen=True)
class Mark:
    text: str
    x: float
    y: float
    day: int = 0


@dataclass(frozen=True)
class Window:
    center: tuple[float, float]
    half_w: float
    half_h: float

    @property
    def left(self) -> float:
        return self.center[0] - self.half_w

    @property
    def right(self) -> float:
        return self.center[0] + self.half_w


def moon_index(phase: float) -> int:
    """Sprite index 0–7. Index 0 is the new moon rendered at phase 0."""
    wrapped = phase % 1.0
    return int(math.floor(wrapped * 8.0 + 0.5)) % 8


def moon_phase_from_unix(seconds: float) -> float:
    """Phase from seconds since the Unix epoch. 0 is new, 0.5 is full."""
    days = (seconds - NEW_MOON_EPOCH_SECONDS) / 86400.0
    return (days % SYNODIC_DAYS) / SYNODIC_DAYS


def moon_phase_name(phase: float) -> str:
    """Everyday recognizable lunar phase name."""
    wrapped = phase % 1.0
    if wrapped < 0.03 or wrapped >= 0.97:
        return "New Moon"
    if wrapped < 0.22:
        return "Crescent"
    if wrapped < 0.28:
        return "Quarter"
    if wrapped < 0.47:
        return "Gibbous"
    if wrapped < 0.53:
        return "Full Moon"
    if wrapped < 0.72:
        return "Gibbous"
    if wrapped < 0.78:
        return "Quarter"
    return "Crescent"


def calendar_on(moment: datetime) -> tuple[int, int, int]:
    """Month 1–12, weekday 1–7 (Sunday is 1), day of month.

    Same numbering Dial.mc reads from Gregorian.info.
    """
    weekday = (moment.weekday() + 1) % 7 + 1
    return moment.month, weekday, moment.day


def moon_phase(year: int, month: int, day: int) -> float:
    """Phase at 12:00 UTC on the civil date. 0 is new, 0.5 is full."""
    moment = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return moon_phase_from_unix(moment.timestamp())


def clock_angle(steps: int, count: int) -> float:
    """Clockwise angle from 12 o'clock, in radians, in screen space."""
    return -math.pi / 2.0 + (steps * (2.0 * math.pi / count))


class DialLayout:
    def __init__(self, size: int) -> None:
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0 or size % 2 != 0:
            raise ValueError(f"dial size must be a positive even integer, got {size!r}")
        self.size = size
        self.radius = size / 2.0
        self.center = (self.radius, self.radius)

    def static_labels(self) -> dict[str, str]:
        return {
            "brand": BRAND,
            "automatic": AUTOMATIC,
            "perpetual": " ".join(PERPETUAL),
        }

    @property
    def subdial_center(self) -> tuple[float, float]:
        return self._at(0.0, _SUBDIAL_CENTER_Y)

    @property
    def date_ring_radius(self) -> float:
        return _DATE_RING_RADIUS * self.radius

    @property
    def moon_well_radius(self) -> float:
        return _MOON_WELL_RADIUS * self.radius

    @property
    def month_center(self) -> tuple[float, float]:
        return self._at(0.0, _MONTH_Y)

    @property
    def month_window(self) -> Window:
        return Window(center=self.month_center, half_w=_MONTH_HALF_W * self.radius, half_h=_MONTH_HALF_H * self.radius)

    @property
    def battery_center(self) -> tuple[float, float]:
        """Center of the battery icon."""
        return self._at(_BATTERY_X, _BATTERY_Y)

    @property
    def battery_text_center(self) -> tuple[float, float]:
        x, y = self.battery_center
        return (x, y + _BATTERY_TEXT_DY * self.radius)

    @property
    def lunar_info_center(self) -> tuple[float, float]:
        x, y = self._at(-_BATTERY_X, _BATTERY_Y)
        return (x, y + _BATTERY_TEXT_DY * self.radius)

    @property
    def weekday_window(self) -> Window:
        return self._window(-_WINDOW_CX)

    def date_hand_tip(self, day: int) -> tuple[float, float]:
        """Tip of the hand that indicates the day of the month, 1–31."""
        if not isinstance(day, int) or isinstance(day, bool) or day < 1 or day > 31:
            raise ValueError(f"day must be 1–31, got {day!r}")
        return self._polar(self.subdial_center, _DATE_HAND_RADIUS * self.radius, clock_angle(day - 1, 31))

    @property
    def brand_center(self) -> tuple[float, float]:
        return self._at(0.0, _BRAND_Y)

    @property
    def automatic_center(self) -> tuple[float, float]:
        """The old left legend. The battery icon sits here now."""
        return self.battery_center

    def romans(self) -> list[Mark]:
        names = ("XII", "III", "VI", "IX")
        hours = (0, 3, 6, 9)
        marks = []
        for name, hour in zip(names, hours):
            x, y = self._polar(self.center, _ROMAN_RADIUS * self.radius, clock_angle(hour, 12))
            marks.append(Mark(name, x, y))
        return marks

    def date_numerals(self) -> list[Mark]:
        sub = self.subdial_center
        ring = self.date_ring_radius
        marks = []
        for day in range(1, 32):
            x, y = self._polar(sub, ring, clock_angle(day - 1, 31))
            marks.append(Mark(str(day), x, y, day))
        return marks

    def _window(self, cx_frac: float) -> Window:
        return Window(
            center=self._at(cx_frac, _WINDOW_Y),
            half_w=_WINDOW_HALF_W * self.radius,
            half_h=_WINDOW_HALF_H * self.radius,
        )

    def _at(self, x_frac: float, y_frac: float) -> tuple[float, float]:
        cx, cy = self.center
        return (cx + x_frac * self.radius, cy + y_frac * self.radius)

    @staticmethod
    def _polar(origin: tuple[float, float], radius: float, angle: float) -> tuple[float, float]:
        return (
            origin[0] + radius * math.cos(angle),
            origin[1] + radius * math.sin(angle),
        )
