#!/usr/bin/python3

from dataclasses import dataclass, field
import itertools


class Renderer:
    def setColor(self, color):
        print("Color", color)
        pass

    def setBackground(self, color):
        print("BG", color)
        pass

    def drawSquare(self, orig, size):
        print("sq", orig, size)
        pass

    def drawText(self, position, text):
        print("TEXT", position, text)
        pass


def flatten_list(ml):
    """
    Actually it coud be a list of lists, or a simple
    element. But ensure always a list of simple elements
    """
    if isinstance(ml, (list, tuple)):
        return ml
    return [ml, ]


@dataclass
class Event:
    continuePropagation: bool = True
    target = None

    def stopPropagation(self):
        self.continuePropagation = False


class EventClick(Event):
    buttons: list[int]
    position: tuple[int, int]

    def __init__(self, buttons: list[int], position: tuple[int, int]):
        super().__init__()
        self.buttons = buttons
        self.position = position


class EventFocus(Event):
    pass


class EventKeyPress(Event):
    keycode: str

    def __init__(self, keycode: str):
        super().__init__()
        self.keycode = keycode


class Component:
    name = None
    children: list = None
    props: dict = None
    state: dict = None
    parent = None
    key = None

    __changed: bool = True
    __materialized_children: list = None

    def render(self):
        return self.children

    def paint(self, renderer: Renderer):
        print("paint", self)
        # if not self.__changed:
        #     return
        for child in self.__materialized_children:
            print("paint child", child)
            child.paint(renderer)

    def setChanged(self):
        if self.__changed:
            return
        self.__changed = True
        if self.parent:
            self.parent.setChanged()

    def setState(self, update):
        if self.state is None:
            self.state = {}

        self.state = {**self.state, **update}
        self.setChanged()

    def normalize(self, node):
        if isinstance(node, Component):
            return node
        if isinstance(node, (str, int, float)):
            return Text(text=str(node))
        if node is True:
            return Text(text=True)
        return None

    def materialize(self):
        if not self.__changed:
            return

        children = flatten_list(self.render())
        children = [
            self.normalize(x)
            for x in children
        ]
        children = [
            x for x in children if x
        ]

        if self.__materialized_children is None:
            for child in children:
                child.parent = self
            self.__materialized_children = children
        else:
            nextchildren = []
            for left, right in itertools.zip_longest(children,  self.__materialized_children):
                # print("materialize iseq", left, right)
                if self.isEquivalent(left, right):
                    left.updateProps(right)
                    nextchildren.append(left)
                else:
                    nextchildren.append(right)

            for child in nextchildren:
                if child.parent != self:
                    child.parent = self

            self.__materialized_children = nextchildren

        print("Materialized", self.__materialized_children)
        # rec materialize
        for child in self.__materialized_children:
            child.materialize()

    def isEquivalent(self, left, right):
        if not left or not right:
            return False
        if left.key == right.key:
            return True
        if left.name == right.name:
            return True

        return False

    def updateProps(self, other):
        for key, val in other.props.items():
            oldval = self.props.get(key)
            if not oldval:
                self.props[key] = val
                continue
            if oldval == val:
                continue
            if key[:3] == "on_":
                continue
            self.props[key] = val

    def __init__(self, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props

    def __getitem__(self, children: list):
        self.children = children
        return self

    def __repr__(self):
        if not self.children:
            return f"<{self.name}/>"
        else:
            return f"<{self.name}>{self.children}</{self.name}>"

    def queryElement(self, query):
        if self.name == query:
            return self
        for child in self.__materialized_children:
            ret = child.queryElement(query)
            if ret:
                return ret

    def on_event(self,  on_name, ev):
        if not ev.target:
            ev.target = self

        on_click = self.props.get(on_name)
        if on_click:
            on_click(ev)
        if ev.continuePropagation and self.parent:
            self.parent.on_event(on_name, ev)

    def on_click(self, ev: EventClick):
        self.on_event("on_click", ev)

    def on_focus(self, ev: EventFocus):
        self.on_event("on_focus", ev)


class Paintable(Component):
    def getStyle(self, property: str):
        return None

    def paint(self, renderer: Renderer):
        color = self.getStyle("color")
        if color:
            renderer.setColor("white")
        background = self.getStyle("background")
        if background:
            renderer.setBackground("blue")
            renderer.drawSquare(
                (0, 0), (10, 10),
            )
        super().paint(renderer)


class Text(Component):
    def paint(self, renderer: Renderer):
        text = self.props.get("text")
        if text:
            renderer.drawText(
                (5, 5),
                str(text)
            )


div = Paintable
div.__name__ = "div"
span = Paintable
span.__name__ = "span"


###

class CheckBox(Component):
    def render(self):
        return (
            span(
                on_click=self.props["on_click"]
            )[
                self.props["value"] and "[x]" or "[ ]"
            ]
        )


class App(Component):
    state = {
        "is_on": True,
    }

    def render(self):
        return div(className="flex-row")[
            "Toggle",
            CheckBox(
                value=self.state["is_on"],
                on_click=lambda ev: self.setState(
                    {"is_on": not self.state["is_on"]}
                )
            )
        ]


renderer = Renderer()

root = App()
root.materialize()
root.paint(renderer)

ev = EventClick([1], (10, 10))
root.queryElement("CheckBox").on_click(ev)

print()

root.materialize()
root.paint(renderer)

# print(span().render())
# span().paint(renderer)
