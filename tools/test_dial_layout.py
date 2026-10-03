"""Behavior tests for the Lunara dial layout.

The dial is the cream calendar face: Roman hours, month and date windows,
the LUNARA name, and the moon-phase sub-dial with days 1–31.
Positions are in screen space (positive Y is down).
"""

import math
import re
import unittest
from datetime import datetime
from pathlib import Path

from dial_layout import (
    AUTOMATIC,
    BRAND,
    NEW_MOON_EPOCH,
    NEW_MOON_EPOCH_SECONDS,
    PERPETUAL,
    SYNODIC_DAYS,
    DialLayout,
    calendar_on,
    moon_index,
    moon_phase,
)


class DialLayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = DialLayout(454)

    def test_brand_is_lunara_and_not_an_existing_mark(self):
        labels = self.layout.static_labels()
        self.assertEqual(labels["brand"], "LUNARA")
        self.assertEqual(BRAND, "LUNARA")
        joined = " ".join(labels.values())
        for forbidden in ("GARMIN", "PERPEX", "PATEK"):
            self.assertNotIn(forbidden, joined)

    def test_side_legends_match_the_calendar_dial(self):
        self.assertEqual(AUTOMATIC, "AUTOMATIC")
        self.assertEqual(PERPETUAL, ("PERPETUAL", "CALENDAR"))

    def test_cardinal_romans_sit_on_their_clock_positions(self):
        romans = {mark.text: mark for mark in self.layout.romans()}
        self.assertEqual(set(romans), {"XII", "III", "VI", "IX"})

        center = self.layout.center
        self.assertLess(romans["XII"].y, center[1])
        self.assertGreater(romans["VI"].y, center[1])
        self.assertGreater(romans["III"].x, center[0])
        self.assertLess(romans["IX"].x, center[0])

        self.assertAlmostEqual(romans["XII"].x, center[0], delta=1)
        self.assertAlmostEqual(romans["VI"].x, center[0], delta=1)
        self.assertAlmostEqual(romans["III"].y, center[1], delta=1)
        self.assertAlmostEqual(romans["IX"].y, center[1], delta=1)

    def test_day_one_starts_at_the_top_of_the_subdial_and_runs_clockwise(self):
        days = self.layout.date_numerals()
        self.assertEqual([mark.day for mark in days], list(range(1, 32)))

        sub = self.layout.subdial_center
        day_one = days[0]
        self.assertLess(day_one.y, sub[1])
        self.assertAlmostEqual(day_one.x, sub[0], delta=1.5)

        # Day 9 is about a quarter turn clockwise, so it sits to the right.
        self.assertGreater(days[8].x, sub[0])
        self.assertAlmostEqual(days[8].y, sub[1], delta=self.layout.radius * 0.08)

    def test_subdial_date_ring_and_moon_well_stay_on_the_face(self):
        radius = self.layout.radius
        center = self.layout.center
        sub = self.layout.subdial_center

        self.assertGreater(sub[1], center[1])
        self.assertAlmostEqual(sub[0], center[0], delta=1)

        well = self.layout.moon_well_radius
        ring = self.layout.date_ring_radius
        self.assertLess(well, ring)

        outer = math.dist(center, sub) + ring
        self.assertLess(outer, radius * 0.98)

        for mark in self.layout.date_numerals():
            self.assertLess(math.dist(center, (mark.x, mark.y)), radius * 0.96)

    def test_six_oclock_roman_clears_the_date_ring(self):
        six = next(mark for mark in self.layout.romans() if mark.text == "VI")
        sub = self.layout.subdial_center
        gap = math.dist((six.x, six.y), sub) - self.layout.date_ring_radius
        self.assertGreater(gap, self.layout.radius * 0.06)

    def test_calendar_windows_stack_above_the_name_and_the_moon(self):
        month = self.layout.month_window
        weekday = self.layout.weekday_window
        brand = self.layout.brand_center
        sub = self.layout.subdial_center
        center = self.layout.center

        self.assertLess(month.center[1], weekday.center[1])
        self.assertAlmostEqual(month.center[0], center[0], delta=1)
        self.assertAlmostEqual(weekday.center[0], center[0], delta=1)
        self.assertGreater(month.half_w, weekday.half_w)
        self.assertLess(weekday.center[1], brand[1])
        self.assertLess(brand[1], sub[1])

    def test_date_hand_points_at_the_day_on_the_ring(self):
        sub = self.layout.subdial_center
        first = self.layout.date_hand_tip(1)
        self.assertLess(first[1], sub[1])
        self.assertAlmostEqual(first[0], sub[0], delta=1.5)

        ninth = self.layout.date_hand_tip(9)
        self.assertGreater(ninth[0], sub[0])

        with self.assertRaises(ValueError):
            self.layout.date_hand_tip(0)
        with self.assertRaises(ValueError):
            self.layout.date_hand_tip(32)

    def test_battery_icon_sits_left_of_center_and_the_percent_is_below_it(self):
        battery = self.layout.battery_center
        label = self.layout.battery_text_center
        center = self.layout.center
        sub = self.layout.subdial_center
        self.assertLess(battery[0], center[0])
        self.assertAlmostEqual(label[0], battery[0], delta=1)
        self.assertGreater(label[1], battery[1])
        self.assertGreater(battery[1], self.layout.weekday_window.center[1])
        self.assertLess(label[1], sub[1])
        clearance = self.layout.date_ring_radius + self.layout.radius * 0.04
        self.assertGreater(math.dist(battery, sub), clearance)

    def test_positions_scale_with_screen_size(self):
        small = DialLayout(240)
        large = DialLayout(454)
        self.assertAlmostEqual(
            large.subdial_center[1] / large.radius,
            small.subdial_center[1] / small.radius,
            places=4,
        )
        self.assertAlmostEqual(
            large.date_ring_radius / large.radius,
            small.date_ring_radius / small.radius,
            places=4,
        )

    def test_odd_or_non_positive_size_is_rejected(self):
        with self.assertRaises(ValueError):
            DialLayout(0)
        with self.assertRaises(ValueError):
            DialLayout(-260)
        with self.assertRaises(ValueError):
            DialLayout(261)


