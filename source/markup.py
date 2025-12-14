import re
import textwrap

#  **bold**
#  *italic*
#  {color}colored text{/}
#   - bullet points


# ======================
# Inline Markup Pattern
# ======================
INLINE_PATTERN = re.compile(
    r"(\*\*.*?\*\*|\*.*?\*|\{.*?\}.*?\{\/\})"
)

# ======================
# Color Definitions
# ======================
COLOR_MAP = {
    "red": (150, 30, 30, 255),
    "blue": (40, 60, 160, 255),
    "green": (40, 120, 60, 255),
    "gold": (160, 120, 40, 255),
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
        elif part.startswith("{"):
            color = part[1:part.index("}")]
            content = part[part.index("}") + 1:-3]
            tokens.append(("color", content, color))
        else:
            tokens.append(("normal", part))

    return tokens


# ======================
# Render Markup Block
# ======================
def render_markup(
    text,
    draw,
    x,
    y,
    max_width,
    fonts,
    default_color,
    line_spacing=6,
    wrap_width=45
):
    cursor_y = y

    paragraphs = text.split("\n\n")

    for para in paragraphs:
        lines = para.split("\n")

        for line in lines:
            is_bullet = line.startswith("- ")
            line = line[2:] if is_bullet else line

            wrapped_lines = textwrap.wrap(line, width=wrap_width)

            for wrapped in wrapped_lines:
                cursor_x = x + (22 if is_bullet else 0)

                if is_bullet:
                    draw.text(
                        (x, cursor_y),
                        "•",
                        fill=default_color,
                        font=fonts["normal"]
                    )

                tokens = parse_inline(wrapped)

                for token in tokens:
                    kind = token[0]

                    if kind == "bold":
                        font = fonts["bold"]
                        color = default_color
                        content = token[1]
                    elif kind == "italic":
                        font = fonts["italic"]
                        color = default_color
                        content = token[1]
                    elif kind == "color":
                        font = fonts["normal"]
                        content = token[1]
                        color = COLOR_MAP.get(token[2], default_color)
                    else:
                        font = fonts["normal"]
                        color = default_color
                        content = token[1]

                    draw.text(
                        (cursor_x, cursor_y),
                        content,
                        fill=color,
                        font=font
                    )
                    cursor_x += draw.textlength(content, font=font)

                cursor_y += fonts["normal"].size + line_spacing

        cursor_y += fonts["normal"].size  # paragraph spacing

    return cursor_y
