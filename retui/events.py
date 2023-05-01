
from dataclasses import dataclass


class HandleEventTrait:
    pass


@dataclass
class Event:
    name: str
    stopPropagation: bool = False
    target = None


class EventMouse(Event):
    buttons: list[int]
    position: tuple[int, int]
    name = "mouse"

    def __init__(self, buttons: list[int], position: tuple[int, int]):
        super().__init__(self.name)
        self.buttons = buttons
        self.position = position

    def __str__(self):
        return f"clickevent buttons: {self.buttons}, x: {self.position[0]}, y: {self.position[1]}"


class EventMouseDown(EventMouse):
    name = "mousedown"

    def __str__(self):
        return f"mousedown buttons: {self.buttons}, x: {self.position[0]}, y: {self.position[1]}"


class EventMouseUp(EventMouse):
    name = "mouseup"

    def __str__(self):
        return f"mouseup buttons: {self.buttons}, x: {self.position[0]}, y: {self.position[1]}"


class EventMouseClick(EventMouse):
    name = "click"

    def __str__(self):
        return f"mouseclick buttons: {self.buttons}, x: {self.position[0]}, y: {self.position[1]}"


class EventFocus(Event):
    name = "focus"

    def __init__(self, target):
        super().__init__("focus")
        self.target = target


class EventBlur(Event):
    name = "blur"

    def __init__(self, target):
        super().__init__("blur")
        self.target = target


class EventKeyPress(Event):
    keycode: str

    def __init__(self, keycode: str):
        super().__init__("keypress")
        self.keycode = keycode

    def __repr__(self):
        return f"<KeyPress {repr(self.keycode)}>"


class EventExit(Event):
    exitcode: int

    def __init__(self, exitcode: str = 0):
        super().__init__("exit")
        self.exitcode = exitcode


class EventChange(Event):
    def __init__(self, value, target=None):
        super().__init__("selected")
        self.value = value
        self.originalTarget = target
