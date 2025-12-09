import os
import json
from pathlib import Path
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# === Import plotting module for sensor_legend_mapping ===
import plot_functions
sensor_legend_mapping = plot_functions.sensor_legend_mapping



# ============================================================
#  PATHS & CONFIG (RELATIVE, FROM path.json)
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH  = PROJECT_ROOT / "config" / "path.json"

with open(CONFIG_PATH, "r") as f:
    paths = json.load(f)

FONT_DIR   = PROJECT_ROOT / paths["font_dir"]
PLOTS_DIR  = PROJECT_ROOT / paths["plots_dir"]
STATIC_DIR = PROJECT_ROOT / paths["static_dir"]
REPORT_DIR = PROJECT_ROOT / paths["report_dir"]

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ========= BASIC REPORT CONFIG =========
YEAR    = 2025
WEEK_NO = 47

OUTPUT = REPORT_DIR / f"weekly_report_{YEAR}_W{WEEK_NO}.pdf"

BACKGROUND_IMG = STATIC_DIR / "Title_bckgrnd.png"
FALLBACK_IMG = STATIC_DIR / "fig_missing.png"

DATE_FROM = datetime(2025, 11, 17).strftime("%d. %b. %Y")
DATE_TO   = datetime(2025, 11, 23).strftime("%d. %b. %Y")

# ========= PAGE SETTINGS =========
PAGE = landscape(A4)
WIDTH, HEIGHT = PAGE


# ============================================================
#  LOAD FONTS
# ============================================================

FONTS = {}

for f in sorted(os.listdir(FONT_DIR)):
    if f.lower().endswith(".ttf"):
        name = Path(f).stem
        path = FONT_DIR / f
        pdfmetrics.registerFont(TTFont(name, str(path)))
        FONTS[name] = name

print("Loaded fonts:", list(FONTS.keys()))


# ============================================================
#  HEADER & FOOTER
# ============================================================

def draw_header(c):
    left_text  = "Structural Health Monitoring Steel Arena"
    right_text = f"Year {YEAR} — Week {WEEK_NO}"

    font_name = FONTS["Montserrat-Regular"]
    size = 14

    c.setFont(font_name, size)
    c.drawString(40, HEIGHT - 40, left_text)

    rw = stringWidth(right_text, font_name, size)
    c.drawString(WIDTH - rw - 40, HEIGHT - 40, right_text)

    # horizontal line under header
    c.setLineWidth(0.7)
    c.line(40, HEIGHT - 55, WIDTH - 40, HEIGHT - 55)


def draw_footer(c, page_no):
    size = 12

    # horizontal line above footer
    c.setLineWidth(0.2)
    c.line(40, 45, WIDTH - 40, 45)

    # Left: company
    c.setFont(FONTS["Montserrat-Light"], size)
    c.drawString(40, 25, "Rubint Technologies s. r. o.")

    # PAGE NUMBER (center, clickable → ToC)
    label = f"Page {page_no}"
    mid_font = FONTS["Montserrat-Regular"]
    c.setFont(mid_font, size)

    mw = stringWidth(label, mid_font, size)
    x_mid = (WIDTH - mw) / 2
    y_mid = 25

    c.drawString(x_mid, y_mid, label)

    # Make "Page X" clickable → Table of Contents (PAGE_2)
    if page_no >= 2:
        c.linkRect(
            "",
            "PAGE_2",  # bookmark name for ToC page
            Rect=(x_mid, y_mid - 2, x_mid + mw, y_mid + size + 2),
            relative=0,
            thickness=0,
        )

    # Right: Ing. Jakub Rubint, PhD. (only name bold)
    left = "Ing. "
    center = "Jakub Rubint"
    right = ", PhD."

    x = WIDTH - 40
    total_w = (
        stringWidth(left,  FONTS["Montserrat-Light"], size)
        + stringWidth(center, FONTS["Montserrat-Bold"],  size)
        + stringWidth(right, FONTS["Montserrat-Light"], size)
    )
    start = x - total_w

    c.setFont(FONTS["Montserrat-Light"], size)
    c.drawString(start, 25, left)

    pos = start + stringWidth(left, FONTS["Montserrat-Light"], size)
    c.setFont(FONTS["Montserrat-Bold"], size)
    c.drawString(pos, 25, center)

    pos += stringWidth(center, FONTS["Montserrat-Bold"], size)
    c.setFont(FONTS["Montserrat-Light"], size)
    c.drawString(pos, 25, right)


# ============================================================
#  CANVAS INIT & TITLE PAGE
# ============================================================

c = canvas.Canvas(str(OUTPUT), pagesize=PAGE)

# === Background image on title page ===
try:
    img = ImageReader(str(BACKGROUND_IMG))
    iw, ih = img.getSize()
    scale = WIDTH / iw
    new_w = WIDTH
    new_h = ih * scale
    x = 0
    y = (HEIGHT - new_h) / 2

    c.saveState()
    # c.setFillAlpha(0.5)  # if transparency needed, depends on backend
    c.drawImage(str(BACKGROUND_IMG), x, y, width=new_w, height=new_h, mask="auto")
    c.restoreState()

