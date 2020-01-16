from enum import auto, Enum

class Event:
    def __init__(self):
        pass

class MouseEventType(Enum):
    MOVE = 0
    PRESS = 1
    LONG_PRESS = 2
    RELEASE = 3
    DOUBLE_CLICK = 4
    # SCROLL

class MouseButton(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4

class MouseEvent(Event):
    def __init__(self, event_type, button, x, y):
        super().__init__()
        self.event_type = event_type
        self.button = button
        self.x = x
        self.y = y

class MouseEnterEvent(Event):
    pass

class MouseLeaveEvent(Event):
    pass

class KeyEventType(Enum):
    PRESS = 0
    RELEASE = 1

# Copied from pygame
class KeyCode(Enum):
    BACKSPACE = auto()
    TAB = auto()
    CLEAR = auto()
    RETURN = auto()
    PAUSE = auto()
    ESCAPE = auto()
    SPACE = auto()
    EXCLAIM = auto()
    QUOTEDBL = auto()
    HASH = auto()
    DOLLAR = auto()
    AMPERSAND = auto()
    QUOTE = auto()
    LEFTPAREN = auto()
    RIGHTPAREN = auto()
    ASTERISK = auto()
    PLUS = auto()
    COMMA = auto()
    MINUS = auto()
    PERIOD = auto()
    SLASH = auto()
    NUM_0 = auto()
    NUM_1 = auto()
    NUM_2 = auto()
    NUM_3 = auto()
    NUM_4 = auto()
    NUM_5 = auto()
    NUM_6 = auto()
    NUM_7 = auto()
    NUM_8 = auto()
    NUM_9 = auto()
    COLON = auto()
    SEMICOLON = auto()
    LESS = auto()
    EQUALS = auto()
    GREATER = auto()
    QUESTION = auto()
    AT = auto()
    LEFTBRACKET = auto()
    BACKSLASH = auto()
    RIGHTBRACKET = auto()
    CARET = auto()
    UNDERSCORE = auto()
    BACKQUOTE = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()
    DELETE = auto()
    KP0 = auto()
    KP1 = auto()
    KP2 = auto()
    KP3 = auto()
    KP4 = auto()
    KP5 = auto()
    KP6 = auto()
    KP7 = auto()
    KP8 = auto()
    KP9 = auto()
    KP_PERIOD = auto()
    KP_DIVIDE = auto()
    KP_MULTIPLY = auto()
    KP_MINUS = auto()
    KP_PLUS = auto()
    KP_ENTER = auto()
    KP_EQUALS = auto()
    UP = auto()
    DOWN = auto()
    RIGHT = auto()
    LEFT = auto()
    INSERT = auto()
    HOME = auto()
    END = auto()
    PAGEUP = auto()
    PAGEDOWN = auto()
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()
    F13 = auto()
    F14 = auto()
    F15 = auto()
    NUMLOCK = auto()
    CAPSLOCK = auto()
    SCROLLOCK = auto()
    RSHIFT = auto()
    LSHIFT = auto()
    RCTRL = auto()
    LCTRL = auto()
    RALT = auto()
    LALT = auto()
    RMETA = auto()
    LMETA = auto()
    LSUPER = auto()
    RSUPER = auto()
    MODE = auto()
    HELP = auto()
    PRINT = auto()
    SYSREQ = auto()
    BREAK = auto()
    MENU = auto()
    POWER = auto()
    EURO = auto()

class KeyEvent(Event):
    def __init__(self, event_type, key_code, char_code):
        super().__init__()
        self.event_type = event_type
        self.key_code = key_code
        self.char_code = char_code

class FocusLostEvent(Event):
    pass