"""The dial bitmap is ivory, circular, and keeps a dark moon well."""

import math
import unittest
from pathlib import Path

from PIL import Image

from dial_layout import DialLayout, clock_angle
from dial_render import (
    _date_ring_shift,
    paint_battery,
    paint_date_hand,
    paint_timeline_milestones,
    render_dial,
    render_moon,
    scaled_battery_icon,
)


def _is_bright(pixel) -> bool:
    """Lit moon surface. Dark sky, stars, and earthshine do not count."""
    red, green, blue, alpha = pixel
    if alpha <= 200:
        return False
    return red > 110 and green > 110 and (red + green) > 240 and abs(red - blue) < 30


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
        if alpha > 200 and red > 230 and green > 200 and 120 < blue < 190:
            count += 1
    return count


class DialRenderTests(unittest.TestCase):
    def test_dial_matches_the_requested_size(self):
        image = render_dial(240)
        self.assertEqual(image.size, (240, 240))
        self.assertEqual(image.mode, "RGBA")

    def test_open_field_is_warm_ivory_and_the_corner_is_clear(self):
        image = render_dial(240)
        layout = DialLayout(240)
        x = int(layout.center[0] + layout.radius * 0.50)
        y = int(layout.center[1] - layout.radius * 0.15)
        red, green, blue, alpha = image.getpixel((x, y))
        self.assertEqual(alpha, 255)
        self.assertGreater(red, 220)
        self.assertGreater(green, 210)
        self.assertGreater(red, blue + 10)
        self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_placed_rings_are_copied_without_resampling(self):
        """Romans, hour bars, and the date ring keep the supplied artwork."""
        size = 240
        image = render_dial(size)
        artwork = Path(__file__).resolve().parents[1] / "resources" / "artwork"
        outer = Image.open(artwork / f"outer_dial_{size}.png").convert("RGBA")
        date_ring = Image.open(artwork / f"date_ring_{size}.png").convert("RGBA")
        self.assertEqual(outer.size, image.size)
        self.assertEqual(date_ring.size, image.size)
        dx, dy = _date_ring_shift(date_ring, DialLayout(size))
        copied = 0
        for y in range(size):
            for x in range(size):
                top = outer.getpixel((x, y))
                if top[3] == 255:
                    if not _on_hour_index(x, y, size):
                        self.assertEqual(image.getpixel((x, y)), top, f"outer_dial at {x},{y}")
                    copied += 1
                    continue
                sx = x - dx
                sy = y - dy
                if not (0 <= sx < size and 0 <= sy < size):
                    continue
                band = date_ring.getpixel((sx, sy))
                if top[3] == 0 and band[3] == 255:
                    self.assertEqual(image.getpixel((x, y)), band, f"date_ring at {x},{y}")
                    copied += 1
        self.assertGreater(copied, 1000)

    def test_hour_bars_are_dark_enough_to_read(self):
        size = 260
        layout = DialLayout(size)
        image = render_dial(size)
        angle = -math.pi / 2.0 + 2.0 * (math.tau / 12.0)
        x = int(round(layout.center[0] + math.cos(angle) * layout.radius * 0.67))
        y = int(round(layout.center[1] + math.sin(angle) * layout.radius * 0.67))
        dark = 0
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                red, green, blue, alpha = image.getpixel((x + dx, y + dy))
                if alpha > 200 and red < 40 and green < 40 and blue < 40:
                    dark += 1
        self.assertGreater(dark, 0)

    def test_month_and_weekday_sit_on_the_open_dial(self):
        image = render_dial(240)
        layout = DialLayout(240)
        field = image.getpixel((int(layout.center[0] + layout.radius * 0.50), int(layout.center[1] - layout.radius * 0.15)))
        weekday = layout.weekday_window
        points = (
            layout.month_center,
            weekday.center,
            (weekday.left, weekday.center[1] - weekday.half_h),
        )
        for point in points:
            pixel = image.getpixel((int(point[0]), int(point[1])))
            self.assertLess(abs(sum(pixel[:3]) - sum(field[:3])), 20, point)

    def test_moon_well_is_sky_blue(self):
        layout = DialLayout(240)
        image = render_dial(240)
        x = int(round(layout.subdial_center[0]))
        y = int(round(layout.subdial_center[1]))
        red, green, blue, alpha = image.getpixel((x, y))
        self.assertEqual(alpha, 255)
        self.assertLess(red, 20)
        self.assertGreater(blue, 140)
        self.assertGreater(blue, green)

    def test_battery_icon_is_the_placed_artwork_and_fills_from_the_left(self):
        layout = DialLayout(240)
        image = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        paint_battery(image, layout, 80)
        cx, cy = (int(round(layout.battery_center[0])), int(round(layout.battery_center[1])))
        dark = 0
        charge = 0
        for dy in range(-14, 15):
            for dx in range(-22, 23):
                red, green, blue, alpha = image.getpixel((cx + dx, cy + dy))
                if alpha < 100:
                    continue
                if red < 40 and green < 40 and blue < 40:
                    dark += 1
                elif green > red + 20 and green > 70:
                    charge += 1
        self.assertGreater(dark, 8)
        self.assertGreater(charge, 8)

        empty = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        paint_battery(empty, layout, None)
        leaked = 0
        for dy in range(-14, 15):
            for dx in range(-22, 23):
                red, green, blue, alpha = empty.getpixel((cx + dx, cy + dy))
                if alpha > 200 and green > red + 20 and green > 70:
                    leaked += 1
        self.assertEqual(leaked, 0)

    def test_side_legends_are_left_blank_for_live_text(self):
        layout = DialLayout(240)
        image = render_dial(240)
        for point in (layout.automatic_center, layout.battery_text_center):
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

    def test_battery_shell_has_no_lightning_mark(self):
        icon = scaled_battery_icon(96)
        pixels = icon.load()
        mid = icon.height // 2
        interior = range(int(icon.width * 0.30), int(icon.width * 0.62))
        dark = [
            x
            for x in interior
            if pixels[x, mid][3] > 128 and pixels[x, mid][0] < 40
        ]
        self.assertEqual(dark, [])

    def test_date_marker_highlights_day_on_the_ring(self):
        layout = DialLayout(260)
        image = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        paint_date_hand(image, layout, 1)
        tip = layout.date_hand_tip(1)
        r = int(round(layout.radius * 0.024))
        # Check that accent color pixels exist on the ring around day 1
        x, y = int(round(tip[0])), int(round(tip[1] - r))
        pixel = image.getpixel((x, y))
        self.assertGreater(pixel[3], 200)
        # Terracotta orange (225, 75, 45)
        self.assertGreater(pixel[0], 200)
        self.assertLess(pixel[2], 80)
        # Moon center is pure transparent (no shaft across the moon)
        sx, sy = int(round(layout.subdial_center[0])), int(round(layout.subdial_center[1]))
        self.assertEqual(image.getpixel((sx, sy))[3], 0)

    def test_dial_bitmaps_are_not_dithered(self):
        xml = (
            Path(__file__).resolve().parents[1]
            / "resources-round-260x260"
            / "drawables"
            / "drawables.xml"
        ).read_text()
        for name in ("dial_bg.png", "battery_icon.png", "moon_0.png"):
            self.assertIn(f'filename="{name}" dithering="none"', xml)


