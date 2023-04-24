

from dataclasses import dataclass
import itertools
import logging
import math
import re
from typing import Literal
from .events import HandleEventTrait
from .renderer import Renderer
logger = logging.getLogger(__name__)

CSS_SELECTOR_RE = re.compile(
    r"^(?P<name>\w+|)(?P<pseudo>(:\w+)*)(?P<id>#\w+|)(?P<class>(\.(\w|[-_])+)*)$")

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
    props: dict = None
    state: dict = None
    parent = None
    document = None
    key = None
    layout: Layout = None
    children: list = None
    # where to position the cursor relative to the parent, if focused
    # if exists, good, if not, checks parent
    # cursor: tuple[int, int] = (0, 0)

    __mounted: bool = False
    __changed: bool = True

    def __init__(self, *, children=None, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props
        Component.serialid += 1
        self.serialid = Component.serialid
        self.layout = Layout()
        self.children = children or []
        super().__init__()

    def __getitem__(self, children: list):
        self.props["children"] = children
        return self

    def __repr__(self):
        children = self.children
        ids = ""
        if "id" in self.props:
            ids = f"#{self.props['id']}"

        if not children:
            return f"<{self.name}{ids} {self.serialid}/>"
        else:
            return f"<{self.name}{ids} {self.serialid}>...{len(children)}...</{self.name}>"

    def componentDidMount(self):
        pass

    def render(self):
        return self.props.get("children", [])

    def paint(self, renderer: Renderer):
        # logger.debug("paint %s", self)
        # if not self.__changed:
        #     return
        for child in self.children:
            # logger.debug("paint child %s", child)
            child.paint(renderer)

    def setChanged(self):
        if self.__changed:
            return
        self.__changed = True
        if self.parent:
            self.parent.setChanged()

    def setState(self, update):
        # logger.debug("Update state %s: %s", self, update)
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
                item.props["children"] = self.normalize(
                    item.props.get("children", [])
                )
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

        if self.children is None:
            for child in children:
                child.parent = self
                child.document = self.document
            self.children = children
        else:
            nextchildren = self.reconcile(
                self,
                self.children,
                children
            )

            self.children = nextchildren

        # logger.debug("Materialized %s -> %s", self,
        #              self.children)
        # rec materialize
        for child in self.children:
            child.materialize()

        if not self.__mounted:
            self.__mounted = True
            self.componentDidMount()

    def reconcile(self, parent, leftchildren, rightchildren):
        # logger.debug("Reconcile two lists: %s <-> %s",
        #              leftchildren, rightchildren)
        nextchildren = []
        for left, right in itertools.zip_longest(leftchildren, rightchildren):
            # print("materialize iseq", left, right)
            # logger.debug("is eq: %s %s", left, right)
            if self.isEquivalent(left, right):
                # logger.debug("Materialize reconcile: %s ~ %s", left, right)
                left.updateProps(right)
                nextchildren.append(left)
                left.props["children"] = self.reconcile(
                    left,
                    left.props.get("children") or [],
                    right.props.get("children") or [],
                )
            elif right:
                # logger.debug(
                #     "Materialize reconcile: %s != %s", left, right)
                nextchildren.append(right)
                # first use of right, so mount
                right.parent = parent
                right.document = parent and parent.document
                if not right.__mounted:
                    right.__mounted = False
                    right.componentDidMount()

        nextchildren = [x for x in nextchildren if x]
        for child in nextchildren:
            if child.parent != parent:
                child.parent = parent
                child.document = self.document
        return nextchildren

    def isEquivalent(self, left, right):
        if not left or not right:
            return False
        if left.name == right.name:
            return True
        if left.key and left.key == right.key:
            return True

        return False

    def updateProps(self, other):
        # logger.debug("%s Update props: %s from %s",
        #              self, self.props, other.props)
        deleted_props = set(self.props.keys()) - set(other.props.keys())
        for key in deleted_props:
            del self.props[key]

        for key, val in other.props.items():
            oldval = self.props.get(key)
            if not oldval:
                self.props[key] = val
                continue
            if oldval == val:
                continue
            if key[:3] == "on_":
                # logger.debug("Do not replace on_ props: %s", key)
                continue
            # logger.debug("Replace props: %s", key)
            self.props[key] = val

    def queryElement(self, query):
        if self.matchCssSelector(query):
            return self
        for child in self.children:
            ret = child.queryElement(query)
            if ret:
                return ret

    def preorderTraversal(self):
        yield self
        for child in self.children:
            yield from child.preorderTraversal()

    def getStyle(self, csskey: StyleProperty, default=None):
        if csskey == "paddingTop":
            val = self.__getStyle(csskey)
            if val is not None:
                return val
            padding = self.__getStyle("padding")
            if isinstance(padding, int):
                return padding
            if padding:
                padding = padding.split()
                return int(padding[0])
            return default
        if csskey == "paddingRight":
            val = self.__getStyle(csskey)
            if val is not None:
                return val
            padding = self.__getStyle("padding")
            if isinstance(padding, int):
                return padding
            if padding:
                padding = padding.split()
                if len(padding) >= 2:
                    return int(padding[1])
                return int(padding[0])
            return default
        if csskey == "paddingBottom":
            val = self.__getStyle(csskey)
            if val is not None:
                return val
            padding = self.__getStyle("padding")
            if isinstance(padding, int):
                return padding
            if padding:
                padding = padding.split()
                if len(padding) >= 3:
                    return int(padding[2])
                return int(padding[0])
            return default
        if csskey == "paddingLeft":
            val = self.__getStyle(csskey)
            if val is not None:
                return val
            padding = self.__getStyle("padding")
            if isinstance(padding, int):
                return padding
            if padding:
                padding = padding.split()
                if len(padding) >= 4:
                    return int(padding[3])
                if len(padding) >= 2:
                    return int(padding[1])
                return int(padding[0])
            return default

        return self.__getStyle(csskey, default)

    def __getStyle(self, csskey: StyleProperty, default=None):

        style = self.props.get("style")
        if style:
            value = style.get(csskey)
            if value:
                return value

        pri = 0
        value = None
        for selector, style in self.document.css.items():
            npri = self.matchCssSelector(selector)
            if npri > pri:
                value = style.get(csskey) or value
                pri = npri
        if value:
            return value
        if csskey in INHERITABLE_STYLES and self.parent:
            return self.parent.getStyle(csskey)

        return default

    def matchCssSelector(self, selector: str) -> int:
        """
        Very simple selectors. Simple classnames, type and ids. Not nested.

        Returns 0 if no match, if not a priority number, the 
        highest more priority

        Priority based on https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity
        """
        if not selector or selector == "*":
            return 1

        match = CSS_SELECTOR_RE.match(selector)
        pri = 0
        if not match:
            logger.warning("Invalid selector")
            return 0
        mdict = match.groupdict()
        if mdict["name"]:
            if mdict["name"] != self.name:
                return 0
            pri += 1
        if mdict["id"]:
            if mdict["id"][1:] != self.props.get("id"):
                return 0
            pri += 10000
        if mdict["class"]:
            class_name = self.props.get("className", "").split(" ")
            classes = mdict["class"].split(".")[1:]
            for clss in classes:
                if clss not in class_name:
                    return 0
            pri += 10*len(classes)
        if mdict["pseudo"]:
            pri += 1
            for pseudo in mdict["pseudo"].split(":")[1:]:
                if pseudo == "focus":
                    # current focused element maybe a distant child, must check all parents
                    item = self.document.currentFocusedElement
                    is_focused = False
                    while item:
                        if item == self:
                            is_focused = True
                        item = item.parent
                    if not is_focused:
                        return 0
                else:
                    logger.warning("Unknown Pseudo Selector: %s", pseudo)

        return pri

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
        min_width = self.getStyle("minWidth") or min_width
        min_height = self.getStyle("minHeight") or min_height
        max_width = self.getStyle("maxWidth") or max_width
        max_height = self.getStyle("maxHeight") or max_height

        width = self.calculateProportion(max_width, self.getStyle("width"))
        if width:  # if there is a desired width, it is used
            min_width = width
            max_width = width
        height = self.calculateProportion(max_height, self.getStyle("height"))
        if height:  # if there is a desired height, it is used
            min_height = height
            max_height = height

        max_width_pb = max_width - (
            self.getStyle("paddingLeft", 0) +
            self.getStyle("paddingRight", 0) +
            self.getStyle("border", 0)*2
        )
        max_height_pb = max_height - (
            self.getStyle("paddingTop", 0) +
            self.getStyle("paddingBottom", 0) +
            self.getStyle("border", 0)*2
        )

        direction = self.getStyle("flex-direction")
        if direction == "row":
            width, height = self.calculateLayoutSizesRow(
                0, 0, max_width_pb, max_height_pb)
        else:  # default for even unknown is vertical stack
            width, height = self.calculateLayoutSizesColumn(
                0, 0, max_width_pb, max_height_pb)

        width = min(max_width, max(width, min_width))
        height = min(max_height, max(height, min_height))

        self.layout.width = width
        self.layout.height = height

        return (width, height)

    def split_fixed_variable_children(self):
        children_grow = [
            (x, x.getStyle("flex-grow"))
            for x in self.children
        ]
        fixed = [x for x in children_grow if not x[1]]
        variable = [x for x in children_grow if x[1]]
        return fixed, variable

    def calculateLayoutSizesColumn(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = min_width
        height = 0
        for child, _grow in fixed_children:

            child.calculateLayoutSizes(
                0, 0,
                max_width, max_height
            )

            childposition = child.getStyle("position")
            if childposition != "absolute":
                height += child.layout.height
                width = max(width, child.layout.width)
                max_height = max_height-child.layout.height
                min_width = max(min_width, width)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_height / quants
            for child, grow in variable_children:
                cheight = math.floor(quant_size * grow)
                child.calculateLayoutSizes(
                    min_width, cheight,  # fixed height
                    max_width, cheight,
                )
                childposition = child.getStyle("position")
                if childposition != "absolute":
                    height += child.layout.height
                    width = max(width, child.layout.width)
                    max_height = max_height-child.layout.height
                    min_width = max(min_width, width)

        # this is equivalent to align items stretch
        for child in self.children:
            childposition = child.getStyle("position")
            if childposition != "absolute":
                child.layout.width = width
        return (width, height)

    def calculateLayoutSizesRow(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = 0
        height = min_height

        for child, _grow in fixed_children:
            child.calculateLayoutSizes(
                0, 0,
                max_width, max_height
            )
            width += child.layout.width
            height = max(height, child.layout.height)
            max_width = max_width-child.layout.width
            min_height = max(min_height, height)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_width / quants
            for child, grow in variable_children:
                cwidth = math.floor(quant_size * grow)
                child.calculateLayoutSizes(
                    cwidth, min_width,   # fixed width
                    cwidth, max_width,
                )
                width += child.layout.width
                height = max(height, child.layout.height)
                max_width = max_width-child.layout.width
                min_height = max(min_height, height)

        # this is equivalent to align items stretch
        for child in self.children:
            child.layout.height = height
        return (width, height)

    def calculateLayoutPosition(self):
        """
        Calculates the position of children: same as parent + sizeof prev childs.
        """

        x = (
            self.layout.x +
            self.getStyle("paddingLeft", 0) +
            self.getStyle("border", 0)
        )

        y = (
            self.layout.y +
            self.getStyle("paddingTop", 0) +
            self.getStyle("border", 0)
        )

        # print(self, x, y)
        child: Component
        for child in self.children:
            childposition = child.getStyle("position")

            if childposition == "absolute":
                child.layout.y = child.getStyle("top") or 0
                child.layout.x = child.getStyle("left") or 0
                child.calculateLayoutPosition()
            else:
                child.layout.y = y
                child.layout.x = x
                child.calculateLayoutPosition()
                if self.getStyle("flex-direction") == "row":
                    x += child.layout.width
                else:
                    y += child.layout.height

    def prettyPrint(self, indent=0):
        def printable(v):
            if callable(v):
                return '[callable]'
            if isinstance(v, str):
                return f'"{v}"'
            return str(v)
        props = ' '.join([
            f"{k}={printable(v)}"
            for k, v in self.props.items()
            if k != 'children'
        ])
        state = self.state and ' '.join([
            f"{k}={printable(v)}"
            for k, v in self.state.items()
            if k != 'children'
        ]) or ""
        if self.children:
            print(f'{" " * indent}<{self.name} {props} {state}>')
            for child in self.children:
                child.prettyPrint(indent+2)
            print(f'{" " * indent}</{self.name}>')
        else:
            print(f'{" " * indent}<{self.name} {props} {state}/>')


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
            renderer.strokeStyle = self.getStyle(
                "borderColor") or self.getStyle("color")
            border = self.getStyle("border")
            if border:
                renderer.lineWidth = self.getStyle("borderWidth", 0)
                renderer.fillStroke(
                    self.layout.x, self.layout.y,
                    self.layout.width, self.layout.height,
                )
            else:
                renderer.fillRect(
                    self.layout.x, self.layout.y,
                    self.layout.width, self.layout.height,
                )
        super().paint(renderer)


class Text(Paintable):
    def __init__(self, text, **props):
        super().__init__(text=text, **props)

    def paint(self, renderer: Renderer):
        text = self.props.get("text")
        if text:
            color = self.getStyle("color")
            if color:
                renderer.strokeStyle = color
            background = self.getStyle("background")
            if background:
                renderer.fillStyle = background
            fontWeight = self.getStyle("font-weight")
            fontDecoration = self.getStyle("font-decoration")
            fontStyle = self.getStyle("font-style")

            renderer.fillText(
                str(text),
                self.layout.x, self.layout.y,
                bold=fontWeight == "bold",
                underline=fontDecoration == "underline",
                italic=fontStyle == "italic",
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
