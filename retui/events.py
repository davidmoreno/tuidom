
from dataclasses import dataclass


class HandleEventTrait:
    pass


@dataclass
class Event:
    name: str
    stopPropagation: bool = False
    target = None


class EventClick(Event):
    buttons: list[int]
    position: tuple[int, int]

    def __init__(self, buttons: list[int], position: tuple[int, int]):
        super().__init__("click")
        self.buttons = buttons
        self.position = position


class EventFocus(Event):
    name = "focus"
    pass


class EventKeyPress(Event):
    keycode: str

    def __init__(self, keycode: str):
        super().__init__("keypress")
        self.keycode = keycode
