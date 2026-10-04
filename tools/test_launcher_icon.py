"""Each watch gets a launcher icon at the size its compiler file requires."""

import unittest
from pathlib import Path

from PIL import Image

from generate_dial import LAUNCHER_SIZE, paint_launcher

ROOT = Path(__file__).resolve().parents[1]


class LauncherIconTests(unittest.TestCase):
    def test_painted_icon_matches_the_requested_square(self):
        icon = paint_launcher(40)
        self.assertEqual(icon.size, (40, 40))
        self.assertIsNotNone(icon.getbbox())

    def test_each_device_uses_its_own_launcher_size(self):
        jungle = (ROOT / "monkey.jungle").read_text().splitlines()
        for device, size in LAUNCHER_SIZE.items():
            line = next(item for item in jungle if item.startswith(f"{device}.resourcePath"))
            self.assertTrue(line.rstrip().endswith(f"resources-launcher-{size}"), device)
            with Image.open(ROOT / f"resources-launcher-{size}" / "drawables" / "launcher_icon.png") as icon:
                self.assertEqual(icon.size, (size, size), device)
