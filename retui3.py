#!/usr/bin/python3

from dataclasses import dataclass
import itertools
import logging
import os
import shutil
import sys
import termios
import tty

logger = logging.getLogger(__name__)


class Renderer:
    color = "white"
    background = "blue"

    def setColor(self, color):
        self.color = color

    def setBackground(self, color):
        self.background = color

    def drawSquare(self, orig, size):
        logger.debug("sq %s %s", orig, size)
        pass

    def drawText(self, position, text):
        print(text)
        logger.debug("TEXT %s %s", position, text)
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        width, height = shutil.get_terminal_size()
        self.width = width
        self.height = height

        fd = sys.stdin.fileno()
        self.oldtermios = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~(termios.ECHO | termios.ICANON)        # lflags
        termios.tcsetattr(fd, termios.TCSADRAIN, new)

        # save screen state
        # print("\033[?1049h;")

    def close(self):
        # recover saved state
        # print("\033[?1049l;")

        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self.oldtermios)

    def readEvent(self):
        key = os.read(sys.stdin.fileno(), 1)

        if 0 < ord(key) < 27:
            key = chr(ord(key) + ord('A') - 1)
            if key == "I":
                key = "TAB"
            elif key == "J":
                key = "ENTER"
            else:
                key = f"CONTROL+{key}"
            return EventKeyPress(key)
        return EventKeyPress(key.decode("iso8859-15"))


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
    name: str
    stopPropagation: bool = False
    target = None


class EventClick(Event):
    buttons: list[int]
    position: tuple[int, int]

    def __init__(self, buttons: list[int], position: tuple[int, int]):
        super().__init__("click")
        self.buttons = buttons
        self.position = position


class EventFocus(Event):
    name = "focus"
    pass


class EventKeyPress(Event):
    keycode: str

    def __init__(self, keycode: str):
        super().__init__("keypress")
        self.keycode = keycode


class Component:
    serialid = 0  # jsut for debugging, to ensure materialize reuses as possible
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
        logger.debug("paint %s", self)
        # if not self.__changed:
        #     return
        for child in self.__materialized_children:
            logger.debug("paint child %s", child)
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
        """
        Helper to return always some component, normally translating
        strings to Text nodes.
        """
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
            for left, right in itertools.zip_longest(self.__materialized_children, children):
                # print("materialize iseq", left, right)
                if self.isEquivalent(left, right):
                    logger.debug("Materialize reconcile: %s ~ %s", left, right)
                    left.updateProps(right)
                    nextchildren.append(left)
                else:
                    logger.debug(
                        "Materialize reconcile: %s != %s", left, right)
                    nextchildren.append(right)

            for child in nextchildren:
                if child.parent != self:
                    child.parent = self

            self.__materialized_children = nextchildren

        logger.debug("Materialized %s -> %s", self,
                     self.__materialized_children)
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
        logger.debug("Update props: %s from %s", self.props, other.props)
        for key, val in other.props.items():
            oldval = self.props.get(key)
            if not oldval:
                self.props[key] = val
                continue
            if oldval == val:
                continue
            if key[:3] == "on_":
                logger.debug("Do not replace on_ props: %s", key)
                continue
            logger.debug("Replace props: %s", key)
            self.props[key] = val

    def queryElement(self, query):
        if self.name == query:
            return self
        for child in self.__materialized_children:
            ret = child.queryElement(query)
            if ret:
                return ret

    def preorderTraversal(self):
        yield self
        for child in self.__materialized_children:
            yield from child.preorderTraversal()

    def __init__(self, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props
        Component.serialid += 1
        self.serialid = Component.serialid
        super().__init__()

    def __getitem__(self, children: list):
        self.children = children
        return self

    def __repr__(self):
        if not self.children:
            return f"<{self.name} {self.serialid} {self.state}/>"
        else:
            return f"<{self.name} {self.serialid} {self.state}>{self.children}</{self.name}>"


class Paintable(Component):
    """
    This component can be painted with the given renderer
    """

    def getStyle(self, key: str) -> str | None:
        """
        Returns a style by key.

        It might be search by classname or splicitly set
        """
        match key:
            case "color":
                return "white"
            case "background":
                return "blue"
        return None

    def paint(self, renderer: Renderer):
        color = self.getStyle("color")
        if color:
            renderer.setColor(color)
        background = self.getStyle("background")
        if background:
            renderer.setBackground(background)
            renderer.drawSquare(
                (0, 0), (10, 10),
            )
        super().paint(renderer)


class Document(Component):
    """
    A component with some extra methods
    """
    currentFocusedElement = None

    def __init__(self, root=None):
        super().__init__()
        if root:
            self.children = [root]
        self.props = {
            "on_keypress": self.on_keypress,
        }

    def setRoot(self, root):
        self.children = [root]

    @property
    def root(self):
        return self.children[0]

    def is_focusable(self, el):
        for key in el.props.keys():
            if key.startswith("on_"):
                return True
        return False

    def nextFocus(self):
        prev = self.currentFocusedElement
        logger.debug("Current focus is %s", prev)
        for child in self.root.preorderTraversal():
            if self.is_focusable(child):
                if prev is None:
                    logger.debug("Set focus on %s", child)
                    self.currentFocusedElement = child
                    return child
                elif prev is child:
                    prev = None
        logger.debug("Lost focus")
        self.currentFocusedElement = None
        return None

    def on_keypress(self, event: EventKeyPress):
        if event.keycode == "TAB":
            self.nextFocus()
        if event.keycode == "ENTER":
            self.on_event(EventClick([1], (0, 0)))

    def on_event(self, ev: Event):
        name = ev.name
        if not ev.target:
            item = self.currentFocusedElement
            if not item:
                item = self
            ev.target = item
        else:
            item = ev.target

        while item:
            event_handler = item.props.get(f"on_{name}")
            logger.debug(f"Event {name} on {item}: {event_handler}")
            if event_handler:
                event_handler(ev)
            if ev.stopPropagation:
                return
            item = item.parent

        # not handled


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


def main():
    logging.basicConfig(level=logging.DEBUG)
    renderer = Renderer()

    root = Document(App())

    while True:
        logger.debug("\nMaterialize:")
        root.materialize()
        logger.debug("\nRender:")
        root.paint(renderer)
        logger.debug("\nEvent:")
        root.on_event(renderer.readEvent())


if __name__ == '__main__':
    main()
