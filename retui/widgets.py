from retui.component import Paintable, Text

div = Paintable
div.__name__ = "div"
span = Paintable
span.__name__ = "span"


class header(Paintable):
    """
    Just uses the widget name for classes. Children are the children.

    This is a common pattern, instead of setting classes for 
    custom elements, just use the element name
    """
    pass


class select(Paintable):
    state = {
        "open": False
    }

    def handleOpenClose(self):
        self.setState({"open": not self.state["open"]})

    def render(self):
        if self.state["open"]:
            return Text(
                on_click=self.handleOpenClose, text=f"*{self.props.get('label')}*"
            )
        else:
            return Text(
                on_click=self.handleOpenClose, text=f" {self.props.get('label')} "
            )


class option(Paintable):
    pass


class Body(Paintable):
    pass


class footer(Paintable):
    pass