except Exception as e:
    print("Background error:", e)

# === Week info on title page (top-right) ===
info = [
    f"Week: #{WEEK_NO}",
    f"From: {DATE_FROM}",
    f"To:   {DATE_TO}",
]

font_name = FONTS["Montserrat-Regular"]
size = 18
c.setFont(font_name, size)

right_margin = 10 * mm
top_margin   = 14 * mm

start_y = HEIGHT - top_margin

for i, line in enumerate(info):
    lw = stringWidth(line, font_name, size)
    x = WIDTH - lw - right_margin
    y = start_y - i * (size + 6)
    c.drawString(x, y, line)

# End title page
c.showPage()


# ============================================================
#  PAGE 2 — TABLE OF CONTENTS
# ============================================================

page_no = 2
c.bookmarkPage("PAGE_2")
draw_header(c)
draw_footer(c, page_no)

# --- Title ---
c.setFont(FONTS["Montserrat-Bold"], 26)
toc_title = "Table of Contents"
tw = stringWidth(toc_title, FONTS["Montserrat-Bold"], 26)
c.drawString((WIDTH - tw) / 2, HEIGHT - 120, toc_title)

# ---------- BUILD TOC ENTRIES ----------
TOC_ENTRIES = []

# 1) FFT + GRID (A30–A35)
page_cursor = 3
for num in range(30, 36):
    key = f"A{num}"
    label = sensor_legend_mapping[key]

    TOC_ENTRIES.append((f"{key} – {label} — FFT KDE", page_cursor))
    page_cursor += 1

    TOC_ENTRIES.append((f"{key} – {label} — Daily Variation", page_cursor))
    page_cursor += 1

# 2) Strain sensors (S7–S29)
for num in range(7, 30):
    key = f"S{num}"
    label = sensor_legend_mapping[key]
    TOC_ENTRIES.append((f"{key} – {label} — Strain–Temperature", page_cursor))
    page_cursor += 1

# 3) Temperatures
TOC_ENTRIES.append(("Temperatures — Column Summary", page_cursor)); page_cursor += 1
TOC_ENTRIES.append(("Temperatures — Arch Summary",   page_cursor)); page_cursor += 1

# -------- LAYOUT SETTINGS (2 COLUMNS) --------
FONT_SIZE = 10
c.setFont(FONTS["Montserrat-Regular"], FONT_SIZE)

COLS = 2
GUTTER = 50
COL_WIDTH = ((WIDTH - 120) - GUTTER * (COLS - 1)) / COLS

START_X = 60
START_Y = HEIGHT - 170
LINE_SPACING = FONT_SIZE * 1.8

usable_height = START_Y - 70
ROWS_PER_COL = int(usable_height / LINE_SPACING)

x = START_X
y = START_Y
row_in_col = 0
col = 0

dot_char = "."
dot_width = stringWidth(dot_char, FONTS["Montserrat-Regular"], FONT_SIZE)

for label, target_page in TOC_ENTRIES:
    # Label
    c.drawString(x, y, label)
    label_w = stringWidth(label, FONTS["Montserrat-Regular"], FONT_SIZE)

    # Page number (right of column)
    right_text = str(target_page)
    page_w = stringWidth(right_text, FONTS["Montserrat-Regular"], FONT_SIZE)
    page_x = x + COL_WIDTH - page_w
    c.drawString(page_x, y, right_text)

    # Dots between label and page number
    padding = 5
    dot_start_x = x + label_w + padding
    dot_end_x   = page_x - padding
    available_width = dot_end_x - dot_start_x

    if available_width > 0:
        num_dots = int(available_width / dot_width)
        dot_line = dot_char * num_dots
        c.drawString(dot_start_x, y, dot_line)

    # Clickable area for this entry
    c.linkRect(
        "",
        f"PAGE_{target_page}",
        Rect=(x, y - 2, x + COL_WIDTH, y + FONT_SIZE + 2),
        thickness=0,
        relative=0,
    )

    # Next row
    y -= LINE_SPACING
    row_in_col += 1

    if row_in_col >= ROWS_PER_COL:
        col += 1
        if col >= COLS:
            break
        x = START_X + col * (COL_WIDTH + GUTTER)
        y = START_Y
        row_in_col = 0

# Finish ToC page
c.showPage()
page_no = 3


# ============================================================
#  BLOCK: ALTERNATING FFT KDE + DAILY GRID PLOTS (A30–A35)
# ============================================================

BASE = PLOTS_DIR

ALTERNATING_PLOTS = []
for num in range(30, 36):
    ALTERNATING_PLOTS.append(BASE / f"A{num}_fft_kde.png")
    ALTERNATING_PLOTS.append(BASE / f"A{num}_daily_v_grid.png")

