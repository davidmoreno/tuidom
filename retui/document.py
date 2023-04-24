
import logging

from retui import defaults
from retui.renderer import Renderer

from .events import EventBlur, EventClick, EventExit, EventFocus, EventKeyPress, Event, HandleEventTrait
from .component import Component

logger = logging.getLogger(__name__)


class Document(HandleEventTrait, Component):
    """
    A component with some extra methods
    """
    currentFocusedElement = None
    name = "body"
    css = defaults.DEFAULT_CSS
    stopLoop: None | EventExit = None

    def __init__(self, children=None, *, css=None, **props):
        if children:
            props = {
                **props,
                "children": children,
            }
        if css:
            self.css = {
                **defaults.DEFAULT_CSS,
                **css
            }
        super().__init__(**props)
        self.props = {
            "on_keypress": self.on_keypress,
        }
        self.document = self

    def is_focusable(self, item: Component):
        if not isinstance(item, HandleEventTrait):
            return False
        for key in item.props.keys():
            if key.startswith("on_"):
                return True
        return False

    def nextFocus(self):
        prev = self.currentFocusedElement
        for child in self.preorderTraversal():
            if self.is_focusable(child):
                if prev is None:
                    return self.setFocus(child)
                elif prev is child:
                    prev = None
        return self.setFocus(None)

    def prevFocus(self):
        current = self.currentFocusedElement
        prev = None
        for child in self.preorderTraversal():
            if self.is_focusable(child):
                if current is child:
                    current = prev
                    return self.setFocus(current)
                prev = child
        return self.setFocus(prev)

    def setFocus(self, el):
        if self.currentFocusedElement == el:
            return
        if self.currentFocusedElement:
            self.on_event(EventBlur(self.currentFocusedElement))
        self.currentFocusedElement = el
        if el:
            self.on_event(EventFocus(self.currentFocusedElement))

        return el

    def on_keypress(self, event: EventKeyPress):
        if event.keycode == "TAB":
            self.nextFocus()
        if event.keycode == "RTAB":
            self.prevFocus()
        if event.keycode == "ENTER":
            self.on_event(EventClick([1], (0, 0)))

    def on_event(self, ev: Event):
        if isinstance(ev, EventExit):
            self.stopLoop = ev
            return

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
                # logger.debug(f"Event {name} on {item}: {event_handler}")
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
        self.setCursor(renderer)
        renderer.flush()

    def setCursor(self, renderer: Renderer):
        if self.currentFocusedElement:
            el = self.currentFocusedElement
            cursor = (0, 0)
            parent = el
            while parent:
                if hasattr(parent, "cursor"):
                    cursor = parent.cursor
                    break
                parent = parent.parent

            renderer.setCursor(
                el.layout.x + cursor[0],
                el.layout.y + cursor[1],
            )

    def loop(self, renderer: Renderer):
        self.stopLoop = None
        while not self.stopLoop:
            self.materialize()
            self.paint(renderer)
            try:
                ev = renderer.readEvent()
                if ev.name == "keypress" and ev.keycode == defaults.BREAKPOINT_KEYPRESS:
                    renderer.breakpoint(
                        callback=lambda: self.prettyPrint(),
                        document=self
                    )
                elif isinstance(ev, EventExit):
                    return ev
                else:
                    self.on_event(ev)
            except KeyboardInterrupt:
                self.close()
                raise

        renderer.close()

        return self.stopLoop
