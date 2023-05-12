from unittest import TestCase

from retui import css
from retui.document import Document
from retui.widgets import body, div, textarea


class CssTestCase(TestCase):
    def test_compile_rule(self):
        rule = css.Selector(
            "body#id.class1.class2:hover",
        )

        self.assertEqual(rule.element, "body")
        self.assertEqual(rule.classes, ["class1", "class2"])
        self.assertEqual(rule.id, "id")
        self.assertEqual(rule.pseudo, ["hover"])
        self.assertGreater(rule.priority, 0)

        rule = css.Selector(
            "body",
        )
        self.assertGreater(rule.priority, 0)
        self.assertEqual(rule.element, "body")

    def test_match_rule(self):
        rule = css.Selector(
            "body#id.class1.class2",
        )

        element = body(className="class1 class2", id="id")
        self.assertTrue(rule.match(element))

        element = body(className="class1 class3", id="id")
        self.assertFalse(rule.match(element))

        element = div(className="class1 class2", id="id")
        self.assertFalse(rule.match(element))

        element = body(className="class1 class2")
        self.assertFalse(rule.match(element))

    def test_css_stylesheet(self):
        stylesheet = css.StyleSheet()
        stylesheet.addDict(
            {
                "body.class1.class2": {
                    "background": "blue",
                    "border": 1,
                    "borderRight": 2,
                    "z-index": 100,
                }
            }
        )
        element = body(className="class1 class2", id="id")

        self.assertEqual(stylesheet.getStyle(element, "borderRight"), 2)
        self.assertEqual(stylesheet.getStyle(element, "borderTop"), 1)
        self.assertEqual(stylesheet.getStyle(element, "paddingTop"), None)
        self.assertEqual(stylesheet.getStyle(element, "z-index"), 100)

    def test_css_at_document(self):
        class App(Document):
            def __init__(self):
                super().__init__(
                    stylesheet={
                        "textarea.class1.class2": {
                            "background": "blue",
                            "z-index": 100,
                        },
                    },
                )

            def render(self):
                return textarea(className="class1 class2")

        app = App()
        bdy = app.queryElement("textarea")
        self.assertIsNotNone(bdy)
        self.assertEqual(bdy.getStyle("background"), "blue")
