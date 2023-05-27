from dataclasses import dataclass
import math

import logging
import retui

logger = logging.getLogger(__name__)


@dataclass
class Layout:
    node: "retui.component.Component"
    children: list["retui.component.Layout"] | None = None

    dirty: bool = True
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

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
        return f"<{self.node.name} {self.__class__.__name__} {self.as_clipping()}>"

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

    def calculateSize(self, min_width, min_height, max_width, max_height, clip=True):
        """
        Calculates the layout inside the desired rectangle.

        Given the given constraints, sets own size.
        Once we have the size, position is calculated later.
        """
        self.relayout_if_dirty()
        getStyle = self.node.getStyle

        min_width = getStyle("minWidth") or min_width
        min_height = getStyle("minHeight") or min_height
        max_width = getStyle("maxWidth") or max_width
        max_height = getStyle("maxHeight") or max_height

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

        direction = getStyle("flex-direction")
        if direction == "row":
            width, height = self.calculateSizeRow(0, 0, max_width_pb, max_height_pb)
        else:  # default for even unknown is vertical stack
            width, height = self.calculateSizeColumn(0, 0, max_width_pb, max_height_pb)

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

        if clip:
            width = min(max_width, max(width, min_width))
            height = min(max_height, max(height, min_height))

            self.width = width
            self.height = height

        return (width, height)

    def split_fixed_variable_children(self):
        children_grow = [(x, x.node.getStyle("flex-grow")) for x in self.children]
        fixed = [x for x in children_grow if not x[1]]
        variable = [x for x in children_grow if x[1]]
        return fixed, variable

    def calculateSizeColumn(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = min_width
        height = 0
        for child, _grow in fixed_children:
            child.calculateSize(0, 0, max_width, max_height)

            childposition = child.node.getStyle("position")
            if childposition != "absolute":
                height += child.height
                width = max(width, child.width)
                max_height = max_height - child.height
                min_width = max(min_width, width)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_height / quants
            for child, grow in variable_children:
                cheight = math.floor(quant_size * grow)
                child.calculateSize(
                    min_width,
                    cheight,  # fixed height
                    max_width,
                    cheight,
                )
                childposition = child.node.getStyle("position")
                if childposition != "absolute":
                    height += child.height
                    width = max(width, child.width)
                    max_height = max_height - child.height
                    min_width = max(min_width, width)

        # this is equivalent to align items stretch
        for child in self.children:
            childposition = child.node.getStyle("position")
            if childposition != "absolute":
                child.width = width
        return (width, height)

    def calculateSizeRow(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = 0
        height = min_height

        for child, _grow in fixed_children:
            child.calculateSize(0, 0, max_width, max_height)
            width += child.width
            height = max(height, child.height)
            max_width = max_width - child.width
            min_height = max(min_height, height)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = max_width / quants
            for child, grow in variable_children:
                cwidth = math.floor(quant_size * grow)
                child.calculateSize(
                    cwidth,
                    min_width,  # fixed width
                    cwidth,
                    max_width,
                )
                width += child.width
                height = max(height, child.height)
                max_width = max_width - child.width
                min_height = max(min_height, height)

        # this is equivalent to align items stretch
        for child in self.children:
            child.height = height
        return (width, height)

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

        # print(self, x, y)
        child: "retui.component.Component"
        def_align = self.node.getStyle("align-items")
        dir_row = self.node.getStyle("flex-direction") == "row"
        for child in self.children:
            align = child.node.getStyle("align-self", def_align)
            justify = child.node.getStyle("justify-self", def_align)
            childposition = child.node.getStyle("position")

            if childposition == "absolute":
                self.layoutPosisitonAbsolute(x, y, dir_row, align, justify)
            else:
                child.y = y
                child.x = x

                if dir_row:
                    if align == "start":
                        child.y = y
                    elif align == "end":
                        child.y = self.y + self.height - child.height
                    elif align == "center":
                        child.y = self.y + (self.height - child.height) // 2
                else:
                    if align == "start":
                        child.x = x
                    elif align == "end":
                        child.x = self.x + self.width - child.width
                    elif align == "center":
                        child.x = self.x + (self.width - child.width) // 2
                child.calculatePosition()
                if dir_row:
                    x += child.width
                else:
                    y += child.height

    def layoutPosisitonAbsolute(self, x, y, dir_row, align, justify):
        px = 0  # should get it from parent with relative
        py = 0
        from_top = False
        from_left = False
        parent = self.node.parent.layout
        if dir_row:
            if align == "start":
                self.y = py
            elif align == "center":
                self.y = py + (parent.height - self.height) // 2
            else:
                from_top = True
            if justify == "center":
                self.x = py + (parent.height - self.height) // 2
            else:
                from_left = True
        else:
            if align == "start":
                self.x = px
            elif align == "center":
                self.x = px + (parent.width - self.width) // 2
            else:
                from_left = True
            if justify == "center":
                self.y = py + (parent.height - self.height) // 2
            else:
                from_top = True
        if from_left:
            left = self.node.getStyle("left")
            self.x = (
                parent.calculateProportion(parent.width, left)
                if left is not None
                else x
            )
        if from_top:
            top = self.node.getStyle("top")
            self.y = (
                parent.calculateProportion(parent.height, top) if top is not None else y
            )
        # self.calculatePosition()
