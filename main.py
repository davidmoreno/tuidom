#!/bin/python3

import sys
from typing import Literal, Optional

from dataclasses import dataclass

from tuidom import Div, Element, Span, Style, XtermRenderer, Event, KeyPress


@dataclass
class WelcomeProps:
    menu: Optional[Literal["file", "edit", "tools", "exit"]] = None
    status: str = ""

    def handle_event(self, ev: Event):
        print(ev)
        match ev:
            case KeyPress('f'):
                self.menu = "file"
            case KeyPress('e'):
                self.menu = "edit"
            case KeyPress('t'):
                self.menu = "tools"
            case KeyPress('x'):
                sys.exit()
            case _:
                self.menu = None
        self.status = str(ev)


def MenuEntry(label: str, shortcut: str = ""):
    if shortcut:
        idx = label.index(shortcut)
        if idx == 0:
            label = [shortcut, label[1:]]
        elif idx == (len(label) - 1):
            label = [label[:-1], shortcut]
        else:
            label = label.split(shortcut, maxsplit=2)
            label = [label[0], shortcut, label[1]]
    else:
        label = [label]
    return Div([
        *[
            Span(x, style=x == shortcut and Style(underline=True))
            for x in label
        ],
        Span(" ")
    ],
        className="menu_entry",
        on_focus=True,
    )


def MenuBar(props: WelcomeProps):
    return Div(
        [
            MenuEntry("File", "F"),
            MenuEntry("Edit", "E"),
            MenuEntry("Tools", "T"),
            MenuEntry("Exit", "x"),
        ],
        style=Style(
            background="bg-secondary",
            color="text-secondary",
            flexDirection="row",
            width="100%",
        )
    )


def Welcome(props: WelcomeProps = WelcomeProps()):
    return Div([
        MenuBar(props),
        Div([
            Span(text="Hello world!"),
        ],
            className="border quaternary p-1",
            id="holamundo",
        ),
        Div([
            Span(text="Another with some padding!"),
        ],
            id="holamundo2",
            style=Style(
            padding=1,
            background="bg-tertiary",
            color="text-tertiary",
            width="100%",
            flexGrow=1,
        )),
        Span(props.status, style=Style(
            width="100%",
            background="bg-tertiary",
            color="text-tertiary",
        )),
    ],
        style=Style(
            background="bg-primary",
            color="text-primary",
            width="100%",
            height="100%",
            alignItems="center",
            justifyItems="center",
            flexDirection="column",
    ),
    )


if __name__ == '__main__':
    dom = Welcome()
    renderer = XtermRenderer(document=dom)
    renderer.set_css({
        ".menubar": {
            "width": "100%",
            "background": "bg-primary",
            "color": "text-primary",
            ".shortcut": {
                "underline": True,
                "bold": True,
            }
        },
        ".main": {
            "flexGrow": 1,
            "background": "bg-secondary",
        },
        ".footer": {
            "background": "bg-primary",
        },
        ".border": {
            "borderStyle": "double",
        },
        ".menu_entry": {
            "flexDirection": "row",
        },
        ".menu_entry:focus": {
            "background": "text-primary",
            "color": "bg-primary",
        },
        ".p-1": {
            "padding": 1,
        },
        ".primary": {
            "background": "bg-primary",
            "color": "text-primary",
        },
        ".quaternary": {
            "background": "bg-quaternary",
            "color": "text-quaternary",
        },
        ".w-full": {
            "width": "100%",
        },
        ".h-1": {
            "height": 1,
        },
        "h-full": {
            "height": "100%",
        },
        ".flex-row": {
            "flexDirection": "row",
        },
        ".flex-column": {
            "flexDirection": "column",
        },
    })

    if sys.argv[1:] == ["layout"]:
        import json
        renderer.calculate_layout()
        renderer.print_layout(dom)
    else:
        props = WelcomeProps()
        while True:
            renderer.render()
            event = renderer.read_event()
            renderer.handle_event(event)
