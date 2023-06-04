import math

from retui.layout.layout import Layout
from .flex import LayoutFlex


class LayoutFlexRow(LayoutFlex):
    def calculateChildrenSize(self, min_width, min_height, max_width, max_height):
        fixed_children, variable_children = self.split_fixed_variable_children()

        width = 0
        height = min_height
        child: Layout

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

    def calculateChildrenPosition(self, x: int, y: int):
        child: Layout
        def_align = self.node.getStyle("align-items")
        for child in self.children:
            align = child.node.getStyle("align-self", def_align)

            child.y = y
            child.x = x

            if align == "start":
                child.y = y
            elif align == "end":
                child.y = self.y + self.height - child.height
            elif align == "center":
                child.y = self.y + (self.height - child.height) // 2
            child.calculatePosition()

            x += child.width
