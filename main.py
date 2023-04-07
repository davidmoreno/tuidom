#!/usr/bin/python3

import logging

from retui import Component, Document, XtermRenderer, div, span
from retui.widgets import Body, Footer, Menu, MenuBar, MenuItem

logger = logging.getLogger("main")


class CheckBox(Component):
    def render(self):
        logger.debug("Render Checkbox %s: %s", self, self.props)
        return (
            span(
                on_click=self.props["on_click"]
            )[
                self.props["value"] and "[x]" or "[ ]"
            ]
        )


class App(Component):
    state = {
        "is_on": True,
    }

    def render(self):
        return [
            MenuBar()[
                Menu(label="File")[
                    MenuItem()["Open..."],
                    MenuItem()["Close"],
                    MenuItem()["Quit"],
                ],
                Menu(label="Edit")[
                    MenuItem()["Copy"],
                    MenuItem()["Paste"],
                    MenuItem()["Cut"],
                ]
            ],
            Body()[
                span()[
                    "Toggle ",
                    CheckBox(
                        value=self.state["is_on"],
                        on_click=lambda ev: self.setState(
                            {"is_on": not self.state["is_on"]}
                        )
                    )],
            ],
            Footer()["(C) 2023 | Coralbits SL"],
        ]


def main():
    logging.basicConfig(level=logging.INFO)
    renderer = XtermRenderer()
    root = Document(App())
    renderer.loop(root)


if __name__ == '__main__':
    main()
