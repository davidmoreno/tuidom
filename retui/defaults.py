COLORS = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "grey": "#777777",
    "bg": "#590696",
    "bg-primary": "#590696",
    "bg-secondary": "#FBCB0A",
    "bg-tertiary": "#C70A80",
    "bg-quaternary": "#37E2D5",

    "fg": "#FAFAFA",
    "text-primary": "#ffffff",
    "text-secondary": "#000000",
    "text-tertiary": "#ffffff",
    "text-quaternary": "#ffffff",
}

DEFAULT_CSS = {
    "document": {
        "background": "bg",
        "color": "fg",
        "flex-direction": "column",
    },
    "div": {
        "flex-direction": "column",
    },
    "span": {
        "flex-direction": "row",
    },

    "App": {
        "flex-direction": "column",
    },
    "header": {
        "flex-direction": "row",
        "color": "text-secondary",
        "background": "bg-secondary",
        "width": "100%",
    },
    "body": {
        "flex-direction": "column",
        "color": "text-primary",
        "background": "bg-primary",
        "flex-grow": 1,
    },
    "footer": {
        "flex-direction": "row",
        "color": "text-secondary",
        "background": "bg-secondary",
    },
    "select:focus": {
        "background": "text-secondary",
        "color": "bg-secondary",
    },
    ".bold": {
        "font-weight": "bold",
    },
    ".italic": {
        "font-style": "italic",
    },
    ".underline": {
        "font-decoration": "underline",
    },
}


XTERM_KEYCODES = {
    b"\x1bOP": "F1",
    b"\x1bOQ": "F2",
    b"\x1bOR": "F3",
    b"\x1bOS": "F4",
    b"\x1b[15~": "F5",
    b"\x1b[17~": "F6",
    b"\x1b[18~": "F7",
    b"\x1b[19~": "F8",
    b"\x1b[20~": "F9",
    b"\x1b[21~": "F10",
    b"\x1b[22~": "F11",
    b"\x1b[24~": "F12",
    b"\x7f": "DEL",
    b"\t": "TAB",
    b'\x1b[Z': "RTAB",
    b"\n": "ENTER",
    b"\x01": "CONTROL-A",
    b"\x02": "CONTROL-B",
    b"\x03": "CONTROL-C",
    b"\x04": "CONTROL-D",
    b"\x05": "CONTROL-E",
    b"\x06": "CONTROL-F",
    b"\x07": "CONTROL-G",
    b"\x08": "CONTROL-H",
    # b"\x09": "CONTROL-I",
    # b"\x0a": "CONTROL-J",
    b"\x0b": "CONTROL-K",
    b"\x0c": "CONTROL-L",
    b"\x0d": "CONTROL-M",
    b"\x0e": "CONTROL-N",
    b"\x0f": "CONTROL-O",
    b"\x10": "CONTROL-P",
    b"\x11": "CONTROL-Q",
    b"\x12": "CONTROL-R",
    b"\x13": "CONTROL-S",
    b"\x14": "CONTROL-T",
    b"\x15": "CONTROL-U",
    b"\x16": "CONTROL-V",
    b"\x17": "CONTROL-W",
    b"\x18": "CONTROL-X",
    b"\x19": "CONTROL-Y",
    b"\x1a": "CONTROL-Z",
    b"\x1b": "ESC",
}

BREAKPOINT_KEYPRESS = "F12"
