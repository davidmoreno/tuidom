from retui.layout import Layout


class LayoutText(Layout):
    def __init__(self, component):
        super().__init__(component)
        self.node = component

        self.children = []

    def calculateChildrenPosition(self, x: int, y: int):
        """
        No children
        """
        return

    def calculateSize(self, min_width, min_height, max_width, max_height):
        self.width = len(self.node.props.get("text", ""))
        self.height = 1
