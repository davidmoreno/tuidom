from tuidom.tuidom import Layout


class LayoutAbsolute(Layout):
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
