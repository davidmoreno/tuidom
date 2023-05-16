import logging
from unittest import TestCase
from retui.component import Component, Text
from retui.css import Selector
from retui.document import Document
from retui.tests.utils import printLayout
from retui.widgets import div, span, input

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
        self.assertEqual(app.children[0].children[0].props["className"], "bold")
        self.assertEqual(app.children[0].children[1].props.get("className"), None)

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
        self.assertEqual(app.children[0].children[0].props["className"], "bold")
        self.assertEqual(app.children[0].children[1].props.get("className"), None)

    def test_layout(self):
        class App(Document):
            def render(self):
                return div(id="body")[
                    span(id="b1")[
                        Text("H1", id="h1"),
                        Text("H2", id="h2", className="flex-1"),
                        Text("H3", id="h3"),
                    ],
                    Text("MID 1/3", id="b2", className="flex-1"),
                    Text("MID 2/3", id="b3", className="flex-2"),
                    Text("BOTTOM", id="b4"),
                ]

        app = App()
        app.materialize()
        app.prettyPrint()
        app.calculateLayoutSizes(80, 32, 80, 32)
        app.calculateLayoutPosition()

        printLayout(app)

        el = app.queryElement("#b1")
        self.assertEqual(el.layout.x, 0)
        self.assertEqual(el.layout.y, 0)
        self.assertEqual(el.layout.width, 80)
        self.assertEqual(el.layout.height, 1)

        el = app.queryElement("#b2")
        self.assertEqual(el.layout.x, 0)
        self.assertEqual(el.layout.y, 1)
        self.assertEqual(el.layout.width, 80)
        self.assertEqual(el.layout.height, 10)

        el = app.queryElement("#b3")
        self.assertEqual(el.layout.x, 0)
        self.assertEqual(el.layout.y, 11)
        self.assertEqual(el.layout.width, 80)
        self.assertEqual(el.layout.height, 20)

        el = app.queryElement("#b4")
        self.assertEqual(el.layout.x, 0)
        self.assertEqual(el.layout.y, 31)
        self.assertEqual(el.layout.width, 80)
        self.assertEqual(el.layout.height, 1)

    def test_css(self):
        class App(Document):
            def render(self):
                return div(id="body")[
                    span(id="b1")[
                        Text("H1", id="h1"),
                        Text("H2", id="h2", className="flex-1"),
                        Text("H3", id="h3"),
                    ],
                    Text("MID 1/3", id="b2", className="flex-1"),
                    div(id="b3", className="flex-2")[
                        input(id="i1", className="w-full"),
                        input(id="i2", className="w-full"),
                    ],
                    Text("BOTTOM", id="b4"),
                ]

        app = App(
            stylesheet={
                "input": {
                    "background": "white",
                },
                "input:focus": {
                    "background": "blue",
                },
            }
        )
        app.materialize()
        app.prettyPrint()

        fl1 = app.queryElement("#b2")
        self.assertTrue(fl1)
        self.assertEqual(fl1.props.get("className"), "flex-1")
        self.assertTrue(Selector(".flex-1").match(fl1))
        fl1 = app.queryElement(".flex-1")
        self.assertTrue(fl1)
        self.assertEqual(fl1.props.get("className"), "flex-1")

        inpt = app.queryElement("input")
        self.assertEqual(inpt.name, "input")
        self.assertEqual(inpt.props.get("id"), "i1")
        self.assertEqual(inpt.props.get("className"), "w-full")

        # check get proper style by priority

        # not :focus
        self.assertEqual(inpt.getStyle("background"), "text-secondary")

        # :focus
        app.currentFocusedElement = inpt
        inpt2 = app.queryElement("input:focus")
        self.assertEqual(inpt, inpt2)

        self.assertEqual(inpt.getStyle("background"), "bg-secondary")

        app.currentFocusedElement = inpt
        order_of_pri = [
            "",
            "*",
            "input",
            "input:focus",
            ".w-full",
            "input:focus.w-full",
            "input#i1.w-full",
            "input:focus#i1.w-full",
        ]
        pri = 0
        for sel in order_of_pri:
            npri = Selector(sel).match(inpt)
            logger.debug("'%s' -> %s", sel, npri)
            self.assertGreaterEqual(npri, pri)
            pri = npri

    def test_padding(self):
        item = div(style={"padding": "1 2 3 4"})
        item.document = Document()

        self.assertEqual(item.getStyle("paddingTop"), 1)
        self.assertEqual(item.getStyle("paddingRight"), 2)
        self.assertEqual(item.getStyle("paddingBottom"), 3)
        self.assertEqual(item.getStyle("paddingLeft"), 4)

        item = div(style={"padding": "1 2 3"})
        item.document = Document()
        self.assertEqual(item.getStyle("paddingTop"), 1)
        self.assertEqual(item.getStyle("paddingRight"), 2)
        self.assertEqual(item.getStyle("paddingBottom"), 3)
        self.assertEqual(item.getStyle("paddingLeft"), 2)

        item = div(style={"padding": "1 2"})
        item.document = Document()
        self.assertEqual(item.getStyle("paddingTop"), 1)
        self.assertEqual(item.getStyle("paddingRight"), 2)
        self.assertEqual(item.getStyle("paddingBottom"), 1)
        self.assertEqual(item.getStyle("paddingLeft"), 2)

        item = div(style={"padding": "1"})
        item.document = Document()
        self.assertEqual(item.getStyle("paddingTop"), 1)
        self.assertEqual(item.getStyle("paddingRight"), 1)
        self.assertEqual(item.getStyle("paddingBottom"), 1)
        self.assertEqual(item.getStyle("paddingLeft"), 1)

        item = div(style={"padding": 1})
        item.document = Document()
        self.assertEqual(item.getStyle("paddingTop"), 1)
        self.assertEqual(item.getStyle("paddingRight"), 1)
        self.assertEqual(item.getStyle("paddingBottom"), 1)
        self.assertEqual(item.getStyle("paddingLeft"), 1)

        item = div(
            style={
                "padding": 1,
                "paddingTop": 2,
                "paddingRight": 3,
                "paddingBottom": 4,
                "paddingLeft": 5,
            }
        )
        item.document = Document()
        self.assertEqual(item.getStyle("paddingTop"), 2)
        self.assertEqual(item.getStyle("paddingRight"), 3)
        self.assertEqual(item.getStyle("paddingBottom"), 4)
        self.assertEqual(item.getStyle("paddingLeft"), 5)

    def test_overflow(self):
        app = Document()[div(style={"width": 4})["Texto Largo"]]
        app.materialize().calculateLayout(25, 80)
        app.prettyPrint()

        self.assertEqual(app.queryElement("Text").layout.width, 4)
