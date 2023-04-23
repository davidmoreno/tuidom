#!/usr/bin/python3

import logging

from retui import Component, Document, XtermRenderer
from retui.events import EventExit, EventKeyPress
from retui.widgets import body, button, footer, select, header, option, div, span, input, textarea

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

    def on_keypress(self, ev: EventKeyPress):
        self.setState({"keypress": ev.keycode})
        if ev.keycode == "ESC":
            self.quit()
            return
        super().on_keypress(ev)

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
                input(
                    className="bg-tertiary text-tertiary w-full"
                ),
                textarea(
                    className="bg-tertiary text-tertiary w-full",
                    rows=4,
                    maxRows=4,
                ),
            ],
            footer()["(C) 2023 | Coralbits SL | ",
                     str(self.state["keypress"])],
        ]


def main():
    logging.basicConfig(level=logging.INFO)
    renderer = XtermRenderer()
    root = App()
    root.loop(renderer)


if __name__ == '__main__':
    main()
