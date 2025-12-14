import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from markup import render_markup, COLOR_MAP
import copy

# ======================
# Card Constants
# ======================
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
# Card Generator
# ======================
def generate_card(item):
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(card)

    # ---- Title ----
    render_markup(
        item["name"],
        card,
        draw,
        MARGIN,
        MARGIN,
        CARD_WIDTH - (MARGIN * 2),
        {"normal": title_font, "bold": title_font, "italic": title_font},
        TEXT_COLOR
    )

    # ---- Subtitle ----
    render_markup(
        f'{item["type"]} • {item["rarity"]}',
        card,
        draw,
        MARGIN,
        MARGIN + 70,
        CARD_WIDTH - (MARGIN * 2),
        {"normal": subtitle_font, "bold": subtitle_font, "italic": subtitle_font},
        TEXT_COLOR
    )

    # ---- Artwork ----
    art_path = Path("item_images") / item["image"]
    art = Image.open(art_path).convert("RGBA")

    art_ratio = art.width / art.height
    target_width = CARD_WIDTH - (MARGIN * 2)
    target_height = ART_HEIGHT

    if art_ratio > target_width / target_height:
        new_width = target_width
        new_height = int(target_width / art_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * art_ratio)

    art = art.resize((new_width, new_height))
    art_x = (CARD_WIDTH - new_width) // 2
    art_y = MARGIN + 120
    card.paste(art, (art_x, art_y), art)

    # ---- Description with auto-scaling ----
    text_start_y = art_y + ART_HEIGHT + 30
    max_text_height = CARD_HEIGHT - text_start_y - 180  # leave space for flavor & margins
    render_markup_autoscale(
        item["description"],
        card,
        draw,
        MARGIN,
        text_start_y,
        CARD_WIDTH - (MARGIN * 2),
        fonts_dict,
        TEXT_COLOR,
        max_text_height,
    )

    # ---- Flavor text ----
    if "flavor" in item:
        flavor_y = CARD_HEIGHT - 150
        max_flavor_height = 120  # adjust as needed
        render_markup_autoscale(
            f'— {item["flavor"]}',
            card,
            draw,
            MARGIN,
            flavor_y,
            CARD_WIDTH - (MARGIN * 2),
            fonts_dict,
            TEXT_COLOR,
            max_flavor_height
        )

    # ---- Border ----
    border_color = (120, 90, 60, 255)
    border_width = 4
    for i in range(border_width):
        draw.rectangle(
            [i, i, CARD_WIDTH - i - 1, CARD_HEIGHT - i - 1],
            outline=border_color
        )

    # ---- Save ----
    filename = item["name"].lower().replace(" ", "_") + ".png"
    output_path = OUTPUT_DIR / filename
    card.save(output_path, dpi=(DPI, DPI))
    print(f"Generated: {output_path}")


# ======================
# Load JSON and Generate
# ======================
with open("items.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data["items"]:
    generate_card(item)
