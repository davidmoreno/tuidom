import math

from retui.layout.layout import Layout
from .flex import LayoutFlex


class LayoutFlexColumn(LayoutFlex):
    def calculateChildrenSize(self, min_width, min_height, max_width, max_height):
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

    def calculateChildrenPosition(self, x: int, y: int):
        child: "retui.component.Component"
        def_align = self.node.getStyle("align-items")
        child: Layout
        for child in self.children:
            align = child.node.getStyle("align-self", def_align)

            child.y = y
            child.x = x

            if align == "start":
                child.x = x
            elif align == "end":
                child.x = self.x + self.width - child.width
            elif align == "center":
                child.x = self.x + (self.width - child.width) // 2
            child.calculatePosition()
            y += child.height
