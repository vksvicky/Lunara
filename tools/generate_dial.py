"""Write the Lunara dial bitmap, eight moon sprites, and a preview."""

from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from battery_style import battery_color
from dial_layout import DialLayout, calendar_on, moon_phase
from dial_render import render_dial, render_moon
from languages import FACE_LARGE_PX, LEGEND_LARGE_PX, LANGUAGES

SIZES = (240, 260, 280, 360, 390, 416, 454, 466)
ROOT = Path(__file__).resolve().parents[1]
INK = (38, 34, 30, 255)


def main() -> None:
    for size in SIZES:
        folder = ROOT / f"resources-round-{size}x{size}" / "drawables"
        folder.mkdir(parents=True, exist_ok=True)
        render_dial(size).save(folder / "dial_bg.png")
        layout = DialLayout(size)
        moon_size = max(8, int(round(layout.moon_well_radius * 2)))
        for index in range(8):
            render_moon(moon_size, index / 8.0).save(folder / f"moon_{index}.png")
        _write_drawables(folder)
        print(f"{size}x{size}  moon {moon_size}px")

    _write_launcher()
    _write_preview()
    print("preview -> docs/dial_preview.png")


def _write_drawables(folder: Path) -> None:
    lines = ["<drawables>", '    <bitmap id="dial_bg" filename="dial_bg.png" />']
    for index in range(8):
        lines.append(f'    <bitmap id="moon_{index}" filename="moon_{index}.png" />')
    lines.append("</drawables>")
    (folder / "drawables.xml").write_text("\n".join(lines) + "\n")


def _write_launcher() -> None:
    icon = Image.new("RGBA", (65, 65), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.ellipse((1, 1, 63, 63), fill=(244, 237, 224, 255))
    moon = render_moon(28, 0.2)
    icon.alpha_composite(moon, (18, 22))
    path = ROOT / "resources" / "drawables" / "launcher_icon.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    icon.save(path)


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


def _hands(image: Image.Image, layout: DialLayout) -> None:
    """10:10, the time a dial is shown at. Thin, with a small gold cap."""
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = layout.center
    radius = layout.radius
    minute = -math.pi / 2.0 + (10.0 / 60.0) * math.tau
    hour = -math.pi / 2.0 + (10.0 / 12.0) * math.tau + (10.0 / 60.0) * (math.pi / 6.0)
    ink = (42, 38, 34, 255)
    for angle, length, width in ((hour, radius * 0.28, 2), (minute, radius * 0.34, 2)):
        draw.line(
            (cx, cy, cx + length * math.cos(angle), cy + length * math.sin(angle)),
            fill=ink,
            width=width,
        )
    cap = max(3, int(radius * 0.018))
    draw.ellipse((cx - cap, cy - cap, cx + cap, cy + cap), fill=(196, 164, 106, 255))
    image.alpha_composite(overlay)


def _write_preview() -> None:
    size = 454
    image = render_dial(size)
    layout = DialLayout(size)
    today = date.today()
    month, weekday, day = calendar_on(datetime(today.year, today.month, today.day))
    english = next(lang for lang in LANGUAGES if lang.key == "eng")
    well = int(round(layout.moon_well_radius * 2))
    moon = render_moon(well, moon_phase(today.year, today.month, today.day))
    origin = (
        int(round(layout.subdial_center[0] - well / 2)),
        int(round(layout.subdial_center[1] - well / 2)),
    )
    image.alpha_composite(moon, origin)

    text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Baskerville.ttc", FACE_LARGE_PX, index=0)
    legend = ImageFont.truetype("/System/Library/Fonts/Supplemental/Baskerville.ttc", LEGEND_LARGE_PX, index=0)
    quiet = (42, 38, 34, 255)
    draw = ImageDraw.Draw(image)
    charge = battery_color(86, 1, 12)
    draw.text(layout.battery_center, "86%", font=legend, fill=charge + (255,), anchor="mm")
    draw.text(layout.month_center, english.months[month - 1], font=text, fill=quiet, anchor="mm")
    draw.text(layout.weekday_window.center, english.weekdays[weekday - 1], font=legend, fill=quiet, anchor="mm")
    draw.text(layout.date_window.center, str(day), font=legend, fill=quiet, anchor="mm")
    gap = layout.radius * 0.055
    x, y = layout.perpetual_center
    _tracked_label(image, "PERPETUAL", (x, y - gap), legend, quiet, layout.radius * 0.004)
    _tracked_label(image, "CALENDAR", (x, y + gap), legend, quiet, layout.radius * 0.004)
    _hands(image, layout)

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    image.save(docs / "dial_preview.png")


if __name__ == "__main__":
    main()
