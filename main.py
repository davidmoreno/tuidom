
import sys

from test import Div, Span, Style, XtermRenderer, strlist_to_str


def Welcome():
    return Div(
        [
            Div([
                Span(text="Hola Mundo!"),
            ],
                id="holamundo",
                style=Style(
                borderWidth=1,
                borderStyle="solid",
                borderColor="white",
                background="bg-secondary",
                color="black",
            )),
            Div([
                Span(text="Hola Mundo2!"),
            ],
                id="holamundo2",
                style=Style(
                borderWidth=1,
                padding=1,
                background="bg-tertiary",
                color="black",
            ))
        ],
        style=Style(
            background="bg-primary",
            color="text-primary",
            width="100%",
            height="100%",
            alignItems="center",
            justifyItems="center"
        )
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
        print(
            strlist_to_str(
                renderer.render(dom))
        )
        input()
