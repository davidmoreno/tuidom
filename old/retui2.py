
from dataclasses import dataclass
import inspect
import tuidom


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


# def span(*children, **props):
#     return createElement(tuidom.Span, props, children)


def div(*children, **props):
    return createElement(tuidom.Div, props, children)


def button(*children, **props):
    return createElement(tuidom.Div, {"on_focus": True, **props}, children)


@component
def BoldText(text):
    return div(text, className="bold")


@component
def Counter(*, count, on_inc, on_dec):
    return div(
        button("+", on_click=on_inc),
        button("-", on_click=on_dec),
        div("Count is", count),
    )


class Toggle(Component):
    state = {"checked": False}

    def __init__(self, *children, checked=False, **props):
        self.state["checked"] = checked
        super().__init__(self, children, props)

    def handle_click(self, ev):
        self.setState({"checked": not self.state["checked"]})

    def render(self):
        checked = self.state["checked"]
        return [
            div("[x]" if checked else "[ ]",
                on_click=self.handle_click, on_focus=True),
            " ",
            "Toggle"
        ]


class App(Component):
    state = {"count": 0, "loading": True}

    def componentDidMount(self):
        self.setState({"loading": False})

    def render(self):
        if self.state["loading"]:
            return div("Loading...", className="bold", id="loading")

        return div(
            Counter(
                count=self.state["count"],
                on_inc=self.handle_inc,
                on_dec=self.handle_dec,
            ),
            Toggle(),
            style=tuidom.Style(width="100%", height="100%"),
        )

    def handle_inc(self):
        self.setState({"count": self.state["count"] + 1})

    def handle_dec(self):
        self.setState({"count": self.state["count"] - 1})


def render(node: ComponentBase, parent: tuidom.Element):
    print("render", parent, parent.children)
    if isinstance(node, (str, int)):
        print("add span str", parent, parent.children)
        parent.children.append(tuidom.Span(str(node)))
        return
    if isinstance(node, list):
        print("render list", node)
        for child in node:
            render(child, parent)
        return

    if inspect.isfunction(node.component):
        print("func")
        children = [node.component(**node.props)]
    elif inspect.isclass(node.component) and issubclass(node.component, tuidom.Element):
        print("DOM el")
        dom = node.component(**node.props)
        print("dom children", dom, dom.children)
        for child in node.children:
            render(child, dom)
        parent.children.append(dom)
        print("p0", parent.children[0])
    else:  # a class component
        print("CLASS")
        render(node.render(), parent)
        if not node._mounted:
            node._mounted = True
            node.componentDidMount()

    # if dom:
    #     print("add span str")
    #     dom.children = children
    #     parent.children.append(dom)


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
root = tuidom.Div(id="root")

renderer = tuidom.XtermRenderer(document=root)
while True:
    render(counter, root)
    renderer.render()
    event = renderer.read_event()
    event = renderer.handle_event(event)

render(counter, root)
# print(root, root.children)
# print(root.children is root.children[0].children)
# print(root.children[0], root.children[0].children)
# print(root.children[1], root.children[1].children)
root.print()
render(counter, root)
root.print()
# print(rendered)
# print(rendered.children)
# debug_render(rendered)
# print()
# debug_render(render(counter, root))

# print()
# counter.handle_inc()
# debug_render(render(counter, root))
