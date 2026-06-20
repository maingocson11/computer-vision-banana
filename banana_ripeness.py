from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


FONT_PATH = Path(__file__).resolve().parent / "fonts" / "DejaVuSans.ttf"


def _load_font(size=24):
    try:
        return ImageFont.truetype(str(FONT_PATH), size=size)
    except Exception:
        return ImageFont.load_default()


def classify_banana_crop(crop):
    """Classify a banana crop as ripe or unripe using dominant peel colors."""
    rgb = np.asarray(crop.convert("RGB"))
    if rgb.size == 0:
        return "Chuối non"

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    valid = (s > 35) & (v > 45)

    yellow = valid & (h >= 18) & (h <= 38)
    green = valid & (h >= 39) & (h <= 88)
    brown = (s > 40) & (v > 35) & (v < 150) & (h >= 5) & (h <= 28)

    valid_pixels = max(int(valid.sum()), 1)
    yellow_ratio = int(yellow.sum()) / valid_pixels
    green_ratio = int(green.sum()) / valid_pixels
    brown_ratio = int(brown.sum()) / valid_pixels
    ripe_score = yellow_ratio + (brown_ratio * 0.6)

    return "Chuối chín" if ripe_score >= green_ratio else "Chuối non"


def annotate_banana_ripeness(image, result):
    """Draw banana ripeness labels for YOLO detections on a PIL image."""
    annotated = image.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    font = _load_font()
    boxes = getattr(result, "boxes", None)
    summary = {"Chuối chín": 0, "Chuối non": 0}

    if boxes is None or len(boxes) == 0:
        return annotated, summary

    for box in boxes:
        x1, y1, x2, y2 = [int(round(v)) for v in box.xyxy[0].tolist()]
        x1 = max(0, min(x1, annotated.width - 1))
        y1 = max(0, min(y1, annotated.height - 1))
        x2 = max(x1 + 1, min(x2, annotated.width))
        y2 = max(y1 + 1, min(y2, annotated.height))

        crop = annotated.crop((x1, y1, x2, y2))
        label = classify_banana_crop(crop)
        summary[label] += 1
        color = (245, 185, 28) if label == "Chuối chín" else (34, 139, 34)

        draw.rectangle((x1, y1, x2, y2), outline=color, width=4)
        text_bbox = draw.textbbox((x1, y1), label, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        label_y = max(0, y1 - text_h - 8)
        draw.rectangle((x1, label_y, x1 + text_w + 12, label_y + text_h + 8), fill=color)
        draw.text((x1 + 6, label_y + 3), label, fill=(0, 0, 0), font=font)

    return annotated, summary


def format_ripeness_summary(summary):
    ripe = summary.get("Chuối chín", 0)
    unripe = summary.get("Chuối non", 0)
    return f"Chuối chín: **{ripe}** | Chuối non: **{unripe}**"