for plot_path in ALTERNATING_PLOTS:
    plot_path = Path(plot_path)

    c.bookmarkPage(f"PAGE_{page_no}")
    draw_header(c)
    draw_footer(c, page_no)

    # Try real image, or fallback placeholder
    try:
        plot_img = ImageReader(str(plot_path))
    except Exception:
        print(f"[!] Missing plot → using placeholder: {plot_path}")
        plot_img = ImageReader(str(FALLBACK_IMG))

    # Scaling
    TARGET_W = WIDTH - 120
    TARGET_H = HEIGHT - 200

    orig_w, orig_h = plot_img.getSize()
    orig_ratio   = orig_w / orig_h
    target_ratio = TARGET_W / TARGET_H

    if orig_ratio > target_ratio:
        final_w = TARGET_W
        final_h = TARGET_W / orig_ratio
    else:
        final_h = TARGET_H
        final_w = TARGET_H * orig_ratio

    x = (WIDTH - final_w) / 2
    y = (HEIGHT - final_h) / 2

    # MUST draw plot_img, not plot_path!
    c.drawImage(plot_img, x, y, width=final_w, height=final_h)

    c.showPage()
    page_no += 1


# ============================================================
#  BLOCK: STRAIN–TEMPERATURE PLOTS (S7–S29)
# ============================================================

SST_PLOTS = [BASE / f"S{num}_strain_temp.png" for num in range(7, 30)]

for plot_path in SST_PLOTS:
    plot_path = Path(plot_path)

    c.bookmarkPage(f"PAGE_{page_no}")
    draw_header(c)
    draw_footer(c, page_no)

    # Try real image, otherwise fallback
    try:
        plot_img = ImageReader(str(plot_path))
    except Exception:
        print(f"[!] Missing plot → using placeholder: {plot_path}")
        plot_img = ImageReader(str(FALLBACK_IMG))

    # Target frame inside the A4 landscape
    TARGET_W = WIDTH - 120
    TARGET_H = HEIGHT - 200

    # Original figure size (from the loaded image!)
    orig_w, orig_h = plot_img.getSize()
    orig_ratio   = orig_w / orig_h
    target_ratio = TARGET_W / TARGET_H

    # Maintain aspect ratio
    if orig_ratio > target_ratio:
        final_w = TARGET_W
        final_h = TARGET_W / orig_ratio
    else:
        final_h = TARGET_H
        final_w = TARGET_H * orig_ratio

    # Center the image
    x = (WIDTH - final_w) / 2
    y = (HEIGHT - final_h) / 2

    # ⭐ FIXED: draw *plot_img*, NOT plot_path
    c.drawImage(plot_img, x, y, width=final_w, height=final_h)

    c.showPage()
    page_no += 1


# ============================================================
#  BLOCK: TEMPERATURE SUMMARY PLOTS (ARCH + COLUMN)
# ============================================================

# ------------------------
# 1) Arch temperatures
# ------------------------

plot_path = BASE / "temps_arch.png"

c.bookmarkPage(f"PAGE_{page_no}")
draw_header(c)
draw_footer(c, page_no)

# Load real plot or fallback
try:
    plot_img = ImageReader(str(plot_path))
except Exception:
    print(f"[!] Missing plot → using placeholder: {plot_path}")
    plot_img = ImageReader(str(FALLBACK_IMG))

TARGET_W = WIDTH - 120
TARGET_H = HEIGHT - 200

orig_w, orig_h = plot_img.getSize()
orig_ratio   = orig_w / orig_h
target_ratio = TARGET_W / TARGET_H

if orig_ratio > target_ratio:
    final_w = TARGET_W
    final_h = TARGET_W / orig_ratio
else:
    final_h = TARGET_H
    final_w = TARGET_H * orig_ratio

x = (WIDTH - final_w) / 2
y = (HEIGHT - final_h) / 2

# ⭐ FIXED: draw loaded image, not filename
c.drawImage(plot_img, x, y, width=final_w, height=final_h)

c.showPage()
page_no += 1


# ------------------------
# 2) Column temperatures
# ------------------------

plot_path = BASE / "temps_col.png"

c.bookmarkPage(f"PAGE_{page_no}")
draw_header(c)
draw_footer(c, page_no)

# Load real plot or fallback
try:
    plot_img = ImageReader(str(plot_path))
except Exception:
    print(f"[!] Missing plot → using placeholder: {plot_path}")
    plot_img = ImageReader(str(FALLBACK_IMG))

TARGET_W = WIDTH - 120
TARGET_H = HEIGHT - 200

orig_w, orig_h = plot_img.getSize()
orig_ratio   = orig_w / orig_h
target_ratio = TARGET_W / TARGET_H

if orig_ratio > target_ratio:
    final_w = TARGET_W
    final_h = TARGET_W / orig_ratio
else:
    final_h = TARGET_H
    final_w = TARGET_H * orig_ratio

x = (WIDTH - final_w) / 2
y = (HEIGHT - final_h) / 2

# ⭐ FIXED: draw loaded image, not filename
c.drawImage(plot_img, x, y, width=final_w, height=final_h)

c.showPage()
page_no += 1



# ============================================================
#  SAVE REPORT
# ============================================================

c.save()
print(f"Generated: {OUTPUT}")
