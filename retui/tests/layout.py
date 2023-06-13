import logging
from unittest import TestCase
from retui.component import Text

from retui.document import Document
from retui.widgets import div

logger = logging.getLogger(__name__)


class LayoutTestCase(TestCase):
    """
    Tests layouts
    """

    def test_simple_flex_row(self):
        """
        Very basic test layout row
        """
        app = Document(style={"display": "flex", "flex-direction": "row"})[
            Text(id="t1", text="Text1"),
            Text(id="t2", text="Text2"),
        ]
        app.materialize()
        app.calculateLayout()
        app.layout.prettyPrint()

        t1 = app.queryElement("#t1")
        self.assertEqual(t1.layout.x, 0)
        self.assertEqual(t1.layout.y, 0)
        self.assertEqual(t1.layout.width, 5)
        self.assertEqual(t1.layout.height, 1)

        t2 = app.queryElement("#t2")
        self.assertEqual(t2.layout.x, 5)
        self.assertEqual(t2.layout.y, 0)
        self.assertEqual(t2.layout.width, 5)
        self.assertEqual(t2.layout.height, 1)

    def test_simple_flex_col(self):
        app = Document(style={"display": "flex", "flex-direction": "column"})[
            Text(id="t1", text="Text1 long"),
            Text(id="t2", text="Text2"),
        ]
        app.materialize()
        app.calculateLayout()
        app.layout.prettyPrint()
        t1 = app.queryElement("#t1")
        self.assertEqual(t1.layout.x, 0)
        self.assertEqual(t1.layout.y, 0)
        self.assertEqual(t1.layout.width, 10)
        self.assertEqual(t1.layout.height, 1)

        t2 = app.queryElement("#t2")
        self.assertEqual(t2.layout.x, 0)
        self.assertEqual(t2.layout.y, 1)
        self.assertEqual(t2.layout.width, 10)
        self.assertEqual(t2.layout.height, 1)

    def test_simple_block(self):
        app = Document(style={"display": "block", "max-width": 12})[
            Text(id="t1", text="Text1 long"),  # almost get to max
            Text(id="t2", text="Text2"),  # overflow, go next line
            Text(id="t3", text="Text3"),  # fits
            Text(  # next line does not fit
                id="t4",
                text="This should use several lines to be able to display as its longer than 12 chars.",
            ),
        ]
        app.materialize()
        app.calculateLayout()
        app.layout.prettyPrint()

        t1 = app.queryElement("#t1")
        self.assertEqual(t1.layout.x, 0)
        self.assertEqual(t1.layout.y, 0)
        self.assertEqual(t1.layout.width, 10)
        self.assertEqual(t1.layout.height, 1)

        t2 = app.queryElement("#t2")
        self.assertEqual(t2.layout.x, 0)
        self.assertEqual(t2.layout.y, 1)
        self.assertEqual(t2.layout.width, 5)
        self.assertEqual(t2.layout.height, 1)

        t3 = app.queryElement("#t3")
        self.assertEqual(t3.layout.x, 6)
        self.assertEqual(t3.layout.y, 1)
        self.assertEqual(t3.layout.width, 5)
        self.assertEqual(t3.layout.height, 1)

        t3 = app.queryElement("#t4")
        self.assertEqual(t3.layout.x, 0)
        self.assertEqual(t3.layout.y, 2)
        self.assertEqual(t3.layout.width, 80)
        self.assertEqual(t3.layout.height, 1)

    def test_absolute(self):
        app = Document(id="doc", style={"display": "flex", "flex-direction": "column"})[
            div(id="m1", style={"flex-grow": 0})["Top"],
            div(id="m2", style={"flex-grow": 1})["Middle"],
            div(id="m3", style={"flex-grow": 0})["Bottom"],
            div(
                id="abs",
                style={
                    "position": "absolute",
                    "z-index": 1,
                    "align-items": "center",
                    "justify-items": "center",
                    "width": 40,
                    "height": 20,
                },
            )[div(id="inside")["Inside"]],
        ]
        app.materialize()
        app.calculateLayout()
        app.layout.prettyPrint()

        self.assertEqual(app.layout.width, 80)
        self.assertEqual(app.layout.height, 25)

        self.assertEqual(app.queryElement("#m1").layout.height, 1)
        self.assertEqual(app.queryElement("#m2").layout.height, 23)
        self.assertEqual(app.queryElement("#m3").layout.height, 1)

        self.assertEqual(app.queryElement("#abs").layout.height, 20)
        self.assertEqual(app.queryElement("#abs").layout.width, 40)
        self.assertEqual(app.queryElement("#abs").layout.x, 3)
        self.assertEqual(app.queryElement("#abs").layout.y, 20)

        self.assertEqual(app.queryElement("#inside").layout.height, 1)
