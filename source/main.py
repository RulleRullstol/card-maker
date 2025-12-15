import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from markup import render_markup, COLOR_MAP
import copy

# ======================
# Card Constants
# ======================


DEBUG_LAYOUT = True
GRID_WIDTH = 50
GRID_HEIGHT = 50
GRID_COLOR = (0, 255, 255, 120)  # cyan, semi-transparent
GRID_THICKNESS = 1


CARD_WIDTH = 750
CARD_HEIGHT = 1050
DPI = 300

MARGIN = 50
ART_HEIGHT = 400

BACKGROUND_COLOR = (245, 240, 225, 255)
TEXT_COLOR = COLOR_MAP["default"]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ======================
# Load Fonts
# ======================
title_font = ImageFont.truetype("fonts/UncialAntiqua-Regular.ttf", 48)
subtitle_font = ImageFont.truetype("fonts/LibreBaskerville-Regular.ttf", 26)
body_font = ImageFont.truetype("fonts/LibreBaskerville-Regular.ttf", 28)
flavor_font = ImageFont.truetype("fonts/LibreBaskerville-Regular.ttf", 24)
bold_font = ImageFont.truetype("fonts/LibreBaskerville-Bold.ttf", 28)
italic_font = ImageFont.truetype("fonts/LibreBaskerville-Italic.ttf", 28)

fonts_dict = {
    "normal": body_font,
    "bold": bold_font,
    "italic": italic_font
}

# ======================
# Helper: Auto Scale Font
# ======================
def render_markup_autoscale(
    text,
    card,
    draw,
    x,
    y,
    max_width,
    fonts,
    default_color,
    max_height,
    min_font_size=12,
    line_spacing=6,
):
    """Reduce font size until the text fits within max_height."""
    font_size = fonts["normal"].size
    temp_fonts = copy.deepcopy(fonts)

    while font_size >= min_font_size:
        for k, f in temp_fonts.items():
            temp_fonts[k] = ImageFont.truetype(f.path, font_size)

        # Create a dummy image to measure height
        dummy_img = Image.new("RGBA", (max_width, max_height))
        dummy_draw = ImageDraw.Draw(dummy_img)
        y_end = render_markup(text, dummy_img, dummy_draw, x, y, max_width, temp_fonts, default_color, line_spacing=line_spacing, measure_only=True)

        if y_end - y <= max_height:
            # Fits, break
            break

        font_size -= 1  # reduce size and retry

    # Now draw on real image
    render_markup(text, card, draw, x, y, max_width, temp_fonts, default_color, line_spacing=line_spacing)

# ======================
# Debug box layout
# ======================
def debug_draw_box(draw, box, color=(255, 255, 255, 255), label=None):
    if not DEBUG_LAYOUT:
        return

    # ---- Draw grid ONCE ----
    # We attach a flag to the draw object (safe in Python)
    if not hasattr(draw, "_grid_drawn"):
        img_w, img_h = draw.im.size

        # Vertical grid lines
        x = 0
        while x <= img_w:
            draw.line(
                [(x, 0), (x, img_h)],
                fill=GRID_COLOR,
                width=GRID_THICKNESS
            )
            x += GRID_WIDTH

        # Horizontal grid lines
        y = 0
        while y <= img_h:
            draw.line(
                [(0, y), (img_w, y)],
                fill=GRID_COLOR,
                width=GRID_THICKNESS
            )
            y += GRID_HEIGHT

        draw._grid_drawn = True  # mark as done

    # ---- Draw the box ----
    x, y = box["x"], box["y"]
    w, h = box["width"], box["height"]

    draw.rectangle(
        [x, y, x + w, y + h],
        outline=color,
        width=2
    )

    if label:
        draw.text(
            (x + 4, y + 4),
            label,
            fill=color
        )

# ======================
# render markup centered box
# ======================
def render_markup_centered_box(
    text,
    card,
    draw,
    box,
    fonts,
    color
):

    # --- Render to dummy to measure full bounding box ---
    dummy = Image.new("RGBA", (box["width"], box["height"]), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy)

    render_markup(
        text,
        dummy,
        dummy_draw,
        0,
        0,
        box["width"],
        fonts,
        color,
        measure_only=False
    )

    bbox = dummy.getbbox()
    if not bbox:
        return  # nothing to draw

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # --- Compute centered position ---
    start_x = box["x"] + (box["width"] - text_width) // 2
    start_y = box["y"] + (box["height"] - text_height) // 2

    # --- Render for real ---
    render_markup(
        text,
        card,
        draw,
        start_x,
        start_y,
        box["width"],
        fonts,
        color
    )


