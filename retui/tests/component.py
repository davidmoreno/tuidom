import logging
from unittest import TestCase
from retui.component import Component, Text
from retui.document import Document
from retui.widgets import div

logger = logging.getLogger(__name__)


class ComponentTestCase(TestCase):
    def test_update_props(self):
        compa = Component(a=1, b=2, c=3)
        compb = Component(a=11, b=2, d=4)

        compa.updateProps(compb)
        logger.debug(compa.props)
        logger.debug(compb.props)

        self.assertIn("a", compa.props)
        self.assertIn("b", compa.props)
        self.assertNotIn("c", compa.props)
        self.assertIn("d", compa.props)

        self.assertEqual(compa.props["a"], 11)
        self.assertEqual(compa.props["b"], 2)
        self.assertEqual(compa.props["d"], 4)

    def test_reconcile_basic(self):
        class App(Document):
            state = {"is_on": False}

            def render(self):
                if self.state["is_on"]:
                    return Text("ON", className="on")
                else:
                    return Text("OFF", className="off")

        app = App()
        app.materialize()
        self.assertEqual(app.children[0].props["text"], "OFF")
        self.assertEqual(app.children[0].props["className"], "off")

        app.setState({"is_on": True})
        app.materialize()
        self.assertEqual(app.children[0].props["text"], "ON")
        self.assertEqual(app.children[0].props["className"], "on")

    def test_reconcile_change_component(self):
        class App(Document):
            state = {"is_on": False}

            def render(self):
                if self.state["is_on"]:
                    return Text("ON", className="on")
                else:
                    return div(className="off")[
                        Text("O", className="bold"),
                        Text("FF"),
                    ]

        app = App()
        app.materialize()
        app.prettyPrint()
        self.assertEqual(app.children[0].name, "div")
        self.assertEqual(app.children[0].children[0].props["text"], "O")
        self.assertEqual(app.children[0].children[1].props["text"], "FF")
        self.assertEqual(app.children[0].props["className"], "off")
        self.assertEqual(
            app.children[0].children[0].props["className"], "bold")
        self.assertEqual(
            app.children[0].children[1].props.get("className"), None)

        app.setState({"is_on": True})
        app.materialize()
        app.prettyPrint()
        self.assertEqual(app.children[0].name, "Text")
        self.assertEqual(app.children[0].props["text"], "ON")
        self.assertEqual(app.children[0].props["className"], "on")

        app.setState({"is_on": False})
        app.prettyPrint()
        app.materialize()
        self.assertEqual(app.children[0].children[0].props["text"], "O")
        self.assertEqual(app.children[0].children[1].props["text"], "FF")
        self.assertEqual(app.children[0].props["className"], "off")
        self.assertEqual(
            app.children[0].children[0].props["className"], "bold")
        self.assertEqual(
            app.children[0].children[1].props.get("className"), None)
