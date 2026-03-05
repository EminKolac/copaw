"""Generate a PNG mockup of the NBIM Investment Dashboard for Power BI."""
from PIL import Image, ImageDraw, ImageFont
import csv
import os

W, H = 1920, 1080
BG = (13, 17, 23)
CARD_BG = (22, 27, 34)
BORDER = (48, 54, 61)
TEXT_PRIMARY = (230, 237, 243)
TEXT_SECONDARY = (139, 148, 158)
ACCENT = (0, 102, 204)
BLUE_DARK = (0, 51, 102)
BLUE_MID = (51, 153, 255)
BLUE_LIGHT = (179, 217, 255)
GREEN = (46, 160, 67)
WHITE = (255, 255, 255)

# Treemap color gradient based on share
def share_color(share, max_share):
    t = min(share / max_share, 1.0)
    r = int(BLUE_LIGHT[0] + (BLUE_DARK[0] - BLUE_LIGHT[0]) * t)
    g = int(BLUE_LIGHT[1] + (BLUE_DARK[1] - BLUE_LIGHT[1]) * t)
    b = int(BLUE_LIGHT[2] + (BLUE_DARK[2] - BLUE_LIGHT[2]) * t)
    return (r, g, b)

def draw_rounded_rect(draw, xy, fill, radius=8):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def get_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

def get_bold_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        return get_font(size)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

font_sm = get_font(11)
font_md = get_font(14)
font_lg = get_font(18)
font_xl = get_font(28)
font_title = get_bold_font(22)
font_kpi = get_bold_font(36)
font_label = get_font(12)
font_tree = get_font(10)
font_tree_lg = get_bold_font(13)

# === HEADER ===
draw_rounded_rect(draw, (20, 15, W-20, 65), CARD_BG)
draw.text((40, 25), "ALL INVESTMENTS", fill=WHITE, font=font_title)
draw.text((340, 30), "|  Norges Bank Investment Management", fill=TEXT_SECONDARY, font=font_md)

# Year pills
years = ["2022", "2023", "2024", "2025"]
x_start = 900
for i, yr in enumerate(years):
    x = x_start + i * 80
    color = ACCENT if yr == "2025" else BORDER
    draw_rounded_rect(draw, (x, 25, x+65, 55), color, radius=12)
    draw.text((x+15, 31), yr, fill=WHITE, font=font_md)

