#!/usr/bin/python3

import logging
import os
import pathlib
import sys

from retui import Component, Document, XtermRenderer
from retui.component import Scrollable
from retui.events import EventMouseClick, EventExit, EventKeyPress
from retui.widgets import (
    body,
    button,
    dialog,
    footer,
    select,
    header,
    option,
    div,
    span,
    input,
    textarea,
)

logger = logging.getLogger("main")


class CheckBox(Component):
    def render(self):
        logger.debug("Render Checkbox %s: %s", self, self.props)
        return span(on_click=self.props["on_click"])[
            self.props["value"] and "[x]" or "[ ]"
        ]


class FileSelector(Component):
    state = {
        "files": False,
        "path": pathlib.Path("."),
    }

    def componentDidMount(self):
        self.loadPath(pathlib.Path(self.props.get("path", ".")))
        self.document.setFocus(self)

    def loadPath(self, path):
        files = [".."]
        for filename in os.listdir(path):
            files.append(filename)
        self.setState({"files": files, "path": path})

    def handleSelectedFile(self, filename):
        path = self.state["path"] / filename
        if path.is_dir():
            self.loadPath(path)
            return

        handle = self.props.get("on_change")
        if handle:
            handle(path)

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
        return div(
            # on_keypress=self.handleKeyPress,
            className="w-full flex-1 items-center"
        )[
            [
                button(
                    id=filename,
                    className="w-full bg-tertiary color-tertiary bg-secondary-focus color-secondary-focus",
                    value=filename,
                    on_click=lambda ev: self.handleSelectedFile(
                        ev.target.queryParent("button").props["value"]
                    ),
                )[filename]
                for filename in self.state["files"]
            ]
        ]


def OpenfileDialog(onAccept: callable, onCancel: callable):
    return dialog()[
        div(
            className="items-center w-full self-center bold",
        )["Select file..."],
        Scrollable(className="flex-1", style={"padding": "1"})[
            FileSelector(path=".", className="flex-1", on_change=onAccept)
        ],
        span()[
            span(className="flex-1"),
            button(on_click=lambda ev: onAccept())[" Accept "],
            " ",
            button(on_click=lambda ev: onCancel())[" Cancel "],
        ],
    ]


class App(Document):
    state = {
        "is_on": True,
        "keypress": None,
        "openDialog": True,
    }

    def __init__(self, **kwargs):
        super().__init__(on_click=self.on_click, **kwargs)

    def on_keypress(self, ev: EventKeyPress):
        self.setState({"keypress": f"{ev.target.name} {ev.keycode}"})
        if ev.keycode == "ESC":
            self.quit()
            return
        super().on_keypress(ev)

    def on_click(self, ev: EventMouseClick):
        self.setState(
            {"keypress": f"{ev.target and ev.target.name} {ev.buttons} {ev.position}"}
        )

    def quit(self):
        self.document.on_event(EventExit(0))

    def handleMenu(self, menu_id):
        match menu_id:
            case "open":
                self.setState({"openDialog": True})
            case "close":
                self.setState({"openDialog": False})
            case "quit":
                self.quit()

    def render(self):
        return [
            header()[
                select(
                    label="File",
                    on_change=lambda ev: self.handleMenu(ev.value),
                )[
                    option(value="open")["Open..."],
                    option(value="close")["Close"],
                    option(value="quit")["Quit"],
                ],
                select(label="Edit")[
                    option()["Copy"],
                    option()["Paste"],
                    option()["Cut"],
                ],
                div(className="flex-1"),
                button(on_click=lambda ev: self.quit())["Quit"],
            ],
            body()[
                # FileSelector(path="."),
                span()[
                    "Toggle ",
                    CheckBox(
                        value=self.state["is_on"],
                        on_click=lambda ev: self.setState(
                            {"is_on": not self.state["is_on"]}
                        ),
                    ),
                ],
                input(className="bg-tertiary text-tertiary w-full"),
                textarea(
                    className="bg-primary color-primary w-full flex-1",
                    # rows=10,
                    # maxRows=10,
                ),
                self.state["openDialog"]
                and OpenfileDialog(
                    onAccept=lambda: self.setState({"openDialog": False}),
                    onCancel=lambda: self.setState({"openDialog": False}),
                ),
                # div(style={"position": "absolute",
                #     "top": 10, "left": 10, "background": "blue", "padding": 1, "border": 4, "borderColor": "#3355FF"})["Hola"]
            ],
            footer()["🐟 (C) 2023 | Coralbits SL | ", str(self.state["keypress"])],
        ]


def main():
    logging.basicConfig(level=logging.INFO)
    root = App()
    root.loop()


if __name__ == "__main__":
    main()
