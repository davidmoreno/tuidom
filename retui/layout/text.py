from retui.layout import Layout


class LayoutText(Layout):
    def __init__(self, component):
        super().__init__(self, component)
        self.node = component

        self.children = []

    def calculateSize(self, min_width, min_height, max_width, max_height):
        text = self.node.props.get("text", "").split("\n")
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

        self.width = width
        self.height = height

        return (width, height)