class MoonPhaseTests(unittest.TestCase):
    def test_epoch_constant_is_the_january_2000_new_moon(self):
        self.assertEqual(int(NEW_MOON_EPOCH.timestamp()), NEW_MOON_EPOCH_SECONDS)
        self.assertEqual(NEW_MOON_EPOCH_SECONDS, 947182440)

    def test_watch_source_uses_the_same_fractions(self):
        layout = DialLayout(1000)
        radius = layout.radius
        _, cy = layout.center
        expected = {
            "MONTH_Y": (layout.month_center[1] - cy) / radius,
            "MONTH_HALF_W": layout.month_window.half_w / radius,
            "MONTH_HALF_H": layout.month_window.half_h / radius,
            "WINDOW_Y": (layout.weekday_window.center[1] - cy) / radius,
            "WINDOW_CX": (layout.center[0] - layout.weekday_window.center[0]) / radius,
            "SUBDIAL_Y": (layout.subdial_center[1] - cy) / radius,
            "MOON_WELL_R": layout.moon_well_radius / radius,
            "DATE_HAND_R": math.dist(layout.subdial_center, layout.date_hand_tip(1)) / radius,
            "BATTERY_X": (layout.battery_center[0] - layout.center[0]) / radius,
            "BATTERY_Y": (layout.battery_center[1] - cy) / radius,
            "BATTERY_TEXT_DY": (layout.battery_text_center[1] - layout.battery_center[1]) / radius,
            "BRAND_Y": (layout.brand_center[1] - cy) / radius,
            "SYNODIC_DAYS": SYNODIC_DAYS,
            "NEW_MOON_EPOCH": float(NEW_MOON_EPOCH_SECONDS),
        }
        source = (Path(__file__).resolve().parents[1] / "source" / "Dial.mc").read_text()
        for name, value in expected.items():
            match = re.search(rf"const {name} = (-?[0-9.]+);", source)
            self.assertIsNotNone(match, name)
            self.assertAlmostEqual(float(match.group(1)), value, places=5)

    def test_known_new_moon_is_a_new_moon(self):
        # 6 Jan 2000 18:14 UTC was a new moon. A date-only phase is noon that day,
        # a few hours earlier, so the value sits just before 0.
        phase = moon_phase(2000, 1, 6)
        self.assertLess(min(phase, 1.0 - phase), 0.04)

    def test_two_weeks_later_is_near_full(self):
        phase = moon_phase(2000, 1, 21)
        self.assertGreater(phase, 0.45)
        self.assertLess(phase, 0.58)

    def test_phase_stays_inside_zero_to_one(self):
        for year, month, day in ((2024, 2, 29), (1999, 12, 31), (2026, 10, 1)):
            phase = moon_phase(year, month, day)
            self.assertGreaterEqual(phase, 0.0)
            self.assertLess(phase, 1.0)

    def test_sprite_index_picks_new_full_and_wraps(self):
        self.assertEqual(moon_index(0.0), 0)
        self.assertEqual(moon_index(0.5), 4)
        self.assertEqual(moon_index(0.999), 0)
        self.assertEqual(moon_index(1.0625), 1)

    def test_calendar_month_follows_the_civil_date(self):
        # Friday 2 October 2026. Weekday numbers match Gregorian.info: Sunday is 1.
        self.assertEqual(calendar_on(datetime(2026, 10, 2)), (10, 6, 2))
        self.assertEqual(calendar_on(datetime(2000, 12, 31)), (12, 1, 31))
        self.assertNotEqual(calendar_on(datetime(2026, 10, 2))[0], 12)

    def test_phase_advances_one_week_without_wrapping(self):
        start = moon_phase(2000, 1, 7)
        later = moon_phase(2000, 1, 14)
        self.assertAlmostEqual(later - start, 7.0 / 29.530588853, delta=0.02)


if __name__ == "__main__":
    unittest.main()
