from retui.component import Paintable, Text
from retui.events import EventFocus, HandleEventTrait


class div(Paintable):
    pass


class span(Paintable):
    pass


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

    def handleOpenClose(self, ev):
        self.setState({"open": not self.state["open"]})

    def render(self):
        if self.state["open"]:
            return div()[
                Text(
                    className="relative",
                    on_click=self.handleOpenClose, text=f"*{self.props.get('label')}*",
                ),
                div(
                    className="absolute top-1 left-0 bg-seconadry text-secondary",
                    children=self.props.get("children", []),
                )
            ]
        else:
            return Text(
                on_click=self.handleOpenClose, text=f" {self.props.get('label')} "
            )


class option(Paintable):
    pass


class body(Paintable):
    pass


class footer(Paintable):
    pass


class button(Paintable):
    pass
