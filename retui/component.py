

from dataclasses import dataclass
import itertools
import logging
from typing import Literal
from .events import HandleEventTrait
from .renderer import Renderer
logger = logging.getLogger(__name__)


StyleProperty = Literal[
    "color",
    "background",
    "flex-direction",
    "flex-grow",
    "padding",
    "border",
    "width",
    "height",
]

# this styles are checked against parents if not defined
INHERITABLE_STYLES: list[StyleProperty] = ["color", "background"]


@dataclass
class Layout:
    y: int = 0
    x: int = 0
    width: int = 0
    height: int = 0


class Component:
    serialid = 0  # just for debugging, to ensure materialize reuses as possible
    name = None
    children: list = None
    props: dict = None
    state: dict = None
    parent = None
    document = None
    key = None
    layout: Layout = None

    __changed: bool = True
    __materialized_children: list = None

    def __init__(self, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props
        Component.serialid += 1
        self.serialid = Component.serialid
        self.layout = Layout()
        super().__init__()

    def __getitem__(self, children: list):
        self.children = children
        return self

    def __repr__(self):
        if not self.children:
            return f"<{self.name} {self.serialid} {self.props}/>"
        else:
            return f"<{self.name} {self.serialid} {self.props}>{self.children}</{self.name}>"

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
        logger.debug("Update state %s: %s", self, update)
        if self.state is None:
            self.state = {}

        self.state = {**self.state, **update}
        self.setChanged()

    def normalize(self, nodes):
        """
        Helper to return always some component, normally translating
        strings to Text nodes.
        """
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        ret = []
        for item in nodes:
            if isinstance(item, Component):
                item.children = self.normalize(item.children)
                ret.append(item)
            elif item is True:
                ret.append(Text(text=True))
            elif item is False or item is None:
                continue  # skip Falses and Nones
            else:
                ret.append(Text(text=str(item)))
        return ret

    def materialize(self):
        if not self.__changed:
            return

        children = self.normalize(self.render())

        if self.__materialized_children is None:
            for child in children:
                child.parent = self
                child.document = self.document
            self.__materialized_children = children
        else:
            nextchildren = self.reconcile(
                self,
                self.__materialized_children,
                children
            )

            self.__materialized_children = nextchildren

        logger.debug("Materialized %s -> %s", self,
                     self.__materialized_children)
        # rec materialize
        for child in self.__materialized_children:
            child.materialize()

    def reconcile(self, parent, leftchildren, rightchildren):
        logger.debug("Reconcile two lists: %s <-> %s",
                     leftchildren, rightchildren)
        nextchildren = []
        for left, right in itertools.zip_longest(leftchildren, rightchildren):
            # print("materialize iseq", left, right)
            logger.debug("is eq: %s %s", left, right)
            if self.isEquivalent(left, right):
                logger.debug("Materialize reconcile: %s ~ %s", left, right)
                left.updateProps(right)
                nextchildren.append(left)
            else:
                logger.debug(
                    "Materialize reconcile: %s != %s", left, right)
                nextchildren.append(right)
            left.children = self.reconcile(
                left,
                left.children or [],
                right.children or [],
            )

        for child in nextchildren:
            if child.parent != parent:
                child.parent = parent
                child.document = self.document
        return nextchildren

    def isEquivalent(self, left, right):
        if not left or not right:
            return False
        if left.key == right.key:
            return True
        if left.name == right.name:
            return True

        return False

    def updateProps(self, other):
        logger.debug("%s Update props: %s from %s",
                     self, self.props, other.props)
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

    def getStyle(self, csskey: StyleProperty):
        style = self.props.get("style")
        if style:
            value = style.get(csskey)
            if value:
                return value

        for selector, style in self.document.css.items():
            if self.matchCssSelector(selector):
                value = style.get(csskey)
                if value:
                    return value
        if csskey in INHERITABLE_STYLES and self.parent:
            return self.parent.getStyle(csskey)

        return None

    def matchCssSelector(self, selector: str) -> bool:
        """
        Very simple selectors. Simple classnames, type and ids. Not nested.
        """
        if selector == self.name:
            return True
        if selector.startswith("."):
            class_name = self.props.get("className")
            if class_name:
                class_name = class_name.split(" ")
                if selector[1:] in class_name:
                    return True
        if selector.startswith("#"):
            id = self.props.get("id")
            if id and id == selector[1:]:
                return True
        return False

    def calculateProportion(self, current, rule):
        """
        Many sizes and positions are relative to the parent size

        This function hides this
        """
        # WIP, only fixed char sizes
        if rule is None:
            return None
        if isinstance(rule, int):
            return max(0, min(current, rule))
        if isinstance(rule, str):
            if rule == "auto":
                return None
            if rule.endswith("%"):
                return int(current * int(rule[:-1]) / 100)
            logger.warning("Invalid width rule: %s", rule)
        return None

    def calculateLayoutSizes(self, min_width, min_height, max_width, max_height):
        """
        Calculates the layout inside the desired rectangle.

        Given the given constraints, sets own size. 
        Once we have the size, position is calculated later.
        """
        width = self.calculateProportion(max_width, self.getStyle("width"))
        if width:  # if there is a desired width, it is used
            min_width = width
            max_width = width
        height = self.calculateProportion(max_height, self.getStyle("height"))
        if height:  # if there is a desired height, it is used
            min_height = height
            max_height = height

        width = min_width
        height = max_height

        direction = self.getStyle("flex-direction")
        if direction == "row":
            width, height = self.calculateLayoutSizesHorizontal(
                min_width, min_height, max_width, max_height)
        else:  # default for even unknown is vertical stack
            width, height = self.calculateLayoutSizesVertical(
                min_width, min_height, max_width, max_height)

        width = min(max_width, max(width, min_width))
        height = min(max_height, max(height, min_height))

        self.layout.width = width
        self.layout.height = height

        return (width, height)

    def calculateLayoutSizesVertical(self, min_width, min_height, max_width, max_height):
        width = 0
        height = 0
        for children in self.__materialized_children:
            cwidth, cheight = children.calculateLayoutSizes(
                min_width, min_height, max_width, max_height)
            width = max(cwidth, width)
            height += cheight
        return (width, height)

    def calculateLayoutSizesHorizontal(self, min_width, min_height, max_width, max_height):
        width = 0
        height = 0
        for children in self.__materialized_children:
            cwidth, cheight = children.calculateLayoutSizes(
                min_width, min_height, max_width, max_height)
            width += cwidth
            height = max(cheight, height)

        return (width, height)

    def calculateLayoutPosition(self):
        """
        Calculates the position of children: same as parent + sizeof prev childs.
        """
        x = self.layout.x
        y = self.layout.y
        print(self, x, y)
        child: Component
        for child in self.__materialized_children:
            child.layout.y = y
            child.layout.x = x
            child.calculateLayoutPosition()
            if self.getStyle("flex-direction") == "row":
                x += child.layout.width
            else:
                y += child.layout.height


class Paintable(HandleEventTrait, Component):
    """
    This component can be painted with the given renderer
    """

    def paint(self, renderer: Renderer):
        color = self.getStyle("color")
        if color:
            renderer.strokeStyle = color
        background = self.getStyle("background")
        if background:
            renderer.fillStyle = background
            renderer.fillRect(
                self.layout.x, self.layout.y,
                self.layout.width, self.layout.height,
            )
        super().paint(renderer)


class Text(Component):
    def paint(self, renderer: Renderer):
        text = self.props.get("text")
        if text:
            renderer.fillText(
                str(text),
                self.layout.x, self.layout.y,
            )

    def calculateLayoutSizes(self, min_width, min_height, max_width, max_height):
        text = self.props.get("text").split('\n')
        height = len(text)
        width = max(len(x) for x in text)
        if width < min_width:
            width = min_width
        if height < min_height:
            height = min_height

        if height > max_height:
            logger.warning("Text too big for viewport: %s %s %s",
                           self, width, height)
        if width > max_width:
            logger.warning("Text too big for viewport: %s %s %s",
                           self, width, height)

        self.layout.width = width
        self.layout.height = height

        return (width, height)


div = Paintable
div.__name__ = "div"
span = Paintable
span.__name__ = "span"
