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
    "body": {
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
    "MenuBar": {
        "flex-direction": "row",
        "color": "text-secondary",
        "background": "bg-secondary",
    },
    "Body": {
        "flex-direction": "column",
        "color": "text-primary",
        "background": "bg-primary",
        "flex-grow": 1,
    },
    "Footer": {
        "flex-direction": "row",
        "color": "text-secondary",
        "background": "bg-secondary",
    }
}
