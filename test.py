#!/bin/python3

import logging
from unittest import TestCase
from tuidom import Div, Span, Style, TuiRenderer, XtermRenderer

logger = logging.getLogger(__name__)


class ClassNameTestCase(TestCase):
    def test_basic(self):
        dom = Div([], className="main")
        renderer = TuiRenderer(document=dom)
        renderer.set_css({
            ".main": {
                "width": "100%",
            }
        })
        self.assertEqual(renderer.get_style(dom, "width"), "100%")

    def test_style_rules(self):
        dom = Div([], className="main", style=Style(width=20))
        renderer = TuiRenderer(document=dom)
        renderer.set_css({
            ".main": {
                "width": "100%",
            }
        })
        self.assertEqual(renderer.get_style(dom, "width"), 20)

    def test_some_styles_inherit_others_dont(self):
        dom = Div([
            Div([], className="inner", id="inner")
        ], className="outer")
        renderer = TuiRenderer(
            document=dom,
            css={
                ".outer": {
                    "width": "100%",
                    "color": "blue",
                }
            }
        )
        inner = dom.queryElement("#inner")
        self.assertEqual(renderer.get_style(inner, "width"), None)
        self.assertEqual(renderer.get_style(inner, "color"), "blue")


class LayoutTestCase(TestCase):
    def test_basic_layout(self):
        dom = Div([])
        renderer = TuiRenderer(document=dom)
        renderer.calculate_layout()
        layout = dom.layout
        self.assertEqual(layout.top, 1)
        self.assertEqual(layout.left, 1)
        self.assertEqual(layout.width, renderer.width)
        self.assertEqual(layout.height, renderer.height)

    def test_app_layout(self):
        dom = Div([
            Div(className="menu"),
            Div(className="main"),
            Div(className="footer"),
        ])
        renderer = TuiRenderer(
            document=dom,
            css={
                ".menu": {
                    "height": 1,
                    "width": "100%",
                    "flexGrow": 0,
                },
                ".main": {
                    "flexGrow": 1,
                },
                ".footer": {
                    "height": 1,
                    "width": "100%",
                    "flexGrow": 0,
                },
            })
        renderer.calculate_layout()
        # print()
        # renderer.print_layout(dom)
        layout = dom.layout
        self.assertEqual(layout.top, 1)
        self.assertEqual(layout.left, 1)
        self.assertEqual(layout.width, renderer.width)
        self.assertEqual(layout.height, renderer.height)

        layout = dom.queryElement(".menu").layout
        self.assertEqual(layout.top, 1)
        self.assertEqual(layout.left, 1)
        self.assertEqual(layout.width, renderer.width)
        self.assertEqual(layout.height, 1)

        layout = dom.queryElement(".main").layout
        self.assertEqual(layout.top, 2)
        self.assertEqual(layout.left, 1)
        self.assertEqual(layout.width, renderer.width)
        self.assertEqual(layout.height, renderer.height-2)

        layout = dom.queryElement(".footer").layout
        self.assertEqual(layout.top, renderer.height)
        self.assertEqual(layout.left, 1)
        self.assertEqual(layout.width, renderer.width)
        self.assertEqual(layout.height, 1)

    def test_layout_w_border_and_padding(self):
        dom = TuiRenderer(
            document=Div([
                Div([Span("A")], id="a", className="grow-0 border-single"),
                Div([Span("B")], id="b", className="grow-0 p-1"),
                Div([Span("C")], id="c", className="grow-0 border-single p-1"),
                Div(className="grow-1"),
            ], className="w-full"),
            css={
                ".w-full": {
                    "width": "100%"
                },
                ".grow-0": {
                    "flexGrow": 0,
                },
                ".grow-1": {
                    "flexGrow": 1,
                },
                ".border-single": {
                    "borderStyle": "single"
                },
                ".p-1": {
                    "padding": 1,
                }
            })
        dom.calculate_layout()
        print()
        dom.print_layout(dom.document)
        self.assertEqual(dom.document.layout.width, dom.width)
        self.assertEqual(dom.queryElement("#a").layout.width, 5)


if __name__ == '__main__':
    logging.basicConfig()
    logger.info("Start TESTS")
    import unittest
    unittest.main()
