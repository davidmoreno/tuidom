#!/bin/python3

import logging
from unittest import TestCase
from retui import Component, ComponentPlan, component, createElement, div, reconcile, render, render_to_dom, span
from tuidom import Div, KeyPress, Span, Style, TuiRenderer, XtermRenderer

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

    def test_focus_pseudo_element(self):
        dom = Div([
            Span("File ", className="menuitem", id="file", on_focus=True),
            Span("Edit ", className="menuitem", id="edit", on_focus=True),
            Span("Tools ", className="menuitem", id="tools", on_focus=True),
        ], className="menu")
        renderer = TuiRenderer(
            document=dom,
            css={
                ".menuitem": {
                    "color": "white",
                    "background": "blue",
                },
                ".menuitem:focus": {
                    "color": "blue",
                    "background": "white",
                },
            }
        )
        file = dom.queryElement("#file")
        self.assertEqual(renderer.get_style(file, "color"), "white")
        renderer.set_focus(file)
        self.assertEqual(renderer.get_style(file, "color"), "blue")


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
        # print()
        # dom.print_layout(dom.document)
        self.assertEqual(dom.document.layout.width, dom.width)
        self.assertEqual(dom.queryElement("#a").layout.width, dom.width)


class EventsTestCase(TestCase):
    def test_focus(self):
        dom = TuiRenderer(
            document=Div([
                Div([
                    Div([Span("A")], id="a", on_focus=True),
                    Div([Span("B")], id="b", on_focus=True),
                    Div([Span("C")], id="c", on_focus=True),
                ]),
                Div(),
            ])
        )
        # until first tab nothing is selected
        sel = dom.selected_element
        self.assertEqual(sel, None)

        dom.handle_event(KeyPress("TAB"))
        sel = dom.selected_element
        self.assertEqual(sel.id, "a")

        dom.handle_event(KeyPress("TAB"))
        sel = dom.selected_element
        self.assertEqual(sel.id, "b")

        dom.handle_event(KeyPress("TAB"))
        sel = dom.selected_element
        self.assertEqual(sel.id, "c")

        dom.handle_event(KeyPress("TAB"))
        self.assertIsNone(dom.selected_element, "a")

        dom.handle_event(KeyPress("TAB"))
        sel = dom.queryElement(":focus")
        self.assertEqual(sel.id, "a")
        sel = dom.queryElement("#a:focus")
        self.assertEqual(sel.id, "a")

        sel = dom.queryElement("#b:focus")
        self.assertIsNone(sel)


class Button(Component):
    state = {"is_selected": False}

    def render(self):
        state = self.state
        props = self.props
        return Span(
            text=props["text"],
            on_click=props["on_click"],
            style={
                "background": "white" if state["is_selected"] else "blue",
                "color": "blue" if state["is_selected"] else "white",
            },
            on_focus=lambda ev: self.setState({"is_selected": True}),
            on_blur=lambda ev: self.setState({"is_selected": False}),
        )


@component
def Counter(props):
    return span(text=str(props["text"]))


class App(Component):
    state = {"count": 1}

    def handle_increase(self, ev):
        self.setState({"count": self.state["count"] + 1})

    def handle_decrease(self, ev):
        self.setState({"count": self.state["count"] - 1})

    def render(self):
        return div(
            Counter(text=self.state["count"]),
            div(
                Button(text="+", on_click=self.handle_increase),
                Button(text="-", on_click=self.handle_increase),
                style={"flexDirection": "column"}
            ), style={"flexDirection": "row"}
        )


class SmartDomReplacementTestCase(TestCase):
    def test_create_plan(self):

        node = Counter(text=10)
        # print(node)
        self.assertTrue(
            node.same_as(
                ComponentPlan(
                    component=Counter.func,
                    props={"text": 10},
                    children=[
                        ComponentPlan(
                            component=Span,
                            props={"text": "10"}
                        )
                    ]
                )
            )
        )

    def test_reconcile_basic(self):
        node_a: ComponentPlan = Counter(text=10)
        node_b: ComponentPlan = Counter(text=20)

        span = node_a.children[0]

        node_c = reconcile(node_a, node_b)
        # is still the same component, but new props.
        self.assertEqual(node_a, node_c)
        self.assertEqual(node_a.props["text"], 20)
        self.assertEqual(node_a.children[0].props["text"], "20")

    def test_render_basic(self):
        node_a: ComponentPlan = Counter(text=20)
        dom = render(node_a)
        logger.debug("Render dom: %s", dom)
        self.assertEqual(dom[0].__class__.__name__, "Span")
        self.assertEqual(dom[0].text, "20")

        node_b: ComponentPlan = Counter(text=30)
        node_c = reconcile(node_a, node_b)
        dom = render(node_c)
        self.assertEqual(dom[0].text, "30")

    def test_render_complex(self):
        app: App = createElement(App, {})
        dom = render(app)
        print()
        print(app.to_string())
        print()
        # print(dom)
        self.assertNotEqual(dom, [])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Start TESTS")
    import unittest
    unittest.main()
