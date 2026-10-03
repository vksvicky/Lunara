"""Language catalog, battery text, and the setting that selects them."""

import re
import unittest
from pathlib import Path

from PIL import ImageFont

from dial_layout import DialLayout
from dial_render import brand_half_width, face_px, label_font, open_label_limit
from languages import (
    FACE_LARGE_PX,
    FACE_SMALL_PX,
    LEGEND_LARGE_PX,
    LEGEND_SMALL_PX,
    LANGUAGES,
    catalog_charset,
    device_language,
    format_battery,
    legend_charset,
    legend_shaped_words,
    render_monkey,
    shaped_words,
)

ROOT = Path(__file__).resolve().parents[1]
DEVA_PATH = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"
SANS_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

EXPECTED_IDS = (
    (1, "eng"),
    (2, "fre"),
    (3, "spa"),
    (4, "zhs"),
    (5, "zht"),
    (6, "jpn_kanji"),
    (7, "jpn_hira"),
    (8, "jpn_kata"),
    (9, "hin"),
    (10, "ita"),
    (11, "deu"),
)


def _blocks(text: str) -> set[str]:
    found = set()
    for char in text:
        if char.isspace():
            continue
        code = ord(char)
        if 0x3040 <= code <= 0x309F:
            found.add("hira")
        elif 0x30A0 <= code <= 0x30FF:
            found.add("kata")
        elif 0x4E00 <= code <= 0x9FFF:
            found.add("kanji")
        elif 0x0900 <= code <= 0x097F:
            found.add("deva")
        elif code < 0x250:
            found.add("latin")
        else:
            found.add("other")
    return found


def _font(language_key: str, size: int) -> ImageFont.FreeTypeFont:
    if language_key == "hin":
        return ImageFont.truetype(DEVA_PATH, size, index=1)
    return ImageFont.truetype(SANS_PATH, size)


def _width(text: str, language_key: str, size: int) -> float:
    return _font(language_key, size).getlength(text)


class LanguageCatalogTests(unittest.TestCase):
    def test_setting_ids_are_stable(self):
        pairs = [(lang.setting_id, lang.key) for lang in LANGUAGES]
        self.assertEqual(pairs, list(EXPECTED_IDS))

    def test_every_language_has_a_full_calendar(self):
        for lang in LANGUAGES:
            self.assertEqual(len(lang.months), 12, lang.key)
            self.assertEqual(len(lang.weekdays), 7, lang.key)
            self.assertGreater(len(lang.automatic), 0, lang.key)
            self.assertEqual(len(lang.perpetual), 2, lang.key)
            self.assertTrue(all(lang.months), lang.key)
            self.assertTrue(all(lang.weekdays), lang.key)

    def test_japanese_offers_kanji_hiragana_and_katakana(self):
        by_key = {lang.key: lang for lang in LANGUAGES}
        kanji = " ".join(by_key["jpn_kanji"].months + by_key["jpn_kanji"].perpetual)
        hira = " ".join(by_key["jpn_hira"].months + by_key["jpn_hira"].weekdays + by_key["jpn_hira"].perpetual)
        kata = " ".join(by_key["jpn_kata"].months + by_key["jpn_kata"].weekdays + by_key["jpn_kata"].perpetual)
        self.assertIn("kanji", _blocks(kanji))
        self.assertNotIn("hira", _blocks(kanji))
        self.assertNotIn("kata", _blocks(kanji))
        self.assertEqual(_blocks(hira), {"hira"})
        self.assertEqual(_blocks(kata), {"kata"})
        self.assertNotEqual(by_key["jpn_hira"].months, by_key["jpn_kata"].months)

    def test_chinese_simplified_and_traditional_differ(self):
        by_key = {lang.key: lang for lang in LANGUAGES}
        simplified = "".join(by_key["zhs"].weekdays) + by_key["zhs"].automatic
        traditional = "".join(by_key["zht"].weekdays) + by_key["zht"].automatic
        self.assertNotEqual(simplified, traditional)
        self.assertIn("kanji", _blocks(simplified))
        self.assertIn("kanji", _blocks(traditional))

    def test_hindi_is_devanagari_and_european_languages_keep_their_marks(self):
        by_key = {lang.key: lang for lang in LANGUAGES}
        hindi = "".join(by_key["hin"].months)
        self.assertEqual(_blocks(hindi), {"deva"})
        self.assertIn("É", by_key["fre"].months[11])
        self.assertIn("Ä", by_key["deu"].months[2])
        spanish = "".join(by_key["spa"].weekdays) + by_key["spa"].automatic
        self.assertTrue(any(ord(char) > 127 for char in spanish))

    def test_same_as_watch_maps_the_device_and_japanese_defaults_to_kanji(self):
        self.assertEqual(device_language(0, "fre"), "fre")
        self.assertEqual(device_language(0, "jpn"), "jpn_kanji")
        self.assertEqual(device_language(0, "zht"), "zht")
        self.assertEqual(device_language(0, "unknown"), "eng")
        self.assertEqual(device_language(9, "eng"), "hin")
        self.assertEqual(device_language(8, "eng"), "jpn_kata")
        self.assertEqual(device_language(None, "deu"), "deu")

    def test_live_text_fits_the_smallest_and_largest_dials(self):
        for size, px in ((240, FACE_SMALL_PX), (466, FACE_LARGE_PX)):
            layout = DialLayout(size)
            month_limit = layout.radius * 1.45
            window = layout.weekday_window.half_w * 2 * 0.92
            for lang in LANGUAGES:
                for month in lang.months:
                    self.assertLess(_width(month, lang.key, px), month_limit, f"{size} {lang.key} {month}")
                for label in lang.weekdays:
                    self.assertLess(_width(label, lang.key, px), window, f"{size} {lang.key} {label}")

    def test_month_weekday_and_name_share_one_font_size(self):
        for size in (240, 260, 390, 466):
            layout = DialLayout(size)
            expected = FACE_LARGE_PX if size >= 390 else FACE_SMALL_PX
            self.assertEqual(face_px(size), expected)
            latin = label_font(layout, "eng")
            hindi = label_font(layout, "hin")
            kana = label_font(layout, "jpn_hira")
            self.assertEqual(latin.getname()[0], "Times New Roman")
            self.assertEqual(latin.size, expected)
            self.assertEqual(hindi.size, expected)
            self.assertEqual(kana.size, expected)
            self.assertGreater(latin.getlength("LUNARA"), 0)

    def test_longest_month_in_every_language_fits_the_open_field(self):
        for size in (240, 260, 280, 360, 390, 416, 454, 466):
            layout = DialLayout(size)
            limit = open_label_limit(layout)
            for lang in LANGUAGES:
                font = label_font(layout, lang.key)
                widest = max(lang.months, key=lambda month: font.getlength(month))
                width = font.getlength(widest)
                self.assertLessEqual(width, limit, f"{size} {lang.key} {widest} {width:.1f} > {limit:.1f}")

    def test_legends_clear_the_brand_and_the_side_romans(self):
        for size, px in ((240, LEGEND_SMALL_PX), (260, LEGEND_SMALL_PX), (390, LEGEND_LARGE_PX), (466, LEGEND_LARGE_PX)):
            layout = DialLayout(size)
            half = brand_half_width(layout)
            gap = layout.radius * 0.02
            pad = layout.radius * 0.06
            nine = next(mark for mark in layout.romans() if mark.text == "IX")
            three = next(mark for mark in layout.romans() if mark.text == "III")
            brand_left = layout.center[0] - half - gap
            brand_right = layout.center[0] + half + gap
            for label in ("100%", "--%"):
                width = _width(label, "eng", px)
                left = layout.battery_text_center[0] - width / 2
                right = layout.battery_text_center[0] + width / 2
                self.assertGreater(left, nine.x + pad, f"{size} {label}")
                self.assertLess(right, brand_left, f"{size} {label}")
            self.assertLess(brand_right, three.x - pad)


