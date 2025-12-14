import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

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

# ======================
# Load Item Data
# ======================
with open("items.json", "r", encoding="utf-8") as f:
    item = json.load(f)

# ======================
# Create Card Base
# ======================
card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
draw = ImageDraw.Draw(card)

# ======================
# Load Fonts
# ======================
title_font = ImageFont.truetype(
    "fonts/UncialAntiqua-Regular.ttf", 48
)
subtitle_font = ImageFont.truetype(
    "fonts/LibreBaskerville-Regular.ttf", 26
)
body_font = ImageFont.truetype(
    "fonts/LibreBaskerville-Regular.ttf", 28
)
flavor_font = ImageFont.truetype(
    "fonts/LibreBaskerville-Regular.ttf", 24
)

# ======================
# Draw Title
# ======================
draw.text(
    (CARD_WIDTH // 2, MARGIN),
    item["name"],
    fill=TEXT_COLOR,
    font=title_font,
    anchor="mm"
)

# ======================
# Draw Subtitle
# ======================
subtitle = f'{item["type"]} • {item["rarity"]}'
draw.text(
    (CARD_WIDTH // 2, MARGIN + 60),
    subtitle,
    fill=TEXT_COLOR,
    font=subtitle_font,
    anchor="mm"
)

# ======================
# Load and Place Art
# ======================
art = Image.open(f"item_images/{item['image']}").convert("RGBA")

art_ratio = art.width / art.height
target_width = CARD_WIDTH - (MARGIN * 2)
target_height = ART_HEIGHT

if art_ratio > target_width / target_height:
    # Image is wide
    new_width = target_width
    new_height = int(target_width / art_ratio)
else:
    # Image is tall
    new_height = target_height
    new_width = int(target_height * art_ratio)

art = art.resize((new_width, new_height))

art_x = (CARD_WIDTH - new_width) // 2
art_y = MARGIN + 100

card.paste(art, (art_x, art_y), art)

# ======================
# Draw Description Text
# ======================
text_start_y = art_y + ART_HEIGHT + 30
text_box_width = CARD_WIDTH - (MARGIN * 2)

wrapped_description = textwrap.fill(
    item["description"], width=45
)

draw.multiline_text(
    (MARGIN, text_start_y),
    wrapped_description,
    fill=TEXT_COLOR,
    font=body_font,
    spacing=6
)

# ======================
# Draw Flavor Text
# ======================
flavor_text = f'— {item["flavor"]}'
wrapped_flavor = textwrap.fill(flavor_text, width=50)

draw.multiline_text(
    (MARGIN, CARD_HEIGHT - 150),
    wrapped_flavor,
    fill=(90, 70, 60, 255),
    font=flavor_font,
    spacing=4
)

# ======================
# Optional Border (because fancy)
# ======================
border_color = (120, 90, 60, 255)
border_width = 4

for i in range(border_width):
    draw.rectangle(
        [i, i, CARD_WIDTH - i - 1, CARD_HEIGHT - i - 1],
        outline=border_color
    )

# ======================
# Save Output
# ======================
output_name = item["name"].replace(" ", "_").lower() + ".png"
card.save(f"output/{output_name}", dpi=(DPI, DPI))

print(f"Generated card: {output_name}")
