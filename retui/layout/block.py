from retui.layout.layout import Layout


class LayoutBlock(Layout):
    def calculateChildrenPosition(self, x: int, y: int):
        line_height = 0
        max_x = x + self.width
        min_x = x
        for child in self.children:
            # print(
            #     child,
            #     min_x,
            #     x,
            #     y,
            #     x + child.width,
            #     max_x,
            #     y + child.height,
            # )
            # first element each row can overflow, so just take it
            if x == min_x:
                child.x = min_x
                child.y = y
                line_height = child.height
                x += child.width

            # overflow
            elif (x + child.width) > max_x:
                y += line_height

                child.x = min_x
                child.y = y
                x = min_x + child.width + 1  # add one extra space
                line_height = child.height
            # add to the same row
            else:
                child.x = x
                child.y = y
                x += child.width
                line_height = max(line_height, child.height)

    def calculateChildrenSize(self, min_width, min_height, max_width, max_height):
        width = 0
        height = 0
        mwidth = 0
        line_height = 0
        for child in self.children:
            child.calculateSize(min_width, min_height, max_width, max_height)

            width += child.width

            line_height = max(line_height, child.height)
            mwidth = max(mwidth, width)

            # print(
            #     f"Get size: {child}, {width} / {mwidth} / {max_width} {height} / {line_height} / {max_height}"
            # )

            if width > max_width:
                height += line_height
                width = 0
                line_height = 0

        height += line_height

        return max_width, height
