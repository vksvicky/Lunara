"""The dial bitmap is ivory, circular, and keeps a dark moon well."""

import unittest

from dial_layout import DialLayout
from dial_render import render_dial, render_moon


def _is_bright(pixel) -> bool:
    red, green, blue, alpha = pixel
    return alpha > 200 and red > 170 and green > 160 and blue > 130


def _bright_count(image) -> int:
    return sum(1 for pixel in image.get_flattened_data() if _is_bright(pixel))


def _bright_centroid(image):
    total_x = 0.0
    total_y = 0.0
    count = 0
    for y in range(image.height):
        for x in range(image.width):
            if _is_bright(image.getpixel((x, y))):
                total_x += x
                total_y += y
                count += 1
    if count == 0:
        return (0.0, 0.0), 0
    return (total_x / count, total_y / count), count


def _star_pixels(image) -> int:
    count = 0
    for pixel in image.get_flattened_data():
        red, green, blue, alpha = pixel
        if alpha > 200 and red > 190 and green > 190 and blue > 190:
            count += 1
    return count


class DialRenderTests(unittest.TestCase):
    def test_dial_matches_the_requested_size(self):
        image = render_dial(240)
        self.assertEqual(image.size, (240, 240))
        self.assertEqual(image.mode, "RGBA")

    def test_center_is_warm_ivory_and_the_corner_is_clear(self):
        image = render_dial(240)
        red, green, blue, alpha = image.getpixel((120, 120))
        self.assertEqual(alpha, 255)
        self.assertGreater(red, 220)
        self.assertGreater(green, 210)
        self.assertGreater(red, blue + 10)
        self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_moon_well_is_dark_blue(self):
        layout = DialLayout(240)
        image = render_dial(240)
        x = int(round(layout.subdial_center[0]))
        y = int(round(layout.subdial_center[1]))
        red, green, blue, alpha = image.getpixel((x, y))
        self.assertEqual(alpha, 255)
        self.assertGreater(blue, red)
        self.assertLess(green, 90)

    def test_twelve_oclock_roman_is_inked(self):
        layout = DialLayout(240)
        image = render_dial(240)
        twelve = next(mark for mark in layout.romans() if mark.text == "XII")
        self.assertTrue(_has_ink(image, twelve.x, twelve.y))

    def test_side_legends_are_left_blank_for_live_text(self):
        layout = DialLayout(240)
        image = render_dial(240)
        for point in (layout.automatic_center, layout.perpetual_center):
            x = int(round(point[0]))
            y = int(round(point[1]))
            ink = 0
            for dy in range(-8, 9):
                for dx in range(-18, 19):
                    red, _green, _blue, alpha = image.getpixel((x + dx, y + dy))
                    if alpha > 200 and red < 90:
                        ink += 1
            self.assertEqual(ink, 0, point)

    def test_odd_size_is_rejected(self):
        with self.assertRaises(ValueError):
            render_dial(241)


class MoonRenderTests(unittest.TestCase):
    def test_full_moon_is_centered_and_brighter_than_new(self):
        full = render_moon(96, 0.5)
        new = render_moon(96, 0.0)
        full_at, full_count = _bright_centroid(full)
        _new_at, new_count = _bright_centroid(new)
        self.assertGreater(full_count, max(1, new_count) * 3)
        self.assertAlmostEqual(full_at[0], (full.width - 1) / 2.0, delta=full.width * 0.08)

    def test_moon_travels_from_left_to_right_across_the_month(self):
        waxing_at, waxing_count = _bright_centroid(render_moon(96, 0.25))
        waning_at, waning_count = _bright_centroid(render_moon(96, 0.75))
        middle = (96 - 1) / 2.0
        self.assertGreater(waxing_count, 20)
        self.assertGreater(waning_count, 20)
        self.assertLess(waxing_at[0], middle - 96 * 0.08)
        self.assertGreater(waning_at[0], middle + 96 * 0.08)

    def test_new_moon_is_a_starry_sky_with_the_moon_off_center(self):
        image = render_moon(96, 0.0)
        red, green, blue, alpha = image.getpixel((48, 48))
        self.assertEqual(alpha, 255)
        self.assertGreater(blue, red)
        self.assertGreater(blue, green)
        stars = _star_pixels(image)
        self.assertGreater(stars, 4)
        self.assertLess(stars, 90)

    def test_quarter_sits_between_new_and_full(self):
        new_moon = _bright_count(render_moon(64, 0.0))
        quarter = _bright_count(render_moon(64, 0.25))
        full_moon = _bright_count(render_moon(64, 0.5))
        self.assertGreater(quarter, new_moon)
        self.assertLess(quarter, full_moon)

    def test_phase_wraps(self):
        wrapped = list(render_moon(32, 1.25).get_flattened_data())
        quarter = list(render_moon(32, 0.25).get_flattened_data())
        self.assertEqual(wrapped, quarter)


def _has_ink(image, x, y) -> bool:
    x0 = max(0, int(x) - 8)
    y0 = max(0, int(y) - 8)
    x1 = min(image.width, int(x) + 9)
    y1 = min(image.height, int(y) + 9)
    for py in range(y0, y1):
        for px in range(x0, x1):
            red, green, blue, alpha = image.getpixel((px, py))
            if alpha > 200 and red < 80 and green < 80 and blue < 80:
                return True
    return False


if __name__ == "__main__":
    unittest.main()
