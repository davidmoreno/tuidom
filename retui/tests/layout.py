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
