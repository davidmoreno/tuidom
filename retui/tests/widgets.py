import logging
from unittest import TestCase
from retui.component import Component, Text
from retui.document import Document
from retui.events import EventClick, EventKeyPress
from retui.widgets import div, select, option

logger = logging.getLogger(__name__)


class WidgetsTestCase(TestCase):
    def test_select(self):
        class App(Document):
            def render(self):
                return select()[
                    option(text="OptionA", value="option_a"),
                    option(text="OptionB", value="option_b"),
                    option(text="OptionB", value="option_b"),
                ]

        app = App()
        app.materialize()
        print(app.prettyPrint())
        self.assertEqual(
            app.queryElement("select").children[0].name,
            "Text"
        )

        app.on_event(EventKeyPress("TAB"))
        app.on_event(EventKeyPress("TAB"))
        # self.assertEqual(app.currentFocusedElement.name, "select")
        app.on_event(EventClick(1, (0, 0)))
        app.materialize()
        print(app.prettyPrint())
        self.assertEqual(
            app.queryElement("select").children[0].name,
            "div"
        )
