import re
import textwrap
from PIL import Image

# ======================
# Inline Markup Pattern
# ======================
# This regex splits a string into tokens for:
# - Bold: **bold text**
# - Italic: *italic text*
# - Colored text: {color}text{/}
# - - bullet
# - Icons: {icon:icon_name}
# - \n for new lines
# - \n\n for paragraph breaks
# Example: "This is **bold** and *italic* text with {red}red text{/} and an {icon:fire} icon."
INLINE_PATTERN = re.compile(
    r"(\*\*.*?\*\*|\*.*?\*|\{.*?\}.*?\{\/\}|\{icon:.*?\})"
)

COLOR_MAP = {
    "red": (150, 30, 30, 255),
    "blue": (40, 60, 160, 255),
    "green": (40, 120, 60, 255),
    "gold": (160, 120, 40, 255),
    "default": (40, 30, 20, 255)
}

ICON_MAP = {
    "fire": "icons/fire.png",
    "lightning": "icons/lightning.png",
    "frost": "icons/frost.png",
    "melee": "icons/melee.png",
    "shield": "icons/shield.png",
    "heart": "icons/heart.png",
    "rooted": "icons/rooted.png",
    "poison": "icons/poison.png",
    "magic": "icons/magic.png",
    "armorbroken": "icons/armorbroken.png",
    "ignited": "icons/ignited.png",
    "dragon": "icons/dragon.png",
    "blood": "icons/blood.png",
    "eye": "icons/eye.png"
}

 #======================
# Fix to keep token effect when wrapping
# ======================
def wrap_tokens(tokens, draw, fonts, max_width, icon_size, space_width):
    lines = []
    current_line = []
    current_width = 0

    for token in tokens:
        if token[0] == "icon":
            token_width = icon_size + 4
            token_text = None
        else:
            content, style = token[1], token[2]
            font = fonts["normal"]
            if style["bold"] and style["italic"]:
                font = fonts.get("bolditalic", fonts["bold"])
            elif style["bold"]:
                font = fonts["bold"]
            elif style["italic"]:
                font = fonts["italic"]

            token_width = draw.textlength(content, font=font)
            token_text = content

        if current_width + token_width > max_width and current_line:
            lines.append(current_line)
            current_line = []
            current_width = 0

        current_line.append(token)
        current_width += token_width

    if current_line:
        lines.append(current_line)

    return lines

def explode_text_tokens(tokens):
    # Splits text tokens into word-level tokens while preserving style.
    exploded = []

    for token in tokens:
        if token[0] == "icon":
            exploded.append(token)
            continue

        content, style = token[1], token[2]

        # split but keep spaces
        parts = re.split(r"(\s+)", content)

        for part in parts:
            if part:
                exploded.append(("text", part, style))

    return exploded

# ======================
# Draw outlines text - for color
# ======================
def draw_text_with_outline(draw, position, text, font, fill, outline=(0, 0, 0, 255), outline_width=1):
    x, y = position

    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline)

    # Draw main text
    draw.text((x, y), text, font=font, fill=fill)

# ======================
# Helper for centering text
# ======================
def measure_token_line(tokens, draw, fonts, icon_size):
    width = 0

    for token in tokens:
        if token[0] == "icon":
            width += icon_size + 4
            continue

        content, style = token[1], token[2]

        font = fonts["normal"]
        if style["bold"] and style["italic"]:
            font = fonts.get("bolditalic", fonts["bold"])
        elif style["bold"]:
            font = fonts["bold"]
        elif style["italic"]:
            font = fonts["italic"]

        width += draw.textlength(content, font=font)

    return width



