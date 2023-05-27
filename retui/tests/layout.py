from unittest import TestCase
from retui.component import Text

from retui.document import Document


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
