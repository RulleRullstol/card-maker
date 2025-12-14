import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from markup import render_markup

# ======================
# Card Constants
# ======================
CARD_WIDTH = 750
CARD_HEIGHT = 1050
DPI = 300

MARGIN = 50
ART_HEIGHT = 400

BACKGROUND_COLOR = (245, 240, 225, 255)
TEXT_COLOR = (40, 30, 20, 255)

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
# Card Generator
# ======================
def generate_card(item):
    # Base card
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(card)

    # ---- Title ----
    draw.text(
        (CARD_WIDTH // 2, MARGIN),
        item["name"],
        fill=TEXT_COLOR,
        font=title_font,
        anchor="mm"
    )

    # ---- Subtitle ----
    subtitle = f'{item["type"]} • {item["rarity"]}'
    draw.text(
        (CARD_WIDTH // 2, MARGIN + 60),
        subtitle,
        fill=TEXT_COLOR,
        font=subtitle_font,
        anchor="mm"
    )

    # ---- Artwork ----
    art_path = Path("item_images") / item["image"]
    art = Image.open(art_path).convert("RGBA")

    # Resize proportionally
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
    art_y = MARGIN + 100
    card.paste(art, (art_x, art_y), art)

    # ---- Description ----
    text_start_y = art_y + ART_HEIGHT + 30
    render_markup(
        item["description"],
        draw,
        MARGIN,
        text_start_y,
        CARD_WIDTH - (MARGIN * 2),
        fonts_dict,
        TEXT_COLOR
    )

    # ---- Flavor text ----
    wrapped_flavor = item.get("flavor", "")
    if wrapped_flavor:
        from markup import COLOR_MAP
        render_markup(
            f'— {wrapped_flavor}',
            draw,
            MARGIN,
            CARD_HEIGHT - 150,
            CARD_WIDTH - (MARGIN * 2),
            fonts_dict,
            color := COLOR_MAP.get("default", TEXT_COLOR)
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
