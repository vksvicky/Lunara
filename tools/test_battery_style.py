"""Battery percentage color: a charge gradient, and palettes that follow the day."""

import unittest
from pathlib import Path

from battery_style import battery_color, period_for_hour


def _channel(color, index):
    return color[index]


class BatteryColorTests(unittest.TestCase):
    def test_classic_gradient_runs_green_amber_red(self):
        full = battery_color(100, 1, 12)
        mid = battery_color(50, 1, 12)
        empty = battery_color(0, 1, 12)
        self.assertGreater(_channel(full, 1), _channel(full, 0))
        self.assertGreater(_channel(full, 1), _channel(full, 2))
        self.assertGreater(_channel(mid, 0), _channel(mid, 1))
        self.assertGreater(_channel(mid, 1), _channel(mid, 2))
        self.assertGreater(_channel(empty, 0), _channel(empty, 1) + 40)
        self.assertGreater(_channel(empty, 0), _channel(empty, 2))

    def test_halfway_sits_between_the_stops(self):
        full = battery_color(100, 1, 12)
        mid = battery_color(50, 1, 12)
        between = battery_color(75, 1, 12)
        self.assertGreater(_channel(between, 1), _channel(mid, 1))
        self.assertLess(_channel(between, 1), _channel(full, 1))

    def test_unknown_level_stays_ink(self):
        self.assertEqual(battery_color(None, 1, 12), (0x26, 0x22, 0x1E))

    def test_charge_is_clamped_before_the_blend(self):
        self.assertEqual(battery_color(-4, 1, 8), battery_color(0, 1, 8))
        self.assertEqual(battery_color(140, 1, 8), battery_color(100, 1, 8))

    def test_follow_the_day_changes_the_palette_with_the_hour(self):
        self.assertEqual(period_for_hour(7), 2)
        self.assertEqual(period_for_hour(14), 3)
        self.assertEqual(period_for_hour(19), 4)
        self.assertEqual(period_for_hour(23), 5)
        self.assertEqual(period_for_hour(3), 5)
        day = battery_color(100, 0, 14)
        night = battery_color(100, 0, 23)
        self.assertEqual(day, battery_color(100, 1, 14))
        self.assertNotEqual(night, day)

    def test_a_locked_style_ignores_the_hour(self):
        self.assertEqual(battery_color(40, 5, 14), battery_color(40, 5, 2))
        self.assertNotEqual(battery_color(40, 5, 14), battery_color(40, 1, 14))

    def test_unknown_style_uses_the_classic_gradient(self):
        self.assertEqual(battery_color(80, 99, 19), battery_color(80, 1, 19))

    def test_watch_source_uses_the_same_stops(self):
        source = (Path(__file__).resolve().parents[1] / "source" / "Battery.mc").read_text()
        for level, style, hour in ((100, 1, 12), (50, 1, 12), (0, 1, 12), (100, 5, 2)):
            red, green, blue = battery_color(level, style, hour)
            packed = (red << 16) | (green << 8) | blue
            self.assertIn(f"0x{packed:06X}", source)


if __name__ == "__main__":
    unittest.main()
