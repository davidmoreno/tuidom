COLORS = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "yellow": "#FBCB0A",
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
    "select": {
        "cursor": "none",
    },
    "select:focus": {
        "background": "text-secondary",
        "color": "bg-secondary",
    },
    "option": {
        "background": "bg-secondary",
        "color": "text-secondary",
        "padding": "0 1",
        "cursor": "none",
    },
    "option:focus": {
        "background": "text-secondary",
        "color": "bg-secondary",
    },
    "button": {
        "cursor": "none",
        "background": "bg-secondary",
        "color": "text-secondary",
    },
    "button:focus": {
        "background": "text-secondary",
        "color": "bg-secondary",
    },
    "input": {
        "background": "text-secondary",
        "color": "bg-secondary",
    },
    "input:focus": {
        "background": "bg-secondary",
        "color": "text-secondary",
    },
    "textarea": {
        "background": "text-secondary",
        "color": "bg-secondary",
        # "overflowY": "scroll",
        # "overflowX": "scroll",
    },
    "textarea:focus": {
        "background": "bg-secondary",
        "color": "text-secondary",
    },
    "dialog": {
        "zIndex": 3,
        "position": "absolute",
        "background": "bg-tertiary",
        "color": "text-tertiary",
        "padding": "1 2 0 2",
        "border": 1,
        "borderColor": "text-primary",
        "left": 10,
        "top": 10,
        "width": 50,
        "height": 20,
    },
    ".absolute": {
        "position": "absolute",
    },
    ".z-0": {
        "zIndex": 0,
    },
    ".z-1": {
        "zIndex": 1,
    },
    ".z-10": {
        "zIndex": 2,
    },
    ".z-100": {
        "zIndex": 3,
    },
    ".w-full": {
        "width": "100%",
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
    ".flex-0": {
        "flex-grow": 0,
    },
    ".flex-1": {
        "flex-grow": 1,
    },
    ".flex-2": {
        "flex-grow": 2,
    },
    ".cursor-hidden": {
        "cursor": "hidden",
    },
    ".scroll-y": {
        "overflowY": "scroll",
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
    b"\x1b[Z": "RTAB",
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
    b"\x1b[H": "START",
    b"\x1b[F": "END",
    b"\x1b[5~": "PAGE UP",
    b"\x1b[6~": "PAGE DOWN",
    b"\x1b[A": "UP",
    b"\x1b[B": "DOWN",
    b"\x1b[C": "RIGHT",
    b"\x1b[D": "LEFT",
    b"\x1b[3~": "SUPR",
    b"\x1b[1;5C": "CONTROL-RIGHT",
    b"\x1b[1;5D": "CONTROL-LEFT",
}

BREAKPOINT_KEYPRESS = "F12"
