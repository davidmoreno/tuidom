from dataclasses import dataclass
import itertools
import logging
import math

from retui import css
from .events import EventKeyPress, HandleEventTrait
from .renderer import Renderer

logger = logging.getLogger(__name__)


@dataclass
class Layout:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def inside(self, x, y):
        return (self.x <= x < (self.x + self.width)) and (
            self.y <= y < (self.y + self.height)
        )

    def as_clipping(self):
        return ((self.x, self.y), (self.x + self.width, self.y + self.height))


class Component:
    """
    Props:
    * style -- Dict of styles | another component to get styles from it. See select
    * className - List of classnames
    """

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
        style = props.get("style")
        if style and isinstance(style, dict):
            props = {**props, "style": css.StyleSheet.normalizeStyle(props["style"])}
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
            return (
                f"<{self.name}{ids} {self.serialid}>...{len(children)}...</{self.name}>"
            )

    def componentDidMount(self):
        pass

    def render(self):
        return self.props.get("children", [])

    def paint(self, renderer: Renderer):
        zIndex = self.getStyle("zIndex")
        if zIndex is not None:
            renderer.addZIndex(zIndex)
        for child in self.children:
            child.paint(renderer)
        if zIndex is not None:
            renderer.addZIndex(-zIndex)

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
                item.props["children"] = self.normalize(item.props.get("children", []))
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
            nextchildren = self.reconcile(self, self.children, children)

            self.children = nextchildren

        # logger.debug("Materialized %s -> %s", self,
        #              self.children)
        # rec materialize
        for child in self.children:
            child.materialize()

        if not self.__mounted:
            self.__mounted = True
            self.componentDidMount()

        return self

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

    def isFocusable(self):
        if not isinstance(self, HandleEventTrait):
            return False
        for key in self.props.keys():
            if key.startswith("on_"):
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

    def queryElement(self, query: css.Selector | str):
        if isinstance(query, str):
            query = css.Selector(query)
        if query.match(self):
            return self
        for child in self.children:
            ret = child.queryElement(query)
            if ret:
                return ret

    def queryParent(self, query: css.Selector | str):
        """
        Query parents until finds an element that matches (me included)
        """
        if isinstance(query, str):
            query = css.Selector(query)
        if query.match(self):
            return self
        for parent in self.parentTraversal():
            ret = parent.queryElement(query)
            if ret:
                return ret
        return None

    def preorderTraversal(self):
        yield self
        for child in self.children:
            yield from child.preorderTraversal()

    def parentTraversal(self):
        el = self
        while el:
            yield el
            el = el.parent

    def findElementAt(self, x: int, y: int, z: int = 0) -> tuple[int, "Self"]:
        """
        Finds which element is at that position.
        """
        zIndex = (self.getStyle("zIndex") or 0) + z
        ret = (-1, None)
        if self.layout.inside(x, y):
            ret = (zIndex, self)

        for child in self.children:
            rc = child.findElementAt(x, y, zIndex)
            if rc[0] >= ret[0]:
                ret = rc
        return ret

    def getStyle(self, csskey: css.StyleProperty, default=None):
        style = self.props.get("style", {})
        # allow refer style to another component
        if isinstance(style, Component):
            return style.getStyle(csskey, default)
        if csskey in style:
            return style[csskey]
        value = self.document.stylesheet.getStyle(self, csskey)
        if value:
            return value
        if csskey in css.INHERITABLE_STYLES and self.parent:
            return self.parent.getStyle(csskey, default)
        return default

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

    def calculateLayoutSizes(
        self, min_width, min_height, max_width, max_height, clip=True
    ):
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

        border = self.getStyle("border", 0)
        if border:
            border = 2

        max_width_pb = max_width - (
            self.getStyle("paddingLeft", 0) + self.getStyle("paddingRight", 0) + border
        )
        max_height_pb = max_height - (
            self.getStyle("paddingTop", 0) + self.getStyle("paddingBottom", 0) + border
        )

        direction = self.getStyle("flex-direction")
        if direction == "row":
            width, height = self.calculateLayoutSizesRow(
                0, 0, max_width_pb, max_height_pb
            )
        else:  # default for even unknown is vertical stack
            width, height = self.calculateLayoutSizesColumn(
                0, 0, max_width_pb, max_height_pb
            )

        width += (
            self.getStyle("paddingLeft", 0)
            + self.getStyle("paddingRight", 0)
            + (self.getStyle("border", 0) and 2)
        )
        height += (
            self.getStyle("paddingTop", 0)
            + self.getStyle("paddingBottom", 0)
            + (self.getStyle("border", 0) and 2)
        )

        if clip:
            width = min(max_width, max(width, min_width))
            height = min(max_height, max(height, min_height))

            self.layout.width = width
            self.layout.height = height

        return (width, height)

    def split_fixed_variable_children(self):
        children_grow = [(x, x.getStyle("flex-grow")) for x in self.children]
        fixed = [x for x in children_grow if not x[1]]
        variable = [x for x in children_grow if x[1]]
        return fixed, variable

    def calculateLayoutSizesColumn(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = min_width
        height = 0
        for child, _grow in fixed_children:
            child.calculateLayoutSizes(0, 0, max_width, max_height)

            childposition = child.getStyle("position")
            if childposition != "absolute":
                height += child.layout.height
                width = max(width, child.layout.width)
                max_height = max_height - child.layout.height
                min_width = max(min_width, width)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_height / quants
            for child, grow in variable_children:
                cheight = math.floor(quant_size * grow)
                child.calculateLayoutSizes(
                    min_width,
                    cheight,  # fixed height
                    max_width,
                    cheight,
                )
                childposition = child.getStyle("position")
                if childposition != "absolute":
                    height += child.layout.height
                    width = max(width, child.layout.width)
                    max_height = max_height - child.layout.height
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
            child.calculateLayoutSizes(0, 0, max_width, max_height)
            width += child.layout.width
            height = max(height, child.layout.height)
            max_width = max_width - child.layout.width
            min_height = max(min_height, height)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_width / quants
            for child, grow in variable_children:
                cwidth = math.floor(quant_size * grow)
                child.calculateLayoutSizes(
                    cwidth,
                    min_width,  # fixed width
                    cwidth,
                    max_width,
                )
                width += child.layout.width
                height = max(height, child.layout.height)
                max_width = max_width - child.layout.width
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
            self.layout.x
            + self.getStyle("paddingLeft", 0)
            + (self.getStyle("border", 0) and 1)
        )

        y = (
            self.layout.y
            + self.getStyle("paddingTop", 0)
            + (self.getStyle("border", 0) and 1)
        )

        # print(self, x, y)
        child: Component
        def_align = self.getStyle("align-items") or "start"
        dir_row = self.getStyle("flex-direction") == "row"
        for child in self.children:
            align = child.getStyle("align-self", def_align)
            justify = child.getStyle("justify-self", def_align)
            childposition = child.getStyle("position")

            if childposition == "absolute":
                px = 0  # should get it from parent with relative
                py = 0
                if dir_row:
                    if align == "start":
                        child.layout.y = py
                    elif align == "center":
                        child.layout.y = (
                            py + (self.layout.height - child.layout.height) // 2
                        )
                    if justify == "center":
                        child.layout.x = (
                            py + (self.layout.height - child.layout.height) // 2
                        )
                else:
                    if align == "start":
                        child.layout.x = px
                    elif align == "center":
                        child.layout.x = (
                            px + (self.layout.width - child.layout.width) // 2
                        )
                    if justify == "center":
                        child.layout.y = (
                            py + (self.layout.height - child.layout.height) // 2
                        )
                child.layout.y += (
                    self.calculateProportion(self.layout.width, child.getStyle("top"))
                    or 0
                )
                child.layout.x += (
                    self.calculateProportion(self.layout.width, child.getStyle("left"))
                    or 0
                )
                child.calculateLayoutPosition()
            else:
                child.layout.y = y
                child.layout.x = x

                if dir_row:
                    if align == "start":
                        child.layout.y = y
                    elif align == "end":
                        child.layout.y = (
                            self.layout.y + self.layout.height - child.layout.height
                        )
                    elif align == "center":
                        child.layout.y = (
                            self.layout.y
                            + (self.layout.height - child.layout.height) // 2
                        )
                else:
                    if align == "start":
                        child.layout.x = x
                    elif align == "end":
                        child.layout.x = (
                            self.layout.x + self.layout.width - child.layout.width
                        )
                    elif align == "center":
                        child.layout.x = (
                            self.layout.x
                            + (self.layout.width - child.layout.width) // 2
                        )
                child.calculateLayoutPosition()
                if dir_row:
                    x += child.layout.width
                else:
                    y += child.layout.height

    def prettyPrint(self, indent=0):
        def printable(v):
            if callable(v):
                return "[callable]"
            if isinstance(v, str):
                return f'"{v}"'
            return str(v)

        props = " ".join(
            [f"{k}={printable(v)}" for k, v in self.props.items() if k != "children"]
        )
        state = (
            self.state
            and " ".join(
                [
                    f"{k}={printable(v)}"
                    for k, v in self.state.items()
                    if k != "children"
                ]
            )
            or ""
        )
        pseudo = []
        if self.document.currentFocusedElement:
            for el in self.document.currentFocusedElement.parentTraversal():
                if self == el:
                    pseudo.append(":focus")
                    break
        if self == self.document.currentOpenElement:
            pseudo.append(":open")
        pseudo = " ".join(pseudo)
        if self.children:
            print(f'{" " * indent}<{self.name} {props} {state} {pseudo}>')
            for child in self.children:
                child.prettyPrint(indent + 2)
            print(f'{" " * indent}</{self.name}>')
        else:
            print(f'{" " * indent}<{self.name} {props} {state} {pseudo}/>')


