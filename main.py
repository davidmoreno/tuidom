
import sys
from typing import Literal, Optional

from dataclasses import dataclass

from tuidom import Div, Span, Style, XtermRenderer, Event, KeyPress


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


def MenuBar(props: WelcomeProps):
    highlight = Style(
        background="bg-tertiary",
        color="text-tertiary"
    )
    return Div(
        [
            Span("File ", style=props.menu == "file" and highlight),
            Span("Edit ", style=props.menu == "edit" and highlight),
            Span("Tools ", style=props.menu == "tools" and highlight),
            Span("Exit ", style=props.menu == "exit" and highlight),
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
            Span(text="Hola Mundo!"),
        ],
            id="holamundo",
            style=Style(
            borderStyle="double",
            background="bg-secondary",
            color="text-secondary",
            flexGrow=0,
        )),
        Div([
            Span(text="Hola Mundo2!"),
        ],
            id="holamundo2",
            style=Style(
            padding=1,
            background="bg-tertiary",
            color="text-tertiary",
            flexGrow=0,
        )),
        Span(props.status),
    ],
        style=Style(
            background="bg-primary",
            color="text-primary",
            width="100%",
            height="100%",
            alignItems="center",
            justifyItems="center"
    ),
    )


if __name__ == '__main__':
    dom = Welcome()
    renderer = XtermRenderer()
    if sys.argv[1:] == ["layout"]:
        import json
        print(
            renderer.calculate_layout(dom),
        )
    else:
        props = WelcomeProps()
        while True:
            renderer.render(dom)
            event = renderer.read_event()
            props.handle_event(event)
            dom = Welcome(props)
