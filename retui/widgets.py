from retui.component import Paintable, Text
from retui.events import EventFocus, EventKeyPress, HandleEventTrait


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


class option(Paintable):
    pass


class body(Paintable):
    pass


class footer(Paintable):
    pass


class button(Paintable):
    pass


class input(Paintable):
    cursor = (0, 0)

    state = {
        "position": 0,
        "value": "this is a test",
    }

    def getValue(self):
        if 'value' in self.props:
            return self.props["value"]
        return self.state["value"]

    def handleKeyPress(self, ev: EventKeyPress):
        letter = ev.keycode
        value = self.getValue()
        pos = self.state["position"]
        match letter:
            case "LEFT":
                pos = self.state["position"]
                pos = max(0, pos-1)
            case "RIGHT":
                pos = min(len(value), pos+1)
            case "CONTROL-LEFT":
                pos = self.state["position"]-1
                # first skip spaces, then a word
                while pos > 0 and value[pos] == ' ':
                    pos -= 1
                while pos > 0 and value[pos] != ' ':
                    pos -= 1
                if value[pos] == ' ':
                    pos += 1
            case "CONTROL-RIGHT":
                pos = self.state["position"]+1
                mpos = len(value)
                pos = min(mpos, pos)
                print(1, pos)
                # skip spaces, then word
                while pos < mpos and value[pos] == ' ':
                    print(2, pos, value[pos], value[pos] == ' ')
                    pos += 1
                while pos < mpos and value[pos] != ' ':
                    print(3, pos)
                    pos += 1
                pos = min(mpos, pos)
            case "START":
                pos = 0
            case "END":
                pos = len(value)

            case "DEL":
                pos = self.state["position"]
                pre = value[:pos-1]
                post = value[pos:]
                value = f"{pre}{post}"
                pos -= 1

            case "SUPR":
                value = self.getValue()
                pos = self.state["position"]
                pre = value[:pos]
                post = value[pos+1:]
                value = f"{pre}{post}"
            case _:
                if len(letter) == 1:
                    pos = self.state["position"]
                    pre = value[:pos]
                    post = value[pos:]
                    value = f"{pre}{letter}{post}"
                    pos += 1
                else:
                    return  # do nothing, not understand key

        ev.stopPropagation = True

        self.setState({"position": pos, "value": value})
        on_change = self.props.get("on_change")
        self.cursor = (pos, 0)
        if not on_change:
            return
        on_change(value)

    def render(self):
        return Text(self.getValue(), on_keypress=self.handleKeyPress)


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
