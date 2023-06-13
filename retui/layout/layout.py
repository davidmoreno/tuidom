from dataclasses import dataclass, field
import math

import logging
import retui

logger = logging.getLogger(__name__)


@dataclass
class Layout:
    node: "retui.component.Component"
    children: list["retui.component.Layout"] = field(default_factory=list)

    dirty: bool = True
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def __init__(self, node, **kwargs):
        super().__init__()
        self.node = node
        node.layout = self

    def relayout_if_dirty(self):
        """
        Asserts that the layout is sane, and if not recalculates it all.

        Its not recursive as other calls later will ensure it relayouts as neeed.
        """
        if self.dirty:
            from retui.layout import create_layout

            self.children = [create_layout(child) for child in self.node.children]
            self.dirty = False

    def inside(self, x, y):
        return (self.x <= x < (self.x + self.width)) and (
            self.y <= y < (self.y + self.height)
        )

    def as_clipping(self):
        return ((self.x, self.y), (self.x + self.width, self.y + self.height))

    def prettyPrint(self, indent=0):
        print(" " * indent, self)
        for child in self.children:
            child.prettyPrint(indent + 2)

    def __str__(self):
        name = self.node.name
        nid = self.node.props.get("id")
        if nid:
            name = f"{name}#{nid}"
        return f"<{name} {self.__class__.__name__} pos ({self.x}, {self.y}) + size ({self.width}, {self.height})"

    def findElementAt(self, x: int, y: int, z: int = 0) -> tuple[int, "Self"]:
        """
        Finds which element is at that position.
        """
        zIndex = (self.node.getStyle("zIndex") or 0) + z
        ret = (-1, None)
        if self.inside(x, y):
            ret = (zIndex, self.node)

        for child in self.children:
            rc = child.findElementAt(x, y, zIndex)
            if rc[0] >= ret[0]:
                ret = rc
        return ret

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

    def calculateChildrenSize(
        self, min_width, min_height, max_width, max_height
    ) -> tuple[int, int]:
        """
        TO REIMPLEMENT. How the children sizes are calculated.

        Padding, and border already accounted for.
        """
        raise NotImplementedError(f"TO IMPLEMENT ({self.__class__.__name__})")

    def calculateSize(
        self, min_width: int, min_height: int, max_width: int, max_height: int
    ):
        """
        Calculates the layout inside the desired rectangle.

        Given the given constraints, sets own size.
        Once we have the size, position is calculated later.
        """
        self.relayout_if_dirty()
        getStyle = self.node.getStyle

        min_width = getStyle("min-width") or min_width
        min_height = getStyle("min-height") or min_height
        max_width = getStyle("max-width") or max_width
        max_height = getStyle("max-height") or max_height

        # print(f"{min_width} {max_width}")

        width = self.calculateProportion(max_width, getStyle("width"))
        if width:  # if there is a desired width, it is used
            min_width = width
            max_width = width
        height = self.calculateProportion(max_height, getStyle("height"))
        if height:  # if there is a desired height, it is used
            min_height = height
            max_height = height

        border = getStyle("border", 0)
        if border:
            border = 2

        max_width_pb = max_width - (
            getStyle("paddingLeft", 0) + getStyle("paddingRight", 0) + border
        )
        max_height_pb = max_height - (
            getStyle("paddingTop", 0) + getStyle("paddingBottom", 0) + border
        )

        width, height = self.calculateChildrenSize(0, 0, max_width_pb, max_height_pb)

        width += (
            getStyle("paddingLeft", 0)
            + getStyle("paddingRight", 0)
            + (getStyle("border", 0) and 2)
        )
        height += (
            getStyle("paddingTop", 0)
            + getStyle("paddingBottom", 0)
            + (getStyle("border", 0) and 2)
        )

        width = min(max_width, max(width, min_width))
        height = min(max_height, max(height, min_height))

        self.width = width
        self.height = height

    def calculateChildrenPosition(self, x: int, y: int):
        """
        TO IMPLEMENT.

        Calculates the position of chidren. Padding, border, scrollbars...
        all already acounted for in previous caller.
        """
        raise NotImplementedError(f"TO IMPLEMENT ({self.__class__.__name__})")

    def calculatePosition(self):
        """
        Calculates the position of children: same as parent + sizeof prev childs.
        """

        x = (
            self.x
            + self.node.getStyle("paddingLeft", 0)
            + (self.node.getStyle("border", 0) and 1)
        )

        y = (
            self.y
            + self.node.getStyle("paddingTop", 0)
            + (self.node.getStyle("border", 0) and 1)
        )

        self.calculateChildrenPosition(x, y)
