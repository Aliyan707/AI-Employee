#!/usr/bin/env python3
"""Generate a branded 1080x1080 Instagram post image for AI Employee."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

OUT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-/Files/ig_post_20260220.png")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1080

# Colors
BG_DARK   = (10, 17, 40)      # dark navy
ACCENT    = (0, 200, 120)     # emerald green
WHITE     = (255, 255, 255)
LIGHT     = (200, 210, 230)   # soft blue-grey
CARD_BG   = (20, 30, 60)      # slightly lighter navy

img = Image.new("RGB", (W, H), BG_DARK)
draw = ImageDraw.Draw(img)

# ── Background gradient-style blocks ─────────────────────────────────────────
# Top accent bar
draw.rectangle([0, 0, W, 8], fill=ACCENT)
# Bottom accent bar
draw.rectangle([0, H - 8, W, H], fill=ACCENT)

# Central card
card_margin = 60
draw.rounded_rectangle(
    [card_margin, card_margin + 30, W - card_margin, H - card_margin - 30],
    radius=24, fill=CARD_BG
)

# ── Fonts (fallback to default if system fonts unavailable) ───────────────────
def load_font(size, bold=False):
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

font_tag    = load_font(26, bold=False)
font_head   = load_font(58, bold=True)
font_sub    = load_font(34, bold=False)
font_item   = load_font(30, bold=False)
font_cta    = load_font(36, bold=True)
font_price  = load_font(30, bold=False)

def center_text(draw, y, text, font, color=WHITE, width=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]  # return height

def left_text(draw, x, y, text, font, color=WHITE):
    draw.text((x, y), text, font=font, fill=color)

# ── Content ───────────────────────────────────────────────────────────────────
y = 110

# Tag line
center_text(draw, y, "AI EMPLOYEE • KARACHI", font_tag, color=ACCENT)
y += 50

# Headline
h = center_text(draw, y, "Stop Running Admin.", font_head, WHITE)
y += h + 6
center_text(draw, y, "Start Running Business.", font_head, WHITE)
y += 80

# Divider
draw.rectangle([card_margin + 60, y, W - card_margin - 60, y + 3], fill=ACCENT)
y += 28

# Subheadline
center_text(draw, y, "Your AI Employee handles it all — 24/7:", font_sub, LIGHT)
y += 60

# Feature list
features = [
    "✓  Invoices & Odoo ERP — zero manual entry",
    "✓  Emails monitored & drafted automatically",
    "✓  Social media content & publishing",
    "✓  Weekly financial reports, delivered",
    "✓  Every action approved by YOU first",
]
lx = card_margin + 90
for feat in features:
    left_text(draw, lx, y, feat, font_item, LIGHT)
    y += 46

y += 20
draw.rectangle([card_margin + 60, y, W - card_margin - 60, y + 3], fill=ACCENT)
y += 30

# Result stat
center_text(draw, y, "Our clients reclaim 10–12 hours/week", font_sub, WHITE)
y += 50

# Price
center_text(draw, y, "Starting at PKR 50,000/month", font_price, LIGHT)
y += 60

# CTA box
cta_y1 = y
cta_y2 = y + 68
draw.rounded_rectangle(
    [card_margin + 80, cta_y1, W - card_margin - 80, cta_y2],
    radius=14, fill=ACCENT
)
center_text(draw, cta_y1 + 14, 'DM "AUDIT" for a FREE workflow review', font_cta, BG_DARK)
y = cta_y2 + 28

# Hashtags
center_text(draw, y, "#AIEmployee  #KarachiBusiness  #BusinessAutomation", font_tag, ACCENT)

img.save(str(OUT_PATH), "PNG", optimize=True)
print(f"Image saved: {OUT_PATH}")
print(f"Size: {W}x{H}px")
