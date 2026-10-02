"""Three-panel baseline comparison used by the visual report."""

import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

_SEPARATOR_WIDTH = 4
_SEPARATOR_COLOR = (60, 60, 60)
_LABEL_HEIGHT = 28
_LABEL_BG = (30, 30, 30)
_LABEL_COLORS = {
    "BASELINE": (56, 189, 248),
    "CURRENT": (74, 222, 128),
    "DIFF": (248, 113, 113),
}


def _add_label(img: Image.Image, text: str) -> Image.Image:
    label = Image.new("RGB", (img.width, _LABEL_HEIGHT), _LABEL_BG)
    draw = ImageDraw.Draw(label)
    color = _LABEL_COLORS.get(text, (200, 200, 200))
    try:
        font = ImageFont.load_default(size=14)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tx = (img.width - (bbox[2] - bbox[0])) // 2
    ty = (_LABEL_HEIGHT - (bbox[3] - bbox[1])) // 2
    draw.text((tx, ty), text, fill=color, font=font)
    combined = Image.new("RGB", (img.width, _LABEL_HEIGHT + img.height))
    combined.paste(label, (0, 0))
    combined.paste(img, (0, _LABEL_HEIGHT))
    return combined


def _hands_mask(size: tuple[int, int]) -> Image.Image:
    """Hide the center 15% so clock hands do not count as a visual change."""
    width, height = size
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    cx, cy = width // 2, height // 2
    radius = int(min(width, height) * 0.15)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=0)
    return mask


def make_3panel_diff(baseline_path: str, current_path: str, diff_output_path: str) -> dict:
    if not os.path.exists(current_path):
        return {"diff_pct": 0.0, "has_baseline": os.path.exists(baseline_path), "composite_path": None}

    current_img = Image.open(current_path).convert("RGB")
    if not os.path.exists(baseline_path):
        panel = _add_label(current_img, "CURRENT")
        os.makedirs(os.path.dirname(diff_output_path), exist_ok=True)
        panel.save(diff_output_path)
        return {"diff_pct": None, "has_baseline": False, "composite_path": diff_output_path}

    baseline_img = Image.open(baseline_path).convert("RGB")
    if baseline_img.size != current_img.size:
        current_img = current_img.resize(baseline_img.size, Image.Resampling.LANCZOS)

    width, height = baseline_img.size
    hands_mask = _hands_mask((width, height))
    black = Image.new("RGB", (width, height), (0, 0, 0))
    baseline_cmp = Image.composite(baseline_img, black, hands_mask)
    current_cmp = Image.composite(current_img, black, hands_mask)

    diff = ImageChops.difference(baseline_cmp, current_cmp)
    changed = diff.convert("L").point(lambda pixel: 255 if pixel > 5 else 0)
    diff_pixels = sum(1 for pixel in changed.get_flattened_data() if pixel)
    visible = sum(1 for pixel in hands_mask.get_flattened_data() if pixel)
    diff_pct = (diff_pixels / visible) * 100.0 if visible else 0.0

    red_layer = Image.new("RGB", (width, height), (220, 38, 38))
    diff_panel = Image.composite(red_layer, current_img, changed)
    cx, cy = width // 2, height // 2
    radius = int(min(width, height) * 0.15)
    ImageDraw.Draw(diff_panel).ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=(80, 80, 80),
        width=1,
    )

    blue_tint = Image.new("RGB", (width, height), (14, 116, 144))
    baseline_panel = Image.blend(baseline_img, blue_tint, alpha=0.15)
    labeled = [
        _add_label(baseline_panel, "BASELINE"),
        _add_label(current_img.copy(), "CURRENT"),
        _add_label(diff_panel, "DIFF"),
    ]
    panel_h = height + _LABEL_HEIGHT
    separator = Image.new("RGB", (_SEPARATOR_WIDTH, panel_h), _SEPARATOR_COLOR)
    composite = Image.new("RGB", (width * 3 + _SEPARATOR_WIDTH * 2, panel_h))
    x = 0
    for index, panel in enumerate(labeled):
        composite.paste(panel, (x, 0))
        x += width
        if index < 2:
            composite.paste(separator, (x, 0))
            x += _SEPARATOR_WIDTH

    os.makedirs(os.path.dirname(diff_output_path), exist_ok=True)
    composite.save(diff_output_path)
    return {"diff_pct": diff_pct, "has_baseline": True, "composite_path": diff_output_path}
