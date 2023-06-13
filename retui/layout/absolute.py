from retui.layout.layout import Layout


class LayoutAbsolute(Layout):
    def __init__(self, node: "retui.Component", innerLayout: Layout):
        super().__init__(node)
        self.innerLayout = innerLayout

    def getRelativeParent(self):
        # this should look for the first relative... btm direct to document
        return self.node.document.layout

    def calculateSize(self, min_width, min_height, max_width, max_height):
        parent = self.getRelativeParent()

        self.innerLayout.calculateSize(0, 0, parent.width, parent.height)

    def calculatePosition(self):
        px = 0  # should get it from parent with relative
        py = 0
        from_top = False
        from_left = False

        parent = self.getRelativeParent()

        dir_row = self.node.getStyle("flex-direction", "column") == "row"
        align = self.node.getStyle("align", "start")
        justify = self.node.getStyle("justify", "start")

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
                else self.x
            )
        if from_top:
            top = self.node.getStyle("top")
            self.y = (
                parent.calculateProportion(parent.height, top)
                if top is not None
                else self.y
            )

        self.innerLayout.calculateChildrenPosition(self.x, self.y)

    def prettyPrint(self, indent=0):
        print(" " * indent, self, "[absolute]")
        return self.innerLayout.prettyPrint(indent + 2)
