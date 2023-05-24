import logging

from retui import css, defaults
from retui.renderer import Renderer
from retui.xtermrenderer import XtermRenderer

from .events import (
    EventBlur,
    EventMouseClick,
    EventExit,
    EventFocus,
    EventKeyPress,
    Event,
    HandleEventTrait,
)
from .component import Component

logger = logging.getLogger(__name__)
default_renderer = XtermRenderer


class Document(HandleEventTrait, Component):
    """
    A component with some extra methods
    """

    currentFocusedElement = None
    # current open element normally a select. Click outside and it is closed. And only one at a time.
    currentOpenElement = None
    name = "body"
    stylesheet: css.StyleSheet
    stopLoop: None | EventExit = None
    cache = {}

    def __init__(self, renderer=None, children=None, *, stylesheet=None, **props):
        self.stylesheet = css.StyleSheet()
        self.stylesheet.addDict(defaults.DEFAULT_CSS)
        if children:
            props = {
                **props,
                "children": children,
            }
        if stylesheet:
            self.stylesheet.addDict(stylesheet)
        super().__init__(**props)
        self.props = {
            "on_keypress": self.on_keypress,
        }
        self.document = self

        if not renderer:
            renderer = default_renderer()
        self.renderer = renderer
        renderer.document = self

        self.materialize()

    def nextFocus(self):
        prev = self.currentFocusedElement
        for child in self.preorderTraversal():
            if child.isFocusable():
                if prev is None:
                    return self.setFocus(child)
                elif prev is child:
                    prev = None
        return self.setFocus(None)

    def prevFocus(self):
        current = self.currentFocusedElement
        prev = None
        for child in self.preorderTraversal():
            if child.isFocusable():
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
            self.on_event(EventFocus(el))

        return el

    def setOpenElement(self, el):
        self.currentOpenElement = el

    def on_keypress(self, event: EventKeyPress):
        if event.keycode == "TAB":
            self.nextFocus()
        if event.keycode == "RTAB":
            self.prevFocus()
        if event.keycode == "ENTER" and self.currentFocusedElement:
            layout = self.currentFocusedElement.layout
            self.on_event(EventMouseClick([1], (layout.x, layout.y)))

    def on_event(self, ev: Event):
        def handle_event(ev: Event):
            if isinstance(ev, EventMouseClick):
                for el in ev.target.parentTraversal():
                    if el.isFocusable():
                        self.setFocus(el)
                        break

            name = f"on_{ev.name}"
            el = ev.target
            while el:
                if isinstance(el, HandleEventTrait):
                    event_handler = el.props.get(name)
                    # logger.debug(f"Event {name} on {el}: {event_handler}")
                    if event_handler:
                        event_handler(ev)
                    if ev.stopPropagation:
                        return
                el = el.parent
            if self.currentOpenElement and isinstance(ev, EventMouseClick):
                self.setOpenElement(None)

        if isinstance(ev, EventMouseClick):
            el = self.findElementAt(*ev.position)
            ev.target = el

        if isinstance(ev, EventExit):
            self.stopLoop = ev
            return

        # for currently focused and parents
        if not ev.target:
            item = self.currentFocusedElement
            if not item:
                item = self
            ev.target = item

        if ev.target:
            handle_event(ev)

        # not handled
        if ev.stopPropagation:
            return

    def findElementAt(self, x: int, y: int):
        _z, el = super().findElementAt(x, y)
        return el

    def calculateLayout(self):
        self.calculateLayoutSizes(0, 0, self.renderer.width, self.renderer.height)
        self.layout.y = 0
        self.layout.x = 0
        self.calculateLayoutPosition()

        return self

    def paint(self, renderer: Renderer):
        self.calculateLayout()

        renderer.setBackground(self.getStyle("background"))
        renderer.setForeground(self.getStyle("color"))
        renderer.fillRect(0, 0, renderer.width, renderer.height)

        super().paint(renderer)
        assert len(renderer.translateStack) == 0
        assert len(renderer.clippingStack) == 0

        # super().paint(renderer)
        self.setCursor(renderer)
        self.cache = {}
        renderer.flush()

    def setCursor(self, renderer: Renderer):
        el = self.currentFocusedElement
        if not el:
            renderer.setCursor(
                renderer.width,
                renderer.height,
            )
            return

        cursor = el.getStyle("cursor")
        if cursor == "hidden" or cursor == "none":
            renderer.setCursor(
                renderer.width,
                renderer.height,
            )
            return

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

    def loop(self):
        renderer = self.renderer
        self.stopLoop = None
        while not self.stopLoop:
            self.materialize()
            self.paint(renderer)
            try:
                for ev in renderer.readEvents():
                    if (
                        ev.name == "keypress"
                        and ev.keycode == defaults.BREAKPOINT_KEYPRESS
                    ):
                        renderer.breakpoint(
                            callback=lambda: self.prettyPrint(), document=self
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