class MoonRenderTests(unittest.TestCase):
    def test_full_moon_is_centered_and_brighter_than_new(self):
        full = render_moon(96, 0.5)
        new = render_moon(96, 0.0)
        full_at, full_count = _bright_centroid(full)
        _new_at, new_count = _bright_centroid(new)
        self.assertGreater(full_count, 1000)
        self.assertLess(new_count, 20)
        middle = (full.width - 1) / 2.0
        self.assertAlmostEqual(full_at[0], middle, delta=full.width * 0.08)
        self.assertAlmostEqual(full_at[1], middle, delta=full.height * 0.08)

    def test_moon_travels_from_left_to_right_across_the_month(self):
        """Waxing illuminates right limb, waning illuminates left limb."""
        waxing_at, waxing_count = _bright_centroid(render_moon(96, 0.25))
        waning_at, waning_count = _bright_centroid(render_moon(96, 0.75))
        middle = (96 - 1) / 2.0
        self.assertGreater(waxing_count, 20)
        self.assertGreater(waning_count, 20)
        self.assertGreater(waxing_at[0], middle + 96 * 0.08)
        self.assertLess(waning_at[0], middle - 96 * 0.08)

    def test_new_moon_is_a_starry_sky(self):
        image = render_moon(96, 0.0)
        for point in ((48, 4), (48, 91)):
            red, green, blue, alpha = image.getpixel(point)
            self.assertEqual(alpha, 255, point)
            self.assertGreater(blue, 140, point)
            self.assertGreater(blue, red, point)
        c_red, c_green, c_blue, c_alpha = image.getpixel((48, 48))
        self.assertEqual(c_alpha, 255)
        # Luminous earthshine is visible (not pitch black) and clearly darker than sunlit face
        self.assertGreater(c_red, 40)
        self.assertLess(c_red, 110)
        stars = _star_pixels(image)
        self.assertGreater(stars, 4)
        self.assertLess(stars, 90)

    def test_unlit_part_hides_behind_the_window(self):
        """Waxing shows the lit face on the right; unlit side shows earthshine."""
        image = render_moon(96, 0.25)
        red, green, blue, alpha = image.getpixel((20, 48))
        self.assertEqual(alpha, 255)
        self.assertLess(red, 110)

    def test_full_moon_is_white_with_gray_maria(self):
        image = render_moon(96, 0.5)
        red, green, blue, alpha = image.getpixel((48, 48))
        self.assertEqual(alpha, 255)
        self.assertGreater(red, 100)
        highlands = 0
        maria = 0
        for y in range(20, 76):
            for x in range(20, 76):
                r, g, b, a = image.getpixel((x, y))
                if a == 255 and abs(r - g) < 15 and abs(g - b) < 15:
                    if r > 200:
                        highlands += 1
                    elif 65 < r < 160:
                        maria += 1
        self.assertGreater(highlands, 100)
        self.assertGreater(maria, 500)

    def test_timeline_milestones_painted(self):
        layout = DialLayout(260)
        image = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        paint_timeline_milestones(image, layout, 2026, 10)
        non_transparent = sum(1 for p in image.get_flattened_data() if p[3] > 0)
        self.assertGreater(non_transparent, 40)

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


