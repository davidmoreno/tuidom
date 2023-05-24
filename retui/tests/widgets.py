import logging
from unittest import TestCase
from retui.component import Component, Text
from retui.document import Document
from retui.events import EventChange, EventMouseClick, EventKeyPress
from retui.tests.utils import printLayout
from retui.widgets import div, select, option, textarea

logger = logging.getLogger(__name__)


class WidgetsTestCase(TestCase):
    def test_select(self):
        class App(Document):
            state = {"last": None}

            def handle_change(self, ev: EventChange):
                logger.debug(
                    "Event changed: %s target: %s, value: %s", ev, ev.target, ev.value
                )
                self.setState({"last": ev.value})

            def render(self):
                return select(
                    on_change=self.handle_change,
                    value=None,
                )[
                    option(value="option_a", id="option_a")["OptionA"],
                    option(value="option_b", id="option_b")["OptionB"],
                    option(value="option_b", id="option_b")["OptionB"],
                ]

        app = App()
        app.materialize()
        app.calculateLayout()
        print(app.prettyPrint())
        selectel = app.queryElement("select")
        self.assertEqual(selectel.children[0].name, "Text")

        # first try with mouse
        app.on_event(EventMouseClick([1], (0, 0)))
        app.materialize()
        app.calculateLayout()
        printLayout(app)
        print(app.prettyPrint())
        self.assertIn(selectel, app.findElementAt(0, 0).parentTraversal())

        self.assertTrue(app.queryElement("select:focus"))
        self.assertTrue(app.queryElement("select:open"))
        self.assertEqual(app.state["last"], None)
        print("At option1 position", list(app.findElementAt(2, 1).parentTraversal()))
        app.on_event(EventMouseClick([1], (0, 1)))
        self.assertEqual(app.state["last"], "option_a")

        # click outside, lost focus

        # then tabs and arrows
        app.on_event(EventKeyPress("TAB"))
        app.on_event(EventKeyPress("TAB"))
        app.on_event(EventKeyPress("ENTER"))
        app.materialize()
        print(app.prettyPrint())
        self.assertEqual(app.queryElement("select").children[0].name, "div")

    def test_textarea(self):
        inpt = textarea()

        for c in "Hello\nworld!":
            inpt.handleKeyPress(EventKeyPress(c))

        self.assertEqual(inpt.getValue(), "Hello\nworld!")
        self.assertEqual(inpt.cursor, (6, 1))

        inpt.handleKeyPress(EventKeyPress("START"))
        self.assertEqual(inpt.cursor, (0, 1))

        inpt.handleKeyPress(EventKeyPress("UP"))
        self.assertEqual(inpt.cursor, (0, 0))

        inpt.handleKeyPress(EventKeyPress("UP"))
        self.assertEqual(inpt.cursor, (0, 0))

        inpt.handleKeyPress(EventKeyPress("END"))
        self.assertEqual(inpt.cursor, (5, 0))

        inpt.handleKeyPress(EventKeyPress("DOWN"))
        self.assertEqual(inpt.cursor, (5, 1))

        inpt.handleKeyPress(EventKeyPress("DOWN"))
        self.assertEqual(inpt.cursor, (5, 1))

        inpt = textarea(defaultValue="Hello\nworld!", rows=4, maxRows=10)
        inpt.document = Document()
        width, height = inpt.calculateLayoutSizes(0, 0, 100, 100)
        self.assertEqual(height, 4)