def renderer_clipping(func):
    def wrapper(self: Component, renderer: Renderer):
        layout = self.layout

        renderer.pushClipping(layout.as_clipping())
        try:
            func(self, renderer)
        finally:
            renderer.popClipping()

    wrapper.__name__ = func.__name__
    return wrapper


class Paintable(HandleEventTrait, Component):
    """
    This component can be painted with the given renderer
    """

    def paint(self, renderer: Renderer):
        color = self.getStyle("color")
        if color:
            renderer.setForeground(color)
        background = self.getStyle("background")
        if background:
            renderer.setBackground(background)
            border = self.getStyle("border")

            if border:
                renderer.setForeground(
                    self.getStyle("borderColor") or self.getStyle("color")
                )
                renderer.setLineWidth(self.getStyle("border", 0))
                renderer.fillStroke(
                    self.layout.x,
                    self.layout.y,
                    self.layout.width,
                    self.layout.height,
                )
            else:
                renderer.fillRect(
                    self.layout.x,
                    self.layout.y,
                    self.layout.width,
                    self.layout.height,
                )

        super().paint(renderer)


class Text(Paintable):
    def __init__(self, text, **props):
        super().__init__(text=text, **props)

    def getStyle(self, csskey: css.StyleProperty, default=None):
        return self.parent.getStyle(csskey, default)

    def paint(self, renderer: Renderer):
        text = self.props.get("text")
        if text:
            color = self.getStyle("color")
            if color:
                renderer.setForeground(color)
            background = self.getStyle("background")
            if background:
                renderer.setBackground(background)
            fontWeight = self.getStyle("font-weight")
            fontDecoration = self.getStyle("font-decoration")
            fontStyle = self.getStyle("font-style")

            renderer.fillText(
                str(text),
                self.layout.x,
                self.layout.y,
                bold=fontWeight == "bold",
                underline=fontDecoration == "underline",
                italic=fontStyle == "italic",
            )

    def calculateLayoutSizes(self, min_width, min_height, max_width, max_height):
        text = self.props.get("text", "").split("\n")
        height = min(1, len(text))
        width = max(len(x) for x in text)
        if width < min_width:
            width = min_width
        if width > max_width:
            width = max_width
        if height < min_height:
            height = min_height
        if height > max_height:
            height = max_height

        self.layout.width = width
        self.layout.height = height

        return (width, height)