def _on_hour_index(x: int, y: int, size: int) -> bool:
    center = (size - 1) / 2.0
    radius = size / 2.0
    dist = math.hypot(x - center, y - center) / radius
    if not (0.55 < dist < 0.78):
        return False
    bearing = math.atan2(y - center, x - center)
    for hour in (1, 2, 4, 5, 7, 8, 10, 11):
        angle = -math.pi / 2.0 + hour * (math.tau / 12.0)
        delta = (bearing - angle + math.pi) % (2 * math.pi) - math.pi
        if abs(delta) < math.radians(6):
            return True
    return False


def _roman_tones(image, layout, x: float, y: float) -> dict[str, int]:
    """Count gunmetal body and the bright chamfer around one numeral."""
    tones = {"metal": 0, "highlight": 0}
    half = 22
    x0 = max(0, int(x) - half)
    y0 = max(0, int(y) - half)
    x1 = min(image.width, int(x) + half + 1)
    y1 = min(image.height, int(y) + half + 1)
    sx, sy = layout.subdial_center
    ring = layout.date_ring_radius + layout.radius * 0.06
    for py in range(y0, y1):
        for px in range(x0, x1):
            if math.hypot(px - sx, py - sy) < ring:
                continue
            if math.hypot(px - layout.center[0], py - layout.center[1]) > layout.radius * 0.86:
                continue
            red, green, blue, alpha = image.getpixel((px, py))
            if alpha < 200:
                continue
            if red > 220 and green > 210 and red > blue + 8:
                continue
            if red > 190 and green > 190 and blue > 185 and abs(red - blue) < 28:
                tones["highlight"] += 1
            elif 28 < red < 120 and abs(red - green) < 24 and abs(green - blue) < 24:
                tones["metal"] += 1
    return tones


def _inset_figure(layout, mark) -> tuple[float, float]:
    """Where the figure is printed: just inside the date ring."""
    sx, sy = layout.subdial_center
    return (sx + (mark.x - sx) * 0.94, sy + (mark.y - sy) * 0.94)


def _dark_figure(image, x: float, y: float) -> int:
    count = 0
    half = 3
    for py in range(max(0, int(y) - half), min(image.height, int(y) + half + 1)):
        for px in range(max(0, int(x) - half), min(image.width, int(x) + half + 1)):
            red, green, blue, alpha = image.getpixel((px, py))
            if alpha > 200 and red < 80 and green < 80 and blue < 80:
                count += 1
    return count


def _metal_and_ink(image, x, y) -> tuple[int, int]:
    """Silver applied indices versus flat black strokes."""
    metal = 0
    ink = 0
    x0 = max(0, int(x) - 8)
    y0 = max(0, int(y) - 8)
    x1 = min(image.width, int(x) + 9)
    y1 = min(image.height, int(y) + 9)
    for py in range(y0, y1):
        for px in range(x0, x1):
            red, green, blue, alpha = image.getpixel((px, py))
            if alpha < 200:
                continue
            if red < 70 and green < 70 and blue < 70:
                ink += 1
            elif 90 < red < 236 and abs(red - green) < 30 and abs(green - blue) < 30 and not (red > 220 and green > 210 and red > blue + 8):
                metal += 1
    return metal, ink


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
