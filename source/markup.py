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

# ======================
# Parse Inline Markup
# ======================
def parse_inline(text):
    parts = INLINE_PATTERN.split(text)
    tokens = []

    for part in parts:
        if not part:
            continue
        if part.startswith("**"):
            tokens.append(("bold", part[2:-2]))
        elif part.startswith("*"):
            tokens.append(("italic", part[1:-1]))
        elif part.startswith("{icon:"):
            icon_name = part[6:-1]  # remove {icon: ... }
            tokens.append(("icon", icon_name))
        elif part.startswith("{"):
            color = part[1:part.index("}")]
            content = part[part.index("}") + 1:-3]  # remove {/}
            tokens.append(("color", content, color))
        else:
            tokens.append(("normal", part))

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
    measure_only=False
):

    cursor_y = y
    paragraphs = text.split("\n\n")  # split paragraphs on double newline

    for para in paragraphs:
        lines = para.split("\n")  # split lines within paragraph
        for line in lines:
            is_bullet = line.startswith("- ")
            line = line[2:] if is_bullet else line

            wrapped_lines = textwrap.wrap(line, width=wrap_width)

            for wrapped in wrapped_lines:
                cursor_x = x + (22 if is_bullet else 0)
                if is_bullet:
                    draw.text((x, cursor_y), "•", fill=default_color, font=fonts["normal"])

                tokens = parse_inline(wrapped)
                for token in tokens:
                    kind = token[0]

                    if kind == "bold":
                        font = fonts["bold"]
                        color = default_color
                        content = token[1]
                        draw.text((cursor_x, cursor_y), content, fill=color, font=font)
                        cursor_x += draw.textlength(content, font=font)
                    elif kind == "italic":
                        font = fonts["italic"]
                        color = default_color
                        content = token[1]
                        draw.text((cursor_x, cursor_y), content, fill=color, font=font)
                        cursor_x += draw.textlength(content, font=font)
                    elif kind == "color":
                        font = fonts["normal"]
                        content = token[1]
                        color = COLOR_MAP.get(token[2], default_color)
                        draw.text((cursor_x, cursor_y), content, fill=color, font=font)
                        cursor_x += draw.textlength(content, font=font)
                    elif kind == "icon":
                        if not measure_only:
                            icon_path = ICON_MAP.get(token[1])
                            if icon_path:
                                icon_img = Image.open(icon_path).convert("RGBA")
                                icon_img = icon_img.resize((icon_size, icon_size))

                                image.paste(
                                    icon_img,
                                    (int(cursor_x), int(cursor_y)),
                                    icon_img
                                )

                        cursor_x += icon_size + 4 # space after icon
                    else:  # normal text
                        font = fonts["normal"]
                        content = token[1]
                        draw.text((cursor_x, cursor_y), content, fill=default_color, font=font)
                        cursor_x += draw.textlength(content, font=font)

                cursor_y += fonts["normal"].size + line_spacing

        cursor_y += fonts["normal"].size  # paragraph spacing

    return cursor_y
