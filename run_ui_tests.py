#!/usr/bin/env python3
"""Lunara visual regression and layout report.

Renders the dial, moon, language text, and battery at each round screen
size, checks the layout, and writes test_output/visual_report.html.

  python3 run_ui_tests.py
  python3 run_ui_tests.py --device fenix7
  python3 run_ui_tests.py --full
  python3 run_ui_tests.py --update-baselines
  python3 run_ui_tests.py --with-hands
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import date, datetime

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from battery_style import battery_color  # noqa: E402
from dial_layout import BRAND, DialLayout, calendar_on, moon_phase  # noqa: E402
from dial_render import (  # noqa: E402
    date_hole_diameter,
    label_font,
    paint_battery,
    paint_date_hand,
    paint_embossed,
    paint_hands,
    render_dial,
    render_moon,
)
from languages import (  # noqa: E402
    LEGEND_LARGE_PX,
    LEGEND_SMALL_PX,
    LANGUAGES,
    format_battery,
)
from test_ui.image_utils import make_3panel_diff  # noqa: E402
from ui_report import generate_report  # noqa: E402

REPORT_PATH = os.path.join(ROOT, "test_output", "visual_report.html")
BASELINES_DIR = os.path.join(ROOT, "test_output", "baselines")
DIFFS_DIR = os.path.join(ROOT, "test_output", "diffs")
SANS = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
DEVA = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"
INK = (38, 34, 30, 255)

DEVICES = [
    ("fenix7s", 240, "240×240 MIP", "Fenix 7S / 7S Pro"),
    ("fenix7", 260, "260×260 MIP", "Fenix 7 / Fenix 8 Solar 47mm"),
    ("fr255", 260, "260×260 MIP", "Forerunner 255 / 255 Music"),
    ("enduro3", 280, "280×280 MIP", "Enduro 3 / Fenix 7X"),
    ("venusq2", (320, 360), "320×360 AMOLED", "Venu Sq 2"),
    ("venu2s", 360, "360×360 AMOLED", "Venu 2S"),
    ("epix2pro42mm", 390, "390×390 AMOLED", "Epix 2 Pro 42mm / Venu 3S"),
    ("venu2", 416, "416×416 AMOLED", "Venu 2 / Epix Gen 2"),
    ("venu3", 454, "454×454 AMOLED", "Venu 3 / Forerunner 965 / Fenix 8 47mm"),
    ("fenix9pro51mm", 466, "466×466 AMOLED", "Fenix 9 Pro 51mm"),
]

# Every device renders English and a low battery. The remaining languages
# are spread across the matrix so a focused run still covers each script.
LANGUAGE_DISTRIBUTION = {
    "fenix7s": ["french", "hindi"],
    "fenix7": ["spanish"],
    "fr255": ["german"],
    "enduro3": ["italian"],
    "venusq2": ["chinese_simplified"],
    "venu2s": ["chinese_traditional"],
    "epix2pro42mm": ["japanese_kanji"],
    "venu2": ["japanese_hiragana"],
    "venu3": ["japanese_katakana"],
    "fenix9pro51mm": ["hindi"],
}

PASSES = [
    {"id": "english", "name": "English", "key": "eng", "battery": 86, "description": "December, Saturday, 86% battery."},
    {"id": "french", "name": "Français", "key": "fre", "battery": 86, "description": "French month, weekday, and legends."},
    {"id": "spanish", "name": "Español", "key": "spa", "battery": 86, "description": "Spanish month, weekday, and legends."},
    {"id": "chinese_simplified", "name": "简体中文", "key": "zhs", "battery": 86, "description": "Simplified Chinese calendar."},
    {"id": "chinese_traditional", "name": "繁體中文", "key": "zht", "battery": 86, "description": "Traditional Chinese calendar."},
    {"id": "japanese_kanji", "name": "日本語（漢字）", "key": "jpn_kanji", "battery": 86, "description": "Japanese kanji calendar."},
    {"id": "japanese_hiragana", "name": "日本語（ひらがな）", "key": "jpn_hira", "battery": 86, "description": "Japanese hiragana calendar."},
    {"id": "japanese_katakana", "name": "日本語（カタカナ）", "key": "jpn_kata", "battery": 86, "description": "Japanese katakana calendar."},
    {"id": "hindi", "name": "हिन्दी", "key": "hin", "battery": 86, "description": "Hindi calendar, shaped as whole words."},
    {"id": "italian", "name": "Italiano", "key": "ita", "battery": 86, "description": "Italian month, weekday, and legends."},
    {"id": "german", "name": "Deutsch", "key": "deu", "battery": 86, "description": "German month, weekday, and legends."},
    {"id": "battery_low", "name": "Battery 5%", "key": "eng", "battery": 5, "description": "Low battery is still the only metric."},
    {"id": "battery_empty", "name": "Battery 0%", "key": "eng", "battery": 0, "description": "Empty battery clamps to 0%."},
    {"id": "battery_full", "name": "Battery 100%", "key": "eng", "battery": 100, "description": "Full battery clamps to 100%."},
]
PASS_BY_ID = {item["id"]: item for item in PASSES}
BY_KEY = {lang.key: lang for lang in LANGUAGES}
_DIALS: dict[int, Image.Image] = {}
_FONTS: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    cached = _FONTS.get((kind, size))
    if cached is not None:
        return cached
    if kind == "deva":
        loaded = ImageFont.truetype(DEVA, size, index=1)
    else:
        loaded = ImageFont.truetype(SANS, size)
    _FONTS[(kind, size)] = loaded
    return loaded


def _dial(size: int) -> Image.Image:
    cached = _DIALS.get(size)
    if cached is None:
        cached = render_dial(size)
        _DIALS[size] = cached
    return cached.copy()


def _flatten(image: Image.Image) -> Image.Image:
    background = Image.new("RGB", image.size, (0, 0, 0))
    background.paste(image, mask=image.getchannel("A"))
    return background


def render_face(size: int | tuple[int, int], language_key: str, battery: float, with_hands: bool) -> Image.Image:
    layout = DialLayout(size)
    if isinstance(size, tuple):
        w, h = size
        dial_side = min(w, h)
        dial_img = _dial(dial_side)
        image = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        image.paste(dial_img, (int((w - dial_side) / 2), int((h - dial_side) / 2)), dial_img)
        well = date_hole_diameter(dial_side)
        legend_px = LEGEND_LARGE_PX if dial_side >= 390 else LEGEND_SMALL_PX
    else:
        image = _dial(size)
        well = date_hole_diameter(size)
        legend_px = LEGEND_LARGE_PX if size >= 390 else LEGEND_SMALL_PX
    today = date.today()
    month, weekday, day = calendar_on(datetime(today.year, today.month, today.day))
    phase = moon_phase(today.year, today.month, today.day)
    moon = render_moon(well, phase)
    origin = (
        int(round(layout.subdial_center[0] - well / 2)),
        int(round(layout.subdial_center[1] - well / 2)),
    )
    image.alpha_composite(moon, origin)

    lang = BY_KEY[language_key]
    month_name = lang.months[month - 1]
    shared = label_font(layout, language_key)
    name = label_font(layout, "eng")
    legend = _font("deva" if language_key == "hin" else "sans", legend_px)
    paint_date_hand(image, layout, day)
    paint_battery(image, layout, battery)
    # Classic green/amber/red so a screenshot does not change when the hour changes.
    charge = battery_color(battery, 1, 12)
    paint_embossed(image, format_battery(battery), layout.battery_text_center, legend, charge + (255,))
    paint_embossed(image, month_name, layout.month_center, shared, INK)
    paint_embossed(image, lang.weekdays[weekday - 1], layout.weekday_window.center, shared, INK)
    paint_embossed(image, BRAND, layout.brand_center, name, INK)
    if with_hands:
        paint_hands(image, layout)
    return _flatten(image)


def _paint_count(image: Image.Image, x: float, y: float, half: int) -> int:
    count = 0
    for py in range(max(0, int(y) - half), min(image.height, int(y) + half + 1)):
        for px in range(max(0, int(x) - half), min(image.width, int(x) + half + 1)):
            red, green, blue = image.getpixel((px, py))
            if abs(red - 244) + abs(green - 237) + abs(blue - 224) > 70:
                count += 1
    return count


def _ink_count(image: Image.Image, x: float, y: float, half: int) -> int:
    count = 0
    for py in range(max(0, int(y) - half), min(image.height, int(y) + half + 1)):
        for px in range(max(0, int(x) - half), min(image.width, int(x) + half + 1)):
            red, green, blue = image.getpixel((px, py))
            if red < 120 and green < 120 and blue < 120 and red > 15:
                count += 1
    return count


def validate(image: Image.Image, layout: DialLayout, with_hands: bool) -> list[str]:
    issues = []
    field_x = int(layout.center[0] + layout.radius * 0.50)
    field_y = int(layout.center[1] - layout.radius * 0.15)
    red, green, blue = image.getpixel((field_x, field_y))
    if not (red > 210 and green > 200 and red > blue + 8):
        issues.append("DIAL: the open field is not the ivory ground.")
    corner = image.getpixel((1, 1))
    if sum(corner) > 40:
        issues.append("BEZEL: a corner pixel is lit outside the round face.")
    mx, my = (int(round(layout.subdial_center[0])), int(round(layout.subdial_center[1])))
    mr, mg, mb = image.getpixel((mx, my))
    lit = mr > 110 and mg > 100 and mb > 80 and mr + mg > mb * 1.6
    sky = mb > mr and mb > mg
    hand = abs(mr - mg) < 24 and abs(mg - mb) < 24 and 40 < mr < 110
    if not lit and not sky and not hand:
        issues.append("MOON: the sub-dial center is neither the sky, the moon, nor the date hand.")
    half = max(8, int(layout.radius * 0.045))
    _, _, day = calendar_on(datetime(date.today().year, date.today().month, date.today().day))
    checks = [
        ("BATTERY", layout.battery_center),
        ("MONTH", layout.month_center),
        ("WEEKDAY", layout.weekday_window.center),
        ("DATE", layout.date_hand_tip(day)),
    ]
    for name, point in checks:
        sample_half = int(round(layout.radius * 0.12)) if name == "BATTERY" else half
        count = _paint_count(image, point[0], point[1], sample_half) if name == "BATTERY" else _ink_count(image, point[0], point[1], sample_half)
        if count < 4:
            issues.append(f"{name}: expected ink was not drawn.")
    if layout.battery_center[0] >= layout.center[0] or layout.battery_text_center[1] <= layout.battery_center[1]:
        issues.append("BATTERY: the percentage is not under the icon.")
    return issues


def annotate(image: Image.Image, layout: DialLayout) -> Image.Image:
    marked = image.copy()
    draw = ImageDraw.Draw(marked)
    half = max(8, int(layout.radius * 0.05))
    boxes = [
        layout.battery_center,
        layout.month_center,
        layout.weekday_window.center,
        layout.battery_text_center,
        layout.date_hand_tip(2),
    ]
    for point in boxes:
        draw.rectangle(
            (point[0] - half * 2, point[1] - half, point[0] + half * 2, point[1] + half),
            outline=(74, 222, 128),
            width=2,
        )
    sx, sy = layout.subdial_center
    ring = layout.date_ring_radius
    draw.ellipse((sx - ring, sy - ring, sx + ring, sy + ring), outline=(251, 146, 60), width=2)
    radius = int(min(image.size) * 0.15)
    cx, cy = layout.center
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(56, 189, 248), width=2)
    return marked


def selected_passes(dev_id: str, full_mode: bool) -> list[dict]:
    if full_mode:
        return list(PASSES)
    wanted = ["english", "battery_low", *LANGUAGE_DISTRIBUTION.get(dev_id, [])]
    return [PASS_BY_ID[item] for item in wanted]


def run_device(dev_id, size, res_info, dev_name, output_dir, full_mode, with_hands) -> list[dict]:
    results = []
    layout = DialLayout(size)
    for spec in selected_passes(dev_id, full_mode):
        print(f"  [{spec['id']}] {spec['name']}")
        image = render_face(size, spec["key"], spec["battery"], with_hands)
        issues = validate(image, layout, with_hands)
        today = date.today()
        month, weekday, day = calendar_on(datetime(today.year, today.month, today.day))
        english = BY_KEY["eng"]
        img_path = os.path.join(output_dir, f"{dev_id}_{spec['id']}.png")
        zones_path = os.path.join(output_dir, f"{dev_id}_{spec['id']}_zones.png")
        image.save(img_path)
        annotate(image, layout).save(zones_path)
        results.append({
            "id": spec["id"],
            "pass_name": spec["name"],
            "description": spec["description"],
            "current_img": img_path,
            "zones_img": zones_path,
            "passed": not issues,
            "issues": issues,
            "slots": [
                f"Language: {spec['name']}",
                f"Battery: {format_battery(spec['battery'])}",
                f"Month: {english.months[month - 1]}",
                f"Weekday: {english.weekdays[weekday - 1]}",
                f"Date: {day}",
            ],
        })
    return results


def process_result_baseline(result, dev_id, update_baselines=False):
    pass_id = result["id"]
    img_path = result.get("current_img")
    base_path = os.path.join(BASELINES_DIR, f"{dev_id}_{pass_id}.png")
    diff_path = os.path.join(DIFFS_DIR, f"{dev_id}_{pass_id}.png")
    if update_baselines:
        if img_path and os.path.exists(img_path) and result.get("passed", False):
            os.makedirs(BASELINES_DIR, exist_ok=True)
            shutil.copy2(img_path, base_path)
            print(f"    [BASELINE SAVED] {os.path.basename(base_path)}")
            result["has_baseline"] = True
            result["baseline_img"] = base_path
            result["diff_img"] = None
            result["diff_pct"] = 0.0
        else:
            reasons = ", ".join(result.get("issues", [])) or "layout validation failed"
            print(f"    [BASELINE FAILED] {dev_id}_{pass_id}: {reasons}")
            result["has_baseline"] = False
            result["passed"] = False
            result["issues"] = list(result.get("issues", [])) + [f"CAPTURE FAILED: {reasons}"]
        return result

    has_baseline = os.path.exists(base_path)
    result["has_baseline"] = has_baseline
    result["baseline_img"] = base_path if has_baseline else None
    result["issues"] = list(result.get("issues", []))
    if not has_baseline:
        result["issues"].insert(0, f"MISSING BASELINE: {base_path}. Run ./run_tests.sh ui --update-baselines")
        result["passed"] = False
        result["diff_img"] = None
        result["diff_pct"] = None
        return result
    diff = make_3panel_diff(base_path, img_path, diff_path)
    result["diff_img"] = diff.get("composite_path")
    result["diff_pct"] = diff.get("diff_pct")
    if diff.get("diff_pct") is not None and diff["diff_pct"] > 5.0:
        result["issues"].append(f"VISUAL REGRESSION: {diff['diff_pct']:.2f}% pixel variance from baseline.")
        result["passed"] = False
    return result


def backup_baselines() -> None:
    if not os.path.isdir(BASELINES_DIR) or not os.listdir(BASELINES_DIR):
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(ROOT, "test_output", f"baselines_backup_{stamp}")
    shutil.copytree(BASELINES_DIR, dest)
    print(f"Backed up baselines to {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lunara visual regression report")
    parser.add_argument("--device", action="append", default=[])
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--update-baselines", action="store_true")
    parser.add_argument("--with-hands", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    chosen = [item for item in DEVICES if not args.device or item[0] in args.device]
    if args.device and len(chosen) != len(args.device):
        known = ", ".join(item[0] for item in DEVICES)
        print(f"Unknown device. Choose from: {known}")
        return 2
    if args.update_baselines:
        backup_baselines()
    output_dir = os.path.join(ROOT, "test_output", "current")
    os.makedirs(output_dir, exist_ok=True)
    all_results = []
    failures = 0
    for dev_id, size, res_info, dev_name in chosen:
        print(f"\n{dev_name} ({dev_id}, {res_info})")
        raw = run_device(dev_id, size, res_info, dev_name, output_dir, args.full, args.with_hands)
        processed = [process_result_baseline(item, dev_id, args.update_baselines) for item in raw]
        failures += sum(1 for item in processed if not item.get("passed"))
        all_results.append((dev_id, res_info, dev_name, processed))
    generate_report(all_results, get_current_branch(), REPORT_PATH, ROOT, args.update_baselines)
    print(f"Failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
