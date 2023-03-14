from unittest import TestCase
from docutils import Component
from retui import ComponentPlan, component, createElement, reconcile, render, span
import logging

logger = logging.getLogger(__name__)


class Button(Component):
    state = {"is_selected": False}

    def render(self):
        state = self.state
        props = self.props
        return span(
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
                            component=span,
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
