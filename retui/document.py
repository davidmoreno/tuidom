
import logging

from retui import defaults
from retui.renderer import Renderer

from .events import EventBlur, EventMouseClick, EventExit, EventFocus, EventKeyPress, Event, HandleEventTrait
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
            self.on_event(EventMouseClick([1], (0, 0)))

    def on_event(self, ev: Event):
        def handle_event(ev: Event):
            if isinstance(ev, EventMouseClick):
                el = ev.target
                while el:
                    if self.is_focusable(el):
                        self.setFocus(el)
                        break
                    el = el.parent

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

        if isinstance(ev, EventMouseClick):
            x, y = ev.position
            for el in self.preorderTraversal():
                inside = el.layout.inside(x, y)
                if inside:
                    ev.target = el

            if ev.target:
                handle_event(ev)

        if isinstance(ev, EventExit):
            self.stopLoop = ev
            return

        # for currently focused and parents
        if not ev.target:
            item = self.currentFocusedElement
            if not item:
                item = self
            ev.target = item

            handle_event(ev)

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

        bylayer = {0: []}
        for child in self.preorderTraversal():
            if child == self:  # skip me
                continue
            # child.paint(renderer)
            zIndex = child.getStyle("zIndex", 0) or 0
            if zIndex not in bylayer:
                bylayer[zIndex] = []
            bylayer[zIndex].append(child)

        for zIndex, paintlist in sorted(bylayer.items()):
            for child in paintlist:
                # print(zIndex, child, child.layout)
                child.paint(renderer)

        # super().paint(renderer)
        self.setCursor(renderer)
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

    def loop(self, renderer: Renderer):
        self.stopLoop = None
        while not self.stopLoop:
            self.materialize()
            self.paint(renderer)
            try:
                for ev in renderer.readEvents():
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
