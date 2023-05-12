from dataclasses import dataclass
import re
import logging


CSS_SELECTOR_RE = re.compile(
    r"^(?P<element>\w+|)(?P<pseudo>(:\w+)*)(?P<id>#\w+|)(?P<class>(\.(\w|[-_])+)*)(?P<pseudo2>(:\w+)*)$"
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

        Normally these rulels are accesses a lot, so fast access is a must.
        """
        self.selector = selector

        match = CSS_SELECTOR_RE.match(selector)
        pri = 0
        if not match:
            logger.warning("Invalid selector: %s", selector)
            self.priority = -1
            return

        mdict = match.groupdict()
        if mdict["element"]:
            self.element = mdict["element"]
            self.priority += 1
        if mdict["id"]:
            self.id = mdict["id"][1:]
            self.priority += 10000
        if mdict["class"]:
            classes = mdict["class"].split(".")[1:]
            self.classes = classes
            self.priority += 10 * len(classes)
        if mdict["pseudo"]:
            self.priority += 1
            self.pseudo = mdict["pseudo"].split(":")[1:]
        if mdict["pseudo2"]:
            self.priority += 1
            self.pseudo = (self.pseudo or []) + mdict["pseudo2"].split(":")[1:]

    def match(self, element: "tui.Component"):
        if self.element and element.name != self.element:
            return False

        if self.id and element.props.get("id") != self.id:
            return False

        if self.classes:
            elcls = element.props.get("className", "").split()
            for cls in self.classes:
                if cls not in elcls:
                    return False

        if self.pseudo:
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
            style = self.normalizeStyle(style)
            self.rules.append((selector, style))

    def normalizeStyle(self, style):
        if "padding" in style:
            padding = style["padding"]
            style["paddingTop"] = style.get("paddingTop", padding)
            style["paddingRight"] = style.get("paddingRight", padding)
            style["paddingBottom"] = style.get("paddingBottom", padding)
            style["paddingLeft"] = style.get("paddingLeft", padding)
        if "border" in style:
            border = style["border"]
            style["borderTop"] = style.get("borderTop", border)
            style["borderRight"] = style.get("borderRight", border)
            style["borderBottom"] = style.get("borderBottom", border)
            style["borderLeft"] = style.get("borderLeft", border)
        return style

    def getStyle(self, component: "retui.Component", key: str):
        priority = -1
        value = None
        for selector, style in self.rules:
            pri = selector.match(component)
            print(selector, pri, key, value)
            if pri and pri > priority:
                value = style.get(key) or value
                priority = pri
        return value
