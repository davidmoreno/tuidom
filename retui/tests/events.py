from retui.document import Document
from retui.events import EventMouseClick
from retui.widgets import div, span
from unittest import TestCase

import logging

logger = logging.getLogger(__name__)


class EventsTestCase(TestCase):
    def test_mouse_click(self):
        class App(Document):
            state = {"selected": None}

            def render(self):
                return div()[
                    span()[
                        span(
                            id="menu1",
                            className="p-1",
                            on_click=lambda ev: self.setState({"selected": "menu1"}),
                        )["Menu1"],
                        span(
                            id="menu2",
                            className="p-1",
                            on_click=lambda ev: self.setState({"selected": "menu2"}),
                        )["Menu2"],
                    ],
                    span(
                        id="menu3",
                        className="p-1",
                        on_click=lambda ev: self.setState({"selected": "menu3"}),
                    )["Menu3"],
                    span(
                        id="menu4",
                        className="p-1",
                        style={
                            "position": "absolute",
                            "zIndex": 10,
                            "top": 1,
                            "left": 3,
                            "width": 10,
                            "height": 1,
                        },
                        on_click=lambda ev: self.setState({"selected": "menu4"}),
                    )["Menu4"],
                ]

        app = App()
        app.materialize()
        app.prettyPrint()
        app.calculateLayoutSizes(0, 0, 80, 24)
        app.calculateLayoutPosition()
        for el in app.preorderTraversal():
            logger.debug("el: %s, layout: %s", el, el.layout)

        self.assertEqual(app.state["selected"], None)

        logger.debug("Click1")
        ev = EventMouseClick([1], (0, 0))
        app.on_event(ev)
        self.assertEqual(app.state["selected"], "menu1")

        logger.debug("Click2")
        ev = EventMouseClick([1], (6, 0))
        app.on_event(ev)
        self.assertEqual(app.state["selected"], "menu2")

        logger.debug("Click3")
        ev = EventMouseClick([1], (2, 1))
        app.on_event(ev)
        self.assertEqual(app.state["selected"], "menu3")

        logger.debug("Click4 index")
        ev = EventMouseClick([1], (4, 1))
        app.on_event(ev)
        self.assertEqual(app.state["selected"], "menu4")
