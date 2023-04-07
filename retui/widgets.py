from retui import component


class MenuBar(component.Component):
    """
    Just uses the widget name for classes. Children are the children.

    This is a common pattern, instead of setting classes for 
    custom elements, just use the element name
    """
    pass


class Menu(component.Component):
    state = {
        "open": False
    }

    def handleOpenClose(self):
        self.setState({"open": not self.state["open"]})

    def render(self):
        if self.state["open"]:
            return component.Text(
                on_click=self.handleOpenClose, text=f"*{self.props.get('label')}*"
            )
        else:
            return component.Text(
                on_click=self.handleOpenClose, text=self.props.get("label")
            )


class MenuItem(component.Component):
    pass


class Body(component.Component):
    pass


class Footer(component.Component):
    pass