# Asset class pills
assets = ["All", "Equities", "Fixed Income", "Real Estate", "Infrastructure"]
x_start = 1280
for i, a in enumerate(assets):
    x = x_start + i * 120
    color = ACCENT if a == "All" else BORDER
    draw_rounded_rect(draw, (x, 25, x+110, 55), color, radius=12)
    tw = draw.textlength(a, font=font_sm)
    draw.text((x + (110-tw)//2, 33), a, fill=WHITE, font=font_sm)

# === KPI CARDS ===
kpis = [
    ("Total Fund Value", "19,744 bn", "NOK"),
    ("Companies", "7,200+", "Worldwide"),
    ("Annual Return", "6.6%", "Since 1998"),
    ("Countries", "70+", "Invested"),
]
card_w = (W - 100) // 4
for i, (label, value, sub) in enumerate(kpis):
    x = 20 + i * (card_w + 20)
    draw_rounded_rect(draw, (x, 80, x+card_w, 175), CARD_BG)
    draw.text((x+20, 93), label, fill=TEXT_SECONDARY, font=font_sm)
    draw.text((x+20, 115), value, fill=WHITE, font=font_kpi)
    draw.text((x+20, 155), sub, fill=GREEN if "6.6" in value else TEXT_SECONDARY, font=font_sm)

# === TREEMAP ===
# Load sample data
data_path = os.path.join(os.path.dirname(__file__), "sample_data", "nbim_holdings_2025.csv")
holdings = []
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        holdings.append({
            "name": row["CompanyName"],
            "value": float(row["ValueNOK_Billions"]),
            "share": float(row["ShareOfFund_Pct"]),
            "sector": row["Sector"],
            "country": row["Country"],
            "asset": row["AssetClass"],
        })

# Sort by value descending
holdings.sort(key=lambda x: x["value"], reverse=True)
equities = [h for h in holdings if h["asset"] == "Equities"]
max_share = max(h["share"] for h in equities)

# Simple squarified-ish treemap layout
treemap_x, treemap_y = 20, 190
treemap_w, treemap_h = 1300, 500
draw_rounded_rect(draw, (treemap_x, treemap_y, treemap_x+treemap_w, treemap_y+treemap_h), CARD_BG)

# Title
draw.text((treemap_x+15, treemap_y+8), "Investment Portfolio Treemap", fill=WHITE, font=font_lg)
draw.text((treemap_x+320, treemap_y+12), "Size = Investment Value  |  Color = Share of Fund", fill=TEXT_SECONDARY, font=font_sm)

# Draw treemap rectangles (simplified row-based layout)
margin = 3
tx, ty = treemap_x + 10, treemap_y + 38
tw, th = treemap_w - 20, treemap_h - 48
total_val = sum(h["value"] for h in equities[:20])

# Layout in rows
items = equities[:20]
row_items = []
rows = []

# Simple algorithm: fill rows proportionally
remaining = list(items)
cy = ty
remaining_h = th

while remaining and remaining_h > 20:
    # Take items that fill ~one row
    row_val = 0
    row = []
    target_val = total_val * (80 / th) if remaining_h > 80 else total_val

    # First row: top 5, second row: next 5, etc.
    n = min(5, len(remaining))
    if len(remaining) <= 5:
        n = len(remaining)
    row = remaining[:n]
    remaining = remaining[n:]

    row_val = sum(h["value"] for h in row)
    row_h = int(remaining_h * (row_val / sum(h["value"] for h in row + remaining)) if remaining else remaining_h)
    row_h = max(row_h, 40)
    row_h = min(row_h, remaining_h)

    # Draw items in this row
    cx = tx
    for h in row:
        item_w = max(int(tw * (h["value"] / row_val)), 30)
        if h == row[-1]:
            item_w = tx + tw - cx  # fill remaining

        color = share_color(h["share"], max_share)
        draw.rectangle((cx+margin, cy+margin, cx+item_w-margin, cy+row_h-margin), fill=color)

        # Draw text if box is large enough
        if item_w > 80 and row_h > 30:
            name = h["name"]
            if len(name) > 18 and item_w < 160:
                name = name[:16] + ".."
            draw.text((cx+margin+6, cy+margin+6), name, fill=WHITE, font=font_tree_lg)
            if row_h > 55:
                draw.text((cx+margin+6, cy+margin+24), f"{h['value']:.0f} bn NOK", fill=(200, 220, 240), font=font_tree)
                if row_h > 70:
                    draw.text((cx+margin+6, cy+margin+38), h["sector"], fill=(170, 190, 210), font=font_tree)
        elif item_w > 50:
            short = h["name"][:12]
            draw.text((cx+margin+4, cy+margin+4), short, fill=WHITE, font=font_tree)

        cx += item_w

    cy += row_h
    remaining_h -= row_h

# Color legend
legend_y = treemap_y + treemap_h - 25
draw.text((treemap_x + 15, legend_y), "Highest Share", fill=TEXT_SECONDARY, font=font_sm)
for i in range(100):
    t = i / 100
    r = int(BLUE_DARK[0] + (BLUE_LIGHT[0] - BLUE_DARK[0]) * t)
    g = int(BLUE_DARK[1] + (BLUE_LIGHT[1] - BLUE_DARK[1]) * t)
    b = int(BLUE_DARK[2] + (BLUE_LIGHT[2] - BLUE_DARK[2]) * t)
    draw.rectangle((treemap_x+130+i*2, legend_y+2, treemap_x+132+i*2, legend_y+14), fill=(r,g,b))
draw.text((treemap_x + 340, legend_y), "Lowest Share", fill=TEXT_SECONDARY, font=font_sm)

# === RIGHT SIDE PANEL: Slicers ===
panel_x = 1340
draw_rounded_rect(draw, (panel_x, 190, W-20, 440), CARD_BG)
draw.text((panel_x+15, 200), "Filters", fill=WHITE, font=font_lg)

# Country slicer
draw.text((panel_x+15, 235), "Country", fill=TEXT_SECONDARY, font=font_sm)
draw_rounded_rect(draw, (panel_x+15, 255, W-40, 285), BORDER, radius=5)
draw.text((panel_x+25, 261), "All Countries", fill=TEXT_PRIMARY, font=font_md)

# Sector slicer
draw.text((panel_x+15, 300), "Sector", fill=TEXT_SECONDARY, font=font_sm)
draw_rounded_rect(draw, (panel_x+15, 320, W-40, 350), BORDER, radius=5)
draw.text((panel_x+25, 326), "All Sectors", fill=TEXT_PRIMARY, font=font_md)

# Search
draw.text((panel_x+15, 365), "Search Company", fill=TEXT_SECONDARY, font=font_sm)
draw_rounded_rect(draw, (panel_x+15, 385, W-40, 415), BORDER, radius=5)
draw.text((panel_x+25, 391), "Type to search...", fill=TEXT_SECONDARY, font=font_md)

# === RIGHT: Sector Donut ===
draw_rounded_rect(draw, (panel_x, 455, W-20, 690), CARD_BG)
draw.text((panel_x+15, 465), "Sector Allocation", fill=WHITE, font=font_lg)

# Draw donut chart approximation
cx_d, cy_d, r_outer, r_inner = panel_x + 150, 590, 70, 40
import math
sectors_data = {}
for h in equities:
    s = h["sector"]
    sectors_data[s] = sectors_data.get(s, 0) + h["value"]

sector_colors = [
    (0, 102, 204), (51, 153, 255), (102, 178, 255), (0, 153, 102),
    (255, 179, 71), (204, 102, 0), (153, 51, 153)
]
sorted_sectors = sorted(sectors_data.items(), key=lambda x: x[1], reverse=True)
total_sector = sum(v for _, v in sorted_sectors)
angle = -90

for i, (sector_name, val) in enumerate(sorted_sectors):
    sweep = (val / total_sector) * 360
    color = sector_colors[i % len(sector_colors)]
    draw.pieslice((cx_d-r_outer, cy_d-r_outer, cx_d+r_outer, cy_d+r_outer), angle, angle+sweep, fill=color)
    angle += sweep

draw.ellipse((cx_d-r_inner, cy_d-r_inner, cx_d+r_inner, cy_d+r_inner), fill=CARD_BG)

# Sector legend
ly = 495
for i, (sector_name, val) in enumerate(sorted_sectors[:5]):
    color = sector_colors[i % len(sector_colors)]
    lx = panel_x + 260
    draw.rectangle((lx, ly, lx+10, ly+10), fill=color)
    pct = val/total_sector*100
    draw.text((lx+16, ly-2), f"{sector_name} ({pct:.0f}%)", fill=TEXT_SECONDARY, font=font_sm)
    ly += 20

# === BOTTOM LEFT: Top Holdings Table ===
table_x, table_y = 20, 705
table_w = 880
draw_rounded_rect(draw, (table_x, table_y, table_x+table_w, H-20), CARD_BG)
draw.text((table_x+15, table_y+8), "Top 15 Holdings", fill=WHITE, font=font_lg)

# Table header
cols = [("Rank", 50), ("Company", 280), ("Value (bn NOK)", 130), ("Sector", 180), ("Country", 200)]
hx = table_x + 15
hy = table_y + 38
draw.line((table_x+15, hy+18, table_x+table_w-15, hy+18), fill=BORDER, width=1)
for col_name, col_w in cols:
    draw.text((hx, hy), col_name, fill=TEXT_SECONDARY, font=font_sm)
    hx += col_w

# Table rows
for i, h in enumerate(equities[:12]):
    ry = hy + 22 + i * 22
    if ry > H - 40:
        break
    hx = table_x + 15
    row_data = [str(i+1), h["name"][:28], f"{h['value']:.0f}", h["sector"], h["country"]]
    for j, (col_name, col_w) in enumerate(cols):
        color = WHITE if j == 1 else TEXT_PRIMARY
        draw.text((hx, ry), row_data[j], fill=color, font=font_label)
        hx += col_w
    if i % 2 == 0:
        draw.rectangle((table_x+10, ry-2, table_x+table_w-10, ry+18), fill=(22, 27, 38))
        hx = table_x + 15
        for j, (col_name, col_w) in enumerate(cols):
            color = WHITE if j == 1 else TEXT_PRIMARY
            draw.text((hx, ry), row_data[j], fill=color, font=font_label)
            hx += col_w

# === BOTTOM RIGHT: Country Bar Chart ===
bar_x, bar_y = 920, 705
bar_w = W - 20 - bar_x
draw_rounded_rect(draw, (bar_x, bar_y, W-20, H-20), CARD_BG)
draw.text((bar_x+15, bar_y+8), "Investment by Country", fill=WHITE, font=font_lg)

# Aggregate by country
country_data = {}
for h in holdings:
    c = h["country"]
    country_data[c] = country_data.get(c, 0) + h["value"]

sorted_countries = sorted(country_data.items(), key=lambda x: x[1], reverse=True)[:8]
max_country_val = sorted_countries[0][1]

by = bar_y + 45
for country, val in sorted_countries:
    bar_len = int((val / max_country_val) * (bar_w - 180))
    draw.text((bar_x+15, by), country[:18], fill=TEXT_SECONDARY, font=font_label)
    draw.rectangle((bar_x+140, by+2, bar_x+140+bar_len, by+18), fill=ACCENT)
    draw.text((bar_x+145+bar_len, by+1), f"{val:.0f}", fill=TEXT_SECONDARY, font=font_label)
    by += 28

# === FOOTER ===
draw.text((20, H-15), "Data as at 31 December 2025  |  Source: Norges Bank Investment Management", fill=TEXT_SECONDARY, font=font_sm)

# Save
output_path = os.path.join(os.path.dirname(__file__), "nbim_dashboard_mockup.png")
img.save(output_path, "PNG", quality=95)
print(f"Dashboard mockup saved to: {output_path}")
print(f"Size: {W}x{H}")
