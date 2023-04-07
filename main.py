#!/usr/bin/python3

import logging

from retui import Component, Document, XtermRenderer, div, span

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
        return div(className="flex-row")[
            "Toggle ",
            CheckBox(
                value=self.state["is_on"],
                on_click=lambda ev: self.setState(
                    {"is_on": not self.state["is_on"]}
                )
            ),
        ]


def main():
    logging.basicConfig(level=logging.INFO)
    renderer = XtermRenderer()
    root = Document(App())
    root.loop(renderer)


if __name__ == '__main__':
    main()
