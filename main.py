#!/usr/bin/python3

import logging

from retui import Component, Document, XtermRenderer
from retui.events import EventExit, EventKeyPress
from retui.widgets import body, button, footer, select, header, option, div, span

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


class App(Document):
    state = {
        "is_on": True,
        "keypress": None,
    }

    def handleKeyPress(self, ev: EventKeyPress):
        self.setState({"keypress": ev})
        if ev.keycode == "ESC":
            self.quit()

    def quit(self):
        self.document.on_event(EventExit(0))

    def render(self):
        return [
            header()[
                select(label="File")[
                    option()["Open..."],
                    option()["Close"],
                    option()["Quit"],
                ],
                select(label="Edit")[
                    option()["Copy"],
                    option()["Paste"],
                    option()["Cut"],
                ],
                div(className="flex-1"),
                button(on_click=lambda ev:self.quit())[
                    "Quit"
                ]
            ],
            body()[
                span()[
                    "Toggle ",
                    CheckBox(
                        value=self.state["is_on"],
                        on_click=lambda ev: self.setState(
                            {"is_on": not self.state["is_on"]}
                        )
                    )],
            ],
            footer()["(C) 2023 | Coralbits SL | ",
                     str(self.state["keypress"])],
        ]


def main():
    logging.basicConfig(level=logging.INFO)
    renderer = XtermRenderer()
    root = App()
    renderer.loop(root)


if __name__ == '__main__':
    main()
