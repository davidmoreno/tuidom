
from dataclasses import dataclass
import inspect


@dataclass
class ComponentBase:
    component: callable
    props: dict
    children: list


class Component(ComponentBase):
    state = {}
    # this forces recalculation of children
    __dirty = True
    _mounted = False

    def __init__(self, *children, **props):
        super().__init__(self.__class__, props, children)

    def componentDidMount(self):
        return None

    def render(self):
        return None

    def setState(self, update):
        self.state = {
            **self.state,
            **update
        }
        self.__dirty = True


def createElement(component, props, children):
    return ComponentBase(component, props, children)


def component(func):
    def wrapped(*children, **props):
        return createElement(func,  props, children)
    wrapped.__name__ = func.__name__
    return wrapped


def span(*children, **props):
    return createElement("span", props, children)


def div(*children, **props):
    return createElement("div", props, children)


def button(*children, **props):
    return createElement("button", props, children)


@component
def BoldText(text):
    return span(text, className="bold")


@component
def Counter(*, count, on_inc, on_dec):
    return div(
        button("+", on_click=on_inc),
        button("-", on_click=on_dec),
        span("Count is", count),
    )


class Toggle(Component):
    state = {"checked": False}

    def __init__(self, *children, checked=False, **props):
        self.state["checked"] = checked
        super().__init__(self, children, props)

    def handle_click(self):
        self.setState({"checked": not self.state["checked"]})

    def render(self):
        checked = self.state["checked"]
        return [
            span("[x]" if checked else "[ ]", on_click=self.handle_click),
            " ",
            "Toggle"
        ]


class App(Component):
    state = {"count": 0, "loading": True}

    def componentDidMount(self):
        self.setState({"loading": False})

    def render(self):
        if self.state["loading"]:
            return span("Loading...", bold=True)

        return div(
            Counter(
                count=self.state["count"],
                on_inc=self.handle_inc,
                on_dec=self.handle_dec,
            ),
            Toggle(),
        )

    def handle_inc(self):
        self.setState({"count": self.state["count"] + 1})

    def handle_dec(self):
        self.setState({"count": self.state["count"] - 1})


def render(node: ComponentBase):
    if isinstance(node, (str, int)):
        return str(node)
    if isinstance(node, list):
        return [
            render(x)
            for x in node
        ]

    dom = False
    if inspect.isfunction(node.component):
        children = [node.component(**node.props)]
    elif isinstance(node.component, str):
        children = node.children
        dom = node.component
    else:
        children = [node.render()]
        if not node._mounted:
            node._mounted = True
            node.componentDidMount()

    children = [
        render(child)
        for child in children
    ]

    if dom:
        return (dom, children, node.props)

    return children


def debug_render(node, indent=0):
    if isinstance(node, list):
        for n in node:
            debug_render(n, indent)
        return
    ws = " " * indent
    if isinstance(node, str):
        print(f"{ws}{repr(node)}")
        return
    print(f"{ws}{node[0]} {node[2]}")
    for child in node[1]:
        debug_render(child, indent+2)


counter = App()
rendered = render(counter)
print(rendered)
debug_render(rendered)
print()
debug_render(render(counter))

print()
counter.handle_inc()
debug_render(render(counter))