# ======================
# HSV recolor
# ======================
def recolor_frame_hsv(frame, hue, saturation):
    frame = frame.convert("RGBA")
    r, g, b, a = frame.split()

    hsv = Image.merge("RGB", (r, g, b)).convert("HSV")
    h, s, v = hsv.split()

    h = Image.new("L", h.size, hue)
    s = Image.new("L", s.size, saturation)

    recolored = Image.merge("HSV", (h, s, v)).convert("RGBA")
    recolored.putalpha(a)

    return recolored


# ======================
# Loading templates
# ======================

def load_template(name):
    base = Path("templates") / name

    with open(base / "layout.json", "r") as f:
        layout = json.load(f)

    images = {
        "base": Image.open(base / "base.png").convert("RGBA"),
        "frame": Image.open(base / "frame.png").convert("RGBA")
    }

    mask_path = base / layout["art"].get("mask", "")
    images["mask"] = (
        Image.open(mask_path).convert("L")
        if mask_path.exists()
        else None
    )

    return layout, images

# ======================
# Skapa kort
# ======================
def generate_card(item):
    template_name = item.get("template", "default")
    layout, assets = load_template(template_name)

    # ---- Frame recolor FIRST ----
    rarity = item.get("rarity", "Common")
    rarity_defs = layout.get("rarity_hsv", {})
    rarity_def = rarity_defs.get(rarity, rarity_defs.get("Common"))

    if rarity_def:
        frame = recolor_frame_hsv(
            assets["frame"],
            rarity_def.get("h", 0),
            rarity_def.get("s", 0)
        )
    else:
        frame = assets["frame"]

    # ---- Start card from recolored frame ----
    card = frame.copy()

    # ---- Composite base onto frame ----
    card.alpha_composite(assets["base"])

    # ---- Draw final ----
    draw = ImageDraw.Draw(card)

    # ---- Title ----
    debug_draw_box(draw, layout["title"], label="TITLE")
    render_markup_centered_box(
        item["name"],
        card,
        draw,
        layout["title"],
        {"normal": title_font, "bold": title_font, "italic": title_font},
        TEXT_COLOR
    )


    # ---- Subtitle ----
    debug_draw_box(draw, layout["subtitle"], label="SUBTITLE")
    render_markup_centered_box(
        f'{item["type"]} • {item["rarity"]}',
        card,
        draw,
        layout["subtitle"],
        {"normal": subtitle_font, "bold": subtitle_font, "italic": subtitle_font},
        TEXT_COLOR
    )

    # ---- Artwork ----
    art = Image.open(Path("item_images") / item["image"]).convert("RGBA")
    art = art.resize(
        (layout["art"]["width"], layout["art"]["height"])
    )

    if assets["mask"]:
        card.paste(
            art,
            (layout["art"]["x"], layout["art"]["y"]),
            assets["mask"]
        )
    else:
        card.paste(
            art,
            (layout["art"]["x"], layout["art"]["y"]),
            art
        )

    # ---- Description ----
    debug_draw_box(draw, layout["description"], label="DESCRIPTION")
    render_markup_autoscale(
        item["description"],
        card,
        draw,
        layout["description"]["x"],
        layout["description"]["y"],
        layout["description"]["width"],
        fonts_dict,
        TEXT_COLOR,
        layout["description"]["height"]
    )

    # ---- Flavor ----
    if "flavor" in item:
        debug_draw_box(draw, layout["flavor"], label="FLAVOR")
        render_markup_autoscale(
            f'— {item["flavor"]}',
            card,
            draw,
            layout["flavor"]["x"],
            layout["flavor"]["y"],
            layout["flavor"]["width"],
            fonts_dict,
            TEXT_COLOR,
            layout["flavor"]["height"]
        )

    # ---- Save ----
    filename = item["name"].lower().replace(" ", "_") + ".png"
    card.save(OUTPUT_DIR / filename, dpi=(DPI, DPI))
    print(f"Generated: {filename}")


# ======================
# Load JSON and Generate
# ======================
with open("items.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data["items"]:
    generate_card(item)
