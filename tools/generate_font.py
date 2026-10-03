"""Build the two Lunara face fonts and the generated Monkey C string tables.

Latin, Chinese, and Japanese are one glyph per character. Each Hindi word
is one shaped glyph, because the watch cannot position Devanagari marks.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from languages import (
    FACE_LARGE_PX,
    FACE_SMALL_PX,
    LEGEND_LARGE_PX,
    LEGEND_SMALL_PX,
    catalog_charset,
    legend_charset,
    legend_shaped_words,
    render_monkey,
    shaped_words,
)

ROOT = Path(__file__).resolve().parents[1]
SANS = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
TIMES = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
DEVA = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"


def main() -> None:
    font_dir = ROOT / "resources" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    _write_face_font(FACE_SMALL_PX, font_dir / "face_small.fnt", font_dir / "face_small_0.png", serif=True)
    _write_face_font(FACE_LARGE_PX, font_dir / "face_large.fnt", font_dir / "face_large_0.png", serif=True)
    _write_face_font(
        LEGEND_SMALL_PX,
        font_dir / "legend_small.fnt",
        font_dir / "legend_small_0.png",
        charset=legend_charset(),
        words=legend_shaped_words(),
    )
    _write_face_font(
        LEGEND_LARGE_PX,
        font_dir / "legend_large.fnt",
        font_dir / "legend_large_0.png",
        charset=legend_charset(),
        words=legend_shaped_words(),
    )
    (ROOT / "source" / "FaceText.mc").write_text(render_monkey())
    print("fonts and source/FaceText.mc")


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return (
        0x3000 <= code <= 0x30FF
        or 0x3400 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0xFF00 <= code <= 0xFFEF
    )


def _write_face_font(
    size: int,
    fnt_path: Path,
    png_path: Path,
    charset: str | None = None,
    words: list[tuple[str, str]] | None = None,
    serif: bool = False,
) -> None:
    latin = ImageFont.truetype(TIMES if serif else SANS, size)
    cjk = ImageFont.truetype(SONG, size, index=6) if serif else latin
    deva = ImageFont.truetype(DEVA, size, index=1)
    ascent, _descent = latin.getmetrics()
    glyphs = [_measure(latin, " ", size, space=True)]
    for char in catalog_charset() if charset is None else charset:
        if char == " ":
            continue
        face = cjk if _is_cjk(char) else latin
        glyphs.append(_measure(face, char, size))
    for glyph, word in shaped_words() if words is None else words:
        glyphs.append(_measure(deva, word, size, code=ord(glyph)))

    atlas_w = 512
    x = 1
    y = 1
    row_h = 0
    placed = []
    for glyph in glyphs:
        if glyph["width"] > 0 and x + glyph["width"] + 1 > atlas_w:
            x = 1
            y += row_h + 1
            row_h = 0
        glyph["atlas_x"] = x
        glyph["atlas_y"] = y
        if glyph["width"] > 0:
            x += glyph["width"] + 1
            row_h = max(row_h, glyph["height"])
        placed.append(glyph)
    atlas_h = max(1, y + row_h + 1)
    line_height = max(ascent + _descent, max(g["yoffset"] + g["height"] for g in placed))

    image = Image.new("L", (atlas_w, atlas_h), 0)
    for glyph in placed:
        if glyph["image"] is not None:
            image.paste(glyph["image"], (glyph["atlas_x"], glyph["atlas_y"]))
    _save_palette(image, png_path)

    lines = [
        f'info face="Lunara" size={size} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1 outline=0',
        f"common lineHeight={line_height} base={ascent} scaleW={atlas_w} scaleH={atlas_h} pages=1 packed=0 alphaChnl=0 redChnl=0 greenChnl=0 blueChnl=0",
        f'page id=0 file="{png_path.name}"',
        f"chars count={len(placed)}",
    ]
    for glyph in placed:
        lines.append(
            "char id={id:<6} x={atlas_x:<5} y={atlas_y:<5} width={width:<5} height={height:<5} "
            "xoffset={xoffset:<5} yoffset={yoffset:<5} xadvance={advance:<5} page=0 chnl=15".format(**glyph)
        )
    fnt_path.write_text("\n".join(lines) + "\n")
    print(f"{fnt_path.name}: {len(placed)} glyphs, atlas {atlas_w}x{atlas_h}")


def _measure(font: ImageFont.FreeTypeFont, text: str, size: int, code: int | None = None, space: bool = False) -> dict:
    code = ord(text) if code is None else code
    advance = max(1, int(math.ceil(font.getlength(text))))
    if space:
        return {
            "id": code,
            "width": 0,
            "height": 0,
            "xoffset": 0,
            "yoffset": 0,
            "advance": advance,
            "image": None,
            "atlas_x": 0,
            "atlas_y": 0,
        }
    ascent, _descent = font.getmetrics()
    left, top, right, bottom = font.getbbox(text)
    width = max(1, right - left)
    height = max(1, bottom - top)
    canvas = Image.new("L", (width + 4, height + 4), 0)
    ImageDraw.Draw(canvas).text((2 - left, 2 - top), text, font=font, fill=255)
    ink = canvas.getbbox()
    if ink is None:
        image = canvas.crop((0, 0, 1, 1))
    else:
        image = canvas.crop(ink)
    return {
        "id": code,
        "width": image.width,
        "height": image.height,
        "xoffset": left,
        "yoffset": ascent + top,
        "advance": advance,
        "image": image,
        "atlas_x": 0,
        "atlas_y": 0,
    }


def _save_palette(image: Image.Image, path: Path) -> None:
    paletted = Image.new("P", image.size, 0)
    paletted.putpalette([255, 255, 255] * 256)
    paletted.paste(image, (0, 0))
    paletted.save(path, format="PNG", transparency=bytes(range(256)))


if __name__ == "__main__":
    main()