# ======================
# Parse Inline Markup
# ======================
def parse_inline(text):
    tokens = []
    i = 0
    stack = []

    def current_style():
        style = {"bold": False, "italic": False, "color": None}
        for s in stack:
            if s == "bold":
                style["bold"] = True
            elif s == "italic":
                style["italic"] = True
            elif s.startswith("color:"):
                style["color"] = s.split(":", 1)[1]
        return style

    buffer = ""

    while i < len(text):
        # ---- Bold ----
        if text.startswith("**", i):
            if buffer:
                tokens.append(("text", buffer, current_style()))
                buffer = ""
            if stack and stack[-1] == "bold":
                stack.pop()
            else:
                stack.append("bold")
            i += 2
            continue

        # ---- Italic ----
        if text.startswith("*", i):
            if buffer:
                tokens.append(("text", buffer, current_style()))
                buffer = ""
            if stack and stack[-1] == "italic":
                stack.pop()
            else:
                stack.append("italic")
            i += 1
            continue

        # ---- Color open ----
        if text.startswith("{", i) and "}" in text[i:]:
            end = text.find("}", i)
            tag = text[i+1:end]

            if tag == "/":
                if stack and stack[-1].startswith("color:"):
                    if buffer:
                        tokens.append(("text", buffer, current_style()))
                        buffer = ""
                    stack.pop()
                i = end + 1
                continue

            if tag.startswith("icon:"):
                if buffer:
                    tokens.append(("text", buffer, current_style()))
                    buffer = ""
                tokens.append(("icon", tag.split(":", 1)[1]))
                i = end + 1
                continue

            # color start
            if buffer:
                tokens.append(("text", buffer, current_style()))
                buffer = ""
            stack.append(f"color:{tag}")
            i = end + 1
            continue

        # ---- Normal char ----
        buffer += text[i]
        i += 1

    if buffer:
        tokens.append(("text", buffer, current_style()))

    return tokens

# ======================
# Render Markup
# ======================
def render_markup(
    text,
    image,
    draw,
    x,
    y,
    max_width,
    fonts,
    default_color,
    icon_size=28,
    line_spacing=6,
    wrap_width=45,
    measure_only=False,
    align="left"
):

    cursor_y = y
    paragraphs = text.split("\n\n")  # split paragraphs on double newline

    for para in paragraphs:
        lines = para.split("\n")  # split lines within paragraph
        for line in lines:
            is_bullet = line.startswith("- ")
            line = line[2:] if is_bullet else line

            tokens = explode_text_tokens(parse_inline(line))

            wrapped_lines = wrap_tokens(
                tokens,
                draw,
                fonts,
                max_width - (22 if is_bullet else 0),
                icon_size,
                draw.textlength(" ", font=fonts["normal"])
            )

            for wrapped_tokens in wrapped_lines:
                line_width = measure_token_line(
                    wrapped_tokens,
                    draw,
                    fonts,
                    icon_size
                )

                if align == "center":
                    cursor_x = x + (max_width - line_width) // 2
                else:
                    cursor_x = x + (22 if is_bullet else 0)


                if is_bullet:
                    draw.text((x, cursor_y), "•", fill=default_color, font=fonts["normal"])

                for token in wrapped_tokens:
                    if token[0] == "icon":
                        if not measure_only:
                            icon_path = ICON_MAP.get(token[1])
                            if icon_path:
                                icon_img = Image.open(icon_path).convert("RGBA")
                                icon_img = icon_img.resize((icon_size, icon_size))
                                image.paste(icon_img, (int(cursor_x), int(cursor_y)), icon_img)
                        cursor_x += icon_size + 4
                        continue

                    # text token
                    content, style = token[1], token[2]

                    font = fonts["normal"]
                    if style["bold"] and style["italic"]:
                        font = fonts.get("bolditalic", fonts["bold"])
                    elif style["bold"]:
                        font = fonts["bold"]
                    elif style["italic"]:
                        font = fonts["italic"]

                    color = COLOR_MAP.get(style["color"], default_color)

                    if style["color"] is not None:
                        draw_text_with_outline(
                            draw,
                            (cursor_x, cursor_y),
                            content,
                            font,
                            fill=color,
                            outline=(0, 0, 0, 255),
                            outline_width= max(1, font.size // 18)
                        )
                    else:
                        draw.text((cursor_x, cursor_y), content, fill=color, font=font)

                    cursor_x += draw.textlength(content, font=font)



                cursor_y += fonts["normal"].size + line_spacing

        cursor_y += fonts["normal"].size  # paragraph spacing

    return cursor_y
