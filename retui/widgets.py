from retui.component import Component, Paintable, Text
from retui.events import EventKeyPress, EventChange, EventMouseClick


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
        "value": "",
    }

    def maxRows(self):
        return 1

    def getValue(self) -> str:
        if "value" in self.props:
            return self.props["value"]
        return self.state["value"]

    def handleKeyPress(self, ev: EventKeyPress):
        letter = ev.keycode
        value = self.getValue()
        pos = self.state["position"]
        match letter:
            case "LEFT":
                pos = self.state["position"]
                pos = max(0, pos - 1)
            case "RIGHT":
                pos = min(len(value), pos + 1)
            case "UP":
                cursor = (self.cursor[0], max(0, self.cursor[1] - 1))
                pos = self.cursorToPosition(cursor, value)
            case "DOWN":
                cursor = (
                    self.cursor[0],
                    min(self.cursor[1] + 1, len(value.split("\n")) - 1),
                )
                pos = self.cursorToPosition(cursor, value)
            case "CONTROL-LEFT":
                pos = self.state["position"] - 1
                # first skip spaces, then a word
                while pos > 0 and value[pos] == " ":
                    pos -= 1
                while pos > 0 and value[pos] != " ":
                    pos -= 1
                if value[pos] == " ":
                    pos += 1
            case "CONTROL-RIGHT":
                pos = self.state["position"] + 1
                mpos = len(value)
                pos = min(mpos, pos)
                # skip spaces, then word
                while pos < mpos and value[pos] == " ":
                    print(2, pos, value[pos], value[pos] == " ")
                    pos += 1
                while pos < mpos and value[pos] != " ":
                    print(3, pos)
                    pos += 1
                pos = min(mpos, pos)
            case "START":
                pos = self.cursorToPosition((0, self.cursor[1]), value)
            case "END":
                vp = value[pos:]
                ex = vp.find("\n")
                if ex < 0:
                    pos += len(vp)
                else:
                    pos += ex

            case "DEL":
                pos = self.state["position"]
                pre = value[: pos - 1]
                post = value[pos:]
                value = f"{pre}{post}"
                pos -= 1

            case "SUPR":
                value = self.getValue()
                pos = self.state["position"]
                pre = value[:pos]
                post = value[pos + 1 :]
                value = f"{pre}{post}"
            case "ENTER":
                pos = self.state["position"]
                pre = value[:pos]
                post = value[pos:]
                rows = sum(1 for x in value if x == "\n") + 1
                if rows < self.maxRows():
                    value = f"{pre}\n{post}"
                    pos += 1
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

        self.cursor = self.getCursor(value[:pos])
        if not on_change:
            return
        on_change(value)

    def cursorToPosition(self, cursor, text):
        """
        Given a cursor and a text, return the real position
        """
        lines = text.split("\n")
        pos = cursor[0]
        pos += sum(len(x) + 1 for x in lines[: cursor[1]])
        return pos

    def getCursor(self, value: str):
        """
        Gets the cursor position for the given string.
        Normally send a partial string split at pos
        """
        lines = value.split("\n")
        posy = len(lines) - 1
        posx = len(lines[-1])

        # nposy = sum(1 for x in value if x == '\n')
        # px = value.rfind('\n')
        # if px < 0:
        #     nposx = 0
        # else:
        #     nposx = len(value) - px

        # assert posy == nposy
        # assert posx == nposx

        return (posx, posy)

    def calculateLayoutSizes(self, min_width, min_height, max_width, max_height):
        rows = self.props.get("rows", len(self.getValue().split("\n")))
        maxRows = self.maxRows()
        rows = min(rows, maxRows)

        return super().calculateLayoutSizes(
            min_width, max(min_height, rows), max_width, min(max_height, maxRows)
        )

    def render(self):
        return Text(self.getValue(), on_keypress=self.handleKeyPress)


class textarea(input):
    def maxRows(self):
        return self.props.get("maxRows", 1024)


class select(Paintable):
    def isOpen(self):
        return self == self.document.currentOpenElement

    def handleOpenClose(self, ev: EventMouseClick):
        if self.isOpen():
            self.document.setOpenElement(None)
        else:
            self.document.setOpenElement(self)
        ev.stopPropagation = True

    def handleChange(self, ev):
        on_change = self.props.get("on_change")
        ev.target = self
        if on_change:
            on_change(ev)

    def handleKeyPress(self, ev: EventKeyPress):
        if not self.children or not self.state["open"]:
            return
        current = self.queryElement(":focus")
        if not current:
            if ev.keycode == "DOWN":
                self.document.setFocus(self.children[0])
            if ev.keycode == "UP":
                self.document.setFocus(self.children[-1])

    def render(self):
        if self.isOpen():
            return div(
                on_keypress=self.handleKeyPress,
                # on_blur=lambda ev: self.setState({"open": False})
            )[
                Text(
                    text=f" {self.props.get('label')} ",
                    style=self,
                    className="relative",
                    on_click=self.handleOpenClose,
                ),
                div(className="absolute z-100", style={"zIndex": 1})[
                    self.props.get("children", [])
                ],
            ]
        else:
            return Text(
                style=self,
                on_click=self.handleOpenClose,
                text=f" {self.props.get('label')} ",
            )


class option(Paintable):
    def handleOnClick(self, ev):
        parent = self.parent
        while parent and not isinstance(parent, select):
            parent = parent.parent
        if not parent:
            return
        parent.handleChange(EventChange(self.props.get("value"), target=self))

    def __init__(self, **kwargs):
        super().__init__(on_click=kwargs.get("on_click", self.handleOnClick))


class dialog(Paintable):
    pass