class BatteryTextTests(unittest.TestCase):
    def test_percentage_is_clamped_and_labeled(self):
        self.assertEqual(format_battery(86), "86%")
        self.assertEqual(format_battery(0), "0%")
        self.assertEqual(format_battery(100), "100%")
        self.assertEqual(format_battery(-4), "0%")
        self.assertEqual(format_battery(140), "100%")
        self.assertEqual(format_battery(99.6), "100%")
        self.assertEqual(format_battery(None), "--%")

    def test_battery_sits_where_the_left_legend_was(self):
        layout = DialLayout(454)
        battery = layout.battery_center
        self.assertLess(battery[0], layout.center[0])
        self.assertGreater(layout.battery_text_center[1], battery[1])
        self.assertGreater(battery[1], layout.weekday_window.center[1])
        self.assertLess(battery[1], layout.subdial_center[1])


class GeneratedFaceTests(unittest.TestCase):
    def test_watch_source_matches_the_catalog(self):
        source = ROOT / "source" / "FaceText.mc"
        self.assertEqual(source.read_text(), render_monkey())

    def test_hindi_words_are_single_shaped_glyphs(self):
        words = shaped_words()
        self.assertGreaterEqual(len(words), 22)
        codes = [ord(glyph) for glyph, _ in words]
        self.assertEqual(codes, list(range(0xE000, 0xE000 + len(words))))

    def test_fonts_include_every_character_the_dial_draws(self):
        needed = set(catalog_charset())
        for word, _ in shaped_words():
            needed.add(word)
        needed.update("0123456789%")
        for name in ("face_small.fnt", "face_large.fnt"):
            text = (ROOT / "resources" / "fonts" / name).read_text()
            present = {int(code) for code in re.findall(r"char id=(\d+)", text)}
            missing = [char for char in needed if ord(char) not in present]
            self.assertEqual(missing, [], name)
        legend_needed = {ord(char) for char in legend_charset()}
        legend_needed.update(ord(glyph) for glyph, _word in legend_shaped_words())
        for name in ("legend_small.fnt", "legend_large.fnt"):
            text = (ROOT / "resources" / "fonts" / name).read_text()
            present = {int(code) for code in re.findall(r"char id=(\d+)", text)}
            missing = sorted(legend_needed - present)
            self.assertEqual(missing, [], name)

    def test_font_pixel_sizes_match_the_catalog(self):
        small = (ROOT / "resources" / "fonts" / "face_small.fnt").read_text()
        large = (ROOT / "resources" / "fonts" / "face_large.fnt").read_text()
        self.assertIn(f"size={FACE_SMALL_PX}", small)
        self.assertIn(f"size={FACE_LARGE_PX}", large)
        legend_small = (ROOT / "resources" / "fonts" / "legend_small.fnt").read_text()
        legend_large = (ROOT / "resources" / "fonts" / "legend_large.fnt").read_text()
        self.assertIn(f"size={LEGEND_SMALL_PX}", legend_small)
        self.assertIn(f"size={LEGEND_LARGE_PX}", legend_large)


if __name__ == "__main__":
    unittest.main()
