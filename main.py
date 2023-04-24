#!/usr/bin/python3

import logging
import os

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


class FileSelector(Component):
    state = {
        "files": False,
    }

    def componentDidMount(self):
        files = []
        for filename in os.listdir(self.props.get("path", ".")):
            files.append(filename)
        self.setState({"files": files})

        self.document.setFocus(self)

    def handleSelectedFile(self, filename):
        pass

    def handleKeyPress(self, ev: EventKeyPress):
        if not self.queryElement("button:focus"):
            self.document.setFocus(self.queryElement("button"))

        if ev.keycode == "UP":
            self.document.prevFocus()
        if ev.keycode == "DOWN":
            self.document.nextFocus()

    def render(self):
        if self.state["files"] is False:
            return div()["Loading..."]
        return div(on_keypress=self.handleKeyPress)[
            [button(on_click=lambda ev:self.handleSelectedFile(x))[x]
             for x in self.state["files"]]
        ]


class App(Document):
    state = {
        "is_on": True,
        "keypress": None,
    }

    def on_keypress(self, ev: EventKeyPress):
        self.setState({"keypress": f"{ev.target.name} {ev.keycode}"})
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
                FileSelector(path="."),
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
                div(style={
                    "position": "absolute",
                    "top": 10,
                    "left": 10,
                    "width": 20,
                    "height": 10,
                    "maxWidth": 20,
                    "background": "#ff7777",
                    "text": "#fff",
                    "padding": 1,
                })[
                    div(className="flex-1")[
                        "Hello world"
                    ],
                    span()[
                        span(className="flex-1"),
                        button(on_click=lambda ev:None)[" Accept "],
                        button(on_click=lambda ev:None)[" Cancel "],
                    ]
                ]
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
