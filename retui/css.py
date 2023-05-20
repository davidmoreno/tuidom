from dataclasses import dataclass
import re
import logging
from typing import Literal


StyleProperty = Literal[
    "color",
    "background",
    "flex-direction",
    "flex-grow",
    "padding",
    "border",
    "width",
    "height",
]

# this styles are checked against parents if not defined
INHERITABLE_STYLES: list[StyleProperty] = [
    "color",
    "background",
    "font-weight",
    "font-decoration",
    "font-style",
]


CSS_SELECTOR_RE = re.compile(
    r"^(?P<element>\w+|\*|)(?P<pseudo>(:\w+)*)(?P<id>#\w+|)(?P<class>(\.(\w|[-_])+)*)(?P<pseudo2>(:\w+)*)$"
)

logger = logging.getLogger(__name__)


@dataclass
class Selector:
    selector: str

    element: str | None = None
    id: str | None = None
    classes: list[str] = None
    pseudo: list[str] = None
    priority: int = 0

    def __init__(self, selector: str):
        """
        Compile a rule into the Rule object.

        Normally these rules are accesses a lot, so fast access is a must.
        """
        self.selector = selector
        self.pseudo = []
        self.classes = []

        match = CSS_SELECTOR_RE.match(selector)
        if not match:
            logger.warning("Invalid selector: %s", selector)
            self.priority = -1
            return

        mdict = match.groupdict()
        if mdict["element"] and mdict["element"] != "*":
            self.element = mdict["element"]
            self.priority += 1
        if mdict["id"]:
            self.id = mdict["id"][1:]
            self.priority += 10000
        if mdict["class"]:
            classes = mdict["class"].split(".")[1:]
            self.classes = classes
            self.priority += 100 * len(classes)
        if mdict["pseudo"]:
            self.priority += 10
            self.pseudo = mdict["pseudo"].split(":")[1:]
        if mdict["pseudo2"]:
            self.priority += 10
            self.pseudo = (self.pseudo or []) + mdict["pseudo2"].split(":")[1:]

        if self.pseudo is None:
            self.pseudo = []

    def match(self, element: "tui.Component"):
        if self.element and element.name != self.element:
            return False

        if self.id and element.props.get("id") != self.id:
            return False

        if self.classes:
            elcls = element.props.get("className")
            if not elcls:
                return False
            elcls = elcls.split()
            for cls in self.classes:
                if cls not in elcls:
                    return False

        if "focus" in self.pseudo:
            focused = element.document.currentFocusedElement
            while focused:
                if focused == element:
                    return self.priority
                focused = focused.parent

            return False

        return self.priority

    def __repr__(self):
        return f"<Selector '{self.selector}'>"


class StyleSheet:
    rules: list[tuple[Selector, dict]] = []

    def __init__(self):
        pass

    def addDict(self, styles):
        for selector, style in styles.items():
            selector = Selector(selector)
            if selector.priority < 0:
                continue
            style = StyleSheet.normalizeStyle(style)
            self.rules.append((selector, style))

    @staticmethod
    def normalizeStyle(style):
        if "padding" in style:
            padding = style["padding"]
            top, right, bottom, left = split_421_item(padding)
            style["paddingTop"] = style.get("paddingTop") or top
            style["paddingRight"] = style.get("paddingRight") or right
            style["paddingBottom"] = style.get("paddingBottom") or bottom
            style["paddingLeft"] = style.get("paddingLeft") or left
        if "border" in style:
            border = style["border"]
            top, right, bottom, left = split_421_item(border)
            style["borderTop"] = style.get("borderTop") or top
            style["borderRight"] = style.get("borderRight") or right
            style["borderBottom"] = style.get("borderBottom") or bottom
            style["borderLeft"] = style.get("borderLeft") or left

        return style

    def getStyle(self, component: "retui.Component", key: str):
        priority = -1
        value = None
        for selector, style in self.rules:
            pri = selector.match(component)
            # print(selector, pri, key, value)
            if pri and pri >= priority and key in style:
                value = style[key]
                priority = pri
        return value


def split_421_item(item):
    items = [int(x) for x in str(item).split()]
    if len(items) == 1:
        item = int(items[0])
        return item, item, item, item
    if len(items) == 2:
        return items[0], items[1], items[0], items[1]
    if len(items) == 3:
        return items[0], items[1], items[2], items[1]
    if len(items) == 4:
        return items[0], items[1], items[2], items[3]

    return items
