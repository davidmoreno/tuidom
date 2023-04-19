
import logging

from retui import defaults
from retui.renderer import Renderer

from .events import EventClick, EventKeyPress, Event, HandleEventTrait
from .component import Component

logger = logging.getLogger(__name__)


class Document(HandleEventTrait, Component):
    """
    A component with some extra methods
    """
    currentFocusedElement = None
    name = "body"
    css = defaults.DEFAULT_CSS

    def __init__(self, root: Component = None):
        super().__init__()
        self.props = {
            "on_keypress": self.on_keypress,
        }
        if root:
            root.document = self
            self.props["children"] = [root]
        self.document = self

    def setRoot(self, root: Component):
        root.document = self
        self.props["children"] = [root]

    @property
    def root(self):
        return self.props["children"][0]

    def is_focusable(self, item: Component):
        if not isinstance(item, HandleEventTrait):
            return False
        for key in item.props.keys():
            if key.startswith("on_"):
                return True
        return False

    def nextFocus(self):
        prev = self.currentFocusedElement
        logger.debug("Current focus is %s", prev)
        for child in self.root.preorderTraversal():
            if self.is_focusable(child):
                if prev is None:
                    logger.debug("Set focus on %s", child)
                    self.currentFocusedElement = child
                    return child
                elif prev is child:
                    prev = None
        logger.debug("Lost focus")
        self.currentFocusedElement = None
        return None

    def on_keypress(self, event: EventKeyPress):
        if event.keycode == "TAB":
            self.nextFocus()
        if event.keycode == "ENTER":
            self.on_event(EventClick([1], (0, 0)))

    def on_event(self, ev: Event):
        name = ev.name
        if not ev.target:
            item = self.currentFocusedElement
            if not item:
                item = self
            ev.target = item
        else:
            item = ev.target

        while item:
            if isinstance(item, HandleEventTrait):
                event_handler = item.props.get(f"on_{name}")
                logger.debug(f"Event {name} on {item}: {event_handler}")
                if event_handler:
                    event_handler(ev)
                if ev.stopPropagation:
                    return
            item = item.parent

        # not handled

    def paint(self, renderer: Renderer):
        self.calculateLayoutSizes(
            0,
            0,
            renderer.width,
            renderer.height
        )
        self.layout.y = 1
        self.layout.x = 1
        self.calculateLayoutPosition()
        # for node in self.preorderTraversal():
        #     print(node, node.layout)
        # return

        renderer.fillStyle = self.getStyle("background")
        renderer.strokeStyle = self.getStyle("color")
        renderer.fillRect(1, 1, renderer.width, renderer.height)

        super().paint(renderer)
        if self.currentFocusedElement:
            renderer.setCursor(
                self.currentFocusedElement.layout.x,
                self.currentFocusedElement.layout.y
            )
        renderer.flush()