class Scrollable(Paintable):
    """
    This widget can have scrollbars
    """

    state = {
        "x": 0,
        "y": 0,
    }
    innerLayout = Layout()

    def __init__(self, **kwargs):
        super().__init__(on_keypress=self.handleKeyPress, **kwargs)

    def handleKeyPress(self, ev: EventKeyPress):
        match ev.keycode:
            case "DOWN":
                maxy = self.innerLayout.height - self.layout.height
                self.setState({"y": min(self.state["y"] + 1, maxy)})
                ev.stopPropagation = True
            case "UP":
                self.setState({"y": max(self.state["y"] - 1, 0)})
                ev.stopPropagation = True

            case "LEFT":
                self.setState({"x": self.state["x"] + 1})
                ev.stopPropagation = True
            case "RIGHT":
                self.setState({"x": self.state["x"] - 1})
                ev.stopPropagation = True

    def calculateLayoutSizes(self, min_width, min_height, max_width, max_height):
        w, h = super().calculateLayoutSizes(0, 0, 128, 128, clip=False)
        self.innerLayout.width = w
        self.innerLayout.height = h
        self.layout.width = max_width
        self.layout.height = max_height
        return (self.layout.width, self.layout.height)

    def paint(self, renderer: Renderer):
        # first fill background
        background = self.getStyle("background")
        renderer.setBackground(background)
        renderer.fillRect(
            self.layout.x,
            self.layout.y,
            self.layout.width,
            self.layout.height,
        )

        renderer.pushTranslate((-self.state["x"], -self.state["y"]))
        renderer.pushClipping(self.layout.as_clipping())
        try:
            super().paint(renderer)
        finally:
            renderer.popClipping()
            renderer.popTranslate()

        renderer.setBackground(background)
        foreground = self.getStyle("color")
        renderer.setForeground(foreground)

        # scrollbar = "▲┃█▼◀━█▶"
        scrollbar = "▕▕█▕▁▁▄▁"
        scrollbar = "┃┃█┃▁▁▄▁"
        # scrollbar = "  █   █ "
        # scrollbar = "┃┃█┃━━◼━"
        has_scrollbar_y = True  # self.getStyle("overflowY") == "scroll"
        if has_scrollbar_y:
            x = self.layout.x + self.layout.width - 1
            miny = self.layout.y
            maxy = self.layout.y + self.layout.height - 1
            oh = self.layout.height
            ih = self.innerLayout.height

            ty = self.state["y"]
            by = self.state["y"] + 1
            if miny + 2 < maxy:
                renderer.fillText(scrollbar[0], x, miny)
                for y in range(miny + 1, maxy):
                    renderer.fillText(scrollbar[1], x, y)
                for y in range(miny + ty, miny + by):
                    renderer.fillText(scrollbar[2], x, y)

                renderer.fillText(scrollbar[3], x, maxy)

        has_scrollbar_x = True  # self.getStyle("overflowX") == "scroll"
        if has_scrollbar_x:
            y = self.layout.y + self.layout.height - 1
            minx = self.layout.x
            maxx = self.layout.x + self.layout.width - 1

            tx = -self.state["x"]
            bx = -self.state["x"] + 1
            if minx + 2 < maxx:
                renderer.fillText(scrollbar[4], minx, y)
                for x in range(minx + 1, maxx):
                    renderer.fillText(scrollbar[5], x, y)
                for x in range(minx + tx, minx + bx):
                    renderer.fillText(scrollbar[6], x, y)

                renderer.fillText(scrollbar[7], maxx, y)
