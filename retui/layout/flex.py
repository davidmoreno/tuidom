from .layout import Layout


class LayoutFlex(Layout):
    def split_fixed_variable_children(self) -> tuple[list[Layout], list[Layout]]:
        children_grow = [(x, x.node.getStyle("flex-grow")) for x in self.children]
        fixed = [x for x in children_grow if not x[1]]
        variable = [x for x in children_grow if x[1]]
        return fixed, variable
