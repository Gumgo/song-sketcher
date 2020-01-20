def rgba(r, g, b, a = 1.0):
    return (r, g, b, a)

def rgba255(r, g, b, a = 255.0):
    return rgba(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

def darken_color(color, darkness):
    rgb = tuple(c * (1.0 - darkness) for c in color[:3])
    return tuple([rgb[0], rgb[1], rgb[2], color[3]])

def lighten_color(color, lightness):
    rgb = tuple(1.0 - (1.0 - c) * (1.0 - lightness) for c in color[:3])
    return tuple([rgb[0], rgb[1], rgb[2], color[3]])

def rgba_hex(color):
    r = (color >> 24) & 0xFF
    g = (color >> 16) & 0xFF
    b = (color >> 8) & 0xFF
    a = color & 0xFF
    return rgba255(r, g, b, a)

class Color:
    BLACK = rgba_hex(0x000000FF)
    WHITE = rgba_hex(0xFFFFFFFF)

class Ui:
    BUTTON_COLOR = rgba_hex(0xD4D4D4FF)
    INPUT_COLOR = rgba_hex(0xFFFFFFFF)
    DROPDOWN_COLOR = rgba_hex(0xE6E6E6FF)
    DROPDOWN_HIGHLIGHT_COLOR = rgba_hex(0x9999FFFF)
    SPINNER_INNER_COLOR = rgba_hex(0xE6E6E6FF)
    SPINNER_OUTER_COLOR = rgba_hex(0x808080FF)
    ACCEPT_BUTTON_COLOR = rgba_hex(0x40D440FF)
    REJECT_BUTTON_COLOR = rgba_hex(0xD44040FF)

    MENU_COLOR = rgba_hex(0x253B59FF)
    PANEL_COLOR = rgba_hex(0x1A5A73FF)
    DIALOG_COLOR = rgba_hex(0x248EA6FF)
    CATEGORY_COLOR = rgba_hex(0x24A6A6FF)
    TRACK_COLOR = rgba_hex(0x24A6A6FF)
    # 0x24A6A6FF
    # 0x96D9C6FF
