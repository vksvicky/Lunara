"""Write the Lunara dial bitmap, eight moon sprites, and a preview."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from battery_style import battery_color
from dial_layout import BRAND, DialLayout, calendar_on, moon_phase
from dial_render import (
    date_hole_diameter,
    label_font,
    paint_battery,
    paint_date_hand,
    paint_embossed,
    paint_hands,
    render_dial,
    render_moon,
    scaled_battery_icon,
)
from languages import LANGUAGES

SIZES = (240, 260, 280, 360, 390, 416, 454, 466)
# Launcher icon pixels from each device's compiler.json, not the screen size.
LAUNCHER_SIZE = {
    "enduro3": 40,
    "epix2": 60,
    "epix2pro42mm": 60,
    "epix2pro47mm": 60,
    "epix2pro51mm": 60,
    "fenix7": 40,
    "fenix7pro": 40,
    "fenix7pronowifi": 40,
    "fenix7s": 40,
    "fenix7spro": 40,
    "fenix7x": 40,
    "fenix7xpro": 40,
    "fenix7xpronowifi": 40,
    "fenix843mm": 60,
    "fenix847mm": 65,
    "fenix8solar47mm": 40,
    "fenix8solar51mm": 40,
    "fenix8pro47mm": 65,
    "fenix943mm": 60,
    "fenix947mm": 65,
    "fenix9pro43mm": 60,
    "fenix9pro47mm": 65,
    "fenix9pro51mm": 65,
    "fenix9prosolar47mm": 40,
    "fenix9prosolar51mm": 40,
    "fenixe": 60,
    "venu2": 70,
    "venu2plus": 70,
    "venu2s": 61,
    "venu3": 70,
    "venu3s": 70,
    "fr255": 40,
    "fr255m": 40,
    "fr965": 65,
}
ROOT = Path(__file__).resolve().parents[1]
INK = (28, 26, 22, 255)
_TIMES = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"


def main() -> None:
    for size in SIZES:
        folder = ROOT / f"resources-round-{size}x{size}" / "drawables"
        folder.mkdir(parents=True, exist_ok=True)
        render_dial(size).save(folder / "dial_bg.png")
        moon_size = date_hole_diameter(size)
        for index in range(8):
            render_moon(moon_size, index / 8.0).save(folder / f"moon_{index}.png")
        icon_width = max(16, int(round((size / 2) * 0.24)))
        scaled_battery_icon(icon_width).save(folder / "battery_icon.png")
        _write_drawables(folder)
        print(f"{size}x{size}  moon {moon_size}px")

    _write_launcher()
    _wire_launcher_paths()
    _write_preview()
    print("preview -> docs/dial_preview.png")


def _write_drawables(folder: Path) -> None:
    lines = [
        "<drawables>",
        '    <bitmap id="dial_bg" filename="dial_bg.png" dithering="none" />',
        '    <bitmap id="battery_icon" filename="battery_icon.png" dithering="none" />',
    ]
    for index in range(8):
        lines.append(
            f'    <bitmap id="moon_{index}" filename="moon_{index}.png" dithering="none" />'
        )
    lines.append("</drawables>")
    (folder / "drawables.xml").write_text("\n".join(lines) + "\n")


def paint_launcher(size: int) -> Image.Image:
    """Ivory disc with a small moon, drawn at the device's launcher size."""
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pad = max(1, size // 65)
    ImageDraw.Draw(icon).ellipse((pad, pad, size - 1 - pad, size - 1 - pad), fill=(246, 240, 228, 255))
    moon_size = max(8, int(round(size * 28 / 65)))
    moon = render_moon(moon_size, 0.2)
    origin = ((size - moon_size) // 2, int(round(size * 22 / 65)))
    icon.alpha_composite(moon, origin)
    return icon


def _write_launcher() -> None:
    paint_launcher(65).save(ROOT / "resources" / "drawables" / "launcher_icon.png")
    for size in sorted(set(LAUNCHER_SIZE.values())):
        folder = ROOT / f"resources-launcher-{size}" / "drawables"
        folder.mkdir(parents=True, exist_ok=True)
        paint_launcher(size).save(folder / "launcher_icon.png")
        (folder / "drawables.xml").write_text(
            '<drawables>\n    <bitmap id="LauncherIcon" filename="launcher_icon.png" />\n</drawables>\n'
        )


def _wire_launcher_paths() -> None:
    jungle = ROOT / "monkey.jungle"
    lines = []
    for line in jungle.read_text().splitlines():
        device = line.split(".", 1)[0]
        if device in LAUNCHER_SIZE and ".resourcePath = resources-round-" in line:
            round_folder = line.split("= ", 1)[1].split(";", 1)[0]
            size = LAUNCHER_SIZE[device]
            line = f"{device}.resourcePath = {round_folder};$(base.resourcePath);resources-launcher-{size}"
        lines.append(line)
    jungle.write_text("\n".join(lines) + "\n")


def _tracked_label(image: Image.Image, text: str, xy: tuple[float, float], font, fill, tracking: float) -> None:
    widths = [font.getbbox(char)[2] - font.getbbox(char)[0] for char in text]
    total = sum(widths) + tracking * (len(text) - 1)
    cursor = xy[0] - total / 2.0
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for char, width in zip(text, widths):
        draw.text((cursor + width / 2.0, xy[1]), char, font=font, fill=fill, anchor="mm")
        cursor += width + tracking
    image.alpha_composite(overlay)


def _write_preview() -> None:
    size = 454
    image = render_dial(size)
    layout = DialLayout(size)
    today = date.today()
    month, weekday, day = calendar_on(datetime(today.year, today.month, today.day))
    english = next(lang for lang in LANGUAGES if lang.key == "eng")
    well = date_hole_diameter(size)
    moon = render_moon(well, moon_phase(today.year, today.month, today.day))
    origin = (
        int(round(layout.subdial_center[0] - well / 2)),
        int(round(layout.subdial_center[1] - well / 2)),
    )
    image.alpha_composite(moon, origin)

    radius = layout.radius
    month_name = english.months[month - 1]
    shared = label_font(layout)
    legend_font = ImageFont.truetype(_TIMES, max(12, int(radius * 0.075)))
    paint_date_hand(image, layout, day)
    paint_battery(image, layout, 86)
    paint_embossed(image, "86%", layout.battery_text_center, legend_font, INK)
    paint_embossed(image, month_name, layout.month_center, shared, INK)
    paint_embossed(image, english.weekdays[weekday - 1], layout.weekday_window.center, shared, INK)
    paint_embossed(image, BRAND, layout.brand_center, shared, INK)
    paint_hands(image, layout)

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    image.save(docs / "dial_preview.png")


if __name__ == "__main__":
    main()
