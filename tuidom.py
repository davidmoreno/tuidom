
import os
import termios
import logging
import math
import shutil
from dataclasses import dataclass, field
import sys
import tty
from typing import Callable, List, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class Style:
    color: Optional[str] = None
    background: Optional[str] = None
    padding: Optional[str | int] = None
    width: Optional[str | int] = None
    height: Optional[str | int] = None
    bold: Optional[bool] = None
    underline: Optional[bool] = None
    scroll: Optional[str] = None
    alignItems: Optional[Literal["top", "center", "bottom"]] = None
    justifyItems: Optional[Literal[
        "left", "center", "right", "justify"]] = None
    borderStyle: Optional[Literal["single", "double"]] = None
    borderColor: Optional[str] = None
    top: Optional[str | int] = None
    left: Optional[str | int] = None
    flexDirection: Literal["row", "column"] = None
    flexGrow: int = None

    def union(self, other):
        if other is None or other is False:
            return self
        nstyle = Style()
        for key in Style.__annotations__.keys():
            nval = getattr(other, key)
            if nval is None:
                nval = getattr(self, key)
            setattr(nstyle, key, nval)
        return nstyle

    def __repr__(self):
        ret = []
        for key in self.__annotations__.keys():
            val = getattr(self, key)
            if val is not None:
                ret.append(f"{key}={repr(val)}")
        return f"Style({', '.join(ret)})"


DEFAULT_CSS = Style(
    color="white",
    background="grey",
    padding=0,
    scroll="auto",
    alignItems="top",
    justifyItems="left",
    flexDirection="column",
)

INHERITABLE_STYLES = set(["color", "background"])

COLORS = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "grey": "#777777",
    "bg-primary": "#37E2D5",
    "bg-secondary": "#590696",
    "bg-tertiary": "#C70A80",
    "bg-quaternary": "#FBCB0A",

    "text-primary": "#000000",
    "text-secondary": "#ffffff",
    "text-tertiary": "#ffffff",
    "text-quaternary": "#000000",
}


@dataclass
class Event:
    stopPropagation: bool = False


@dataclass
class KeyPress(Event):
    key: str = ""

    def __init__(self, key):
        self.key = key


@dataclass
class Focus(Event):
    pass


@dataclass
class Click(Event):
    pass


@dataclass
class Layout:
    """
    Always have a value, to ease calculations
    """
    top: int = 0
    left: int = 0
    width: int = 0
    height: int = 0


@ dataclass
class Constraints:
    minWidth: int = 0
    maxWidth: int = 1024
    minHeight: int = 0
    maxHeight: int = 1024

    def dup(self):
        return Constraints(
            self.minWidth,
            self.maxWidth,
            self.minHeight,
            self.maxHeight,
        )


@ dataclass
class Element:
    children: List['Element'] = field(default_factory=list)
    style: Optional[Style] = field(default_factory=Style)
    id: Optional[str] = None
    className: Optional[str] = None

    # event handlers
    on_focus: Callable | bool = False
    on_click: Callable | bool = False
    on_keypress: Callable | bool = False

    # these is set by the renderer
    parent: Optional['Element'] = None
    document: 'TuiRenderer' = None
    layout: Layout = field(default_factory=Layout)
    pseudo: list[str] = field(default_factory=list)

    def __init__(self, children=[], *, style=False, id=None, className=None, on_focus=False, on_click=False):
        super().__init__()
        self.children = children
        if not style:  # this allows to pass None or False
            style = Style()
        self.style = style
        self.id = id
        self.layout = Layout()
        self.className = className
        self.pseudo = []
        self.on_focus = on_focus
        self.on_click = on_click

    def queryElement(self, query: str):
        return self.document.queryElementCompiled(self, Query(query))

    def __str__(self) -> str:
        if self.id:
            return f"<{self.__class__.__name__.lower()}#{self.id}>"
        return f"<{self.__class__.__name__.lower()}>"

    def __repr__(self) -> str:
        return str(self)


class Div(Element):
    pass


@ dataclass
class Span(Element):
    text: str = ""

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def __str__(self) -> str:
        if self.id:
            return f"<{self.__class__.__name__.lower()}#{self.id}>{self.text}</{self.__class__.__name__.lower()}>"
        return f"<{self.__class__.__name__.lower()}>{self.text}</{self.__class__.__name__.lower()}>"

    def __repr__(self) -> str:
        return str(self)


class TextInput(Span):

    def __init__(self, text="", **kwargs):
        super().__init__(text)
        self.on_keypress = self.handle_keypress
        self.on_focus = True

    def handle_keypress(self, event: KeyPress):
        key = event.key
        base = self.text
        if key == "\x7f":
            base = base[:-1]
        elif key == "ENTER":
            base = base + "\n"
        elif len(key) == 1:
            base = base + key
        self.text = base

        lines = self.text.split("\n")
        self.document.cursor.top = self.layout.top + len(lines) - 1
        self.document.cursor.left = self.layout.left + len(lines[-1])


class Query:
    id_selector: Optional[str] = None
    class_selector: Optional[str] = None
    pseudo_selector: Optional[str] = None

    def __init__(self, query: str):
        oquery = query
        if query.startswith("#"):
            sel = ""
            for c in query[1:]:
                if c in '.:':
                    break
                sel += c
            self.id_selector = sel
            query = query[1+len(sel):]
        if query.startswith("."):
            sel = ""
            for c in query[1:]:
                if c in ':':
                    break
                sel += c
            self.class_selector = sel
            query = query[1+len(sel):]
        if query.startswith(":"):
            self.pseudo_selector = query[1:]
            query = query[1+len(query):]
        if query:
            logger.error("Invalid query: %s", oquery)

    def match(self, node: Element):
        matches = True
        if self.id_selector and node.id != self.id_selector:
            matches = False

        if self.class_selector:
            if not node.className or not any(x == self.class_selector for x in node.className.split()):
                matches = False
        if self.pseudo_selector:
            match self.pseudo_selector:
                case "focus":
                    if node is not node.document.selected_element:
                        matches = False
                case _:
                    logger.warning("Unknown pseudo selector: %s",
                                   self.pseudo_selector)
                    matches = False
        return matches


@dataclass
class Cursor:
    top: int = 1
    left: int = 1


class TuiRenderer:
    width = 80
    height = 25
    document: Optional[Element] = None
    css = {}
    selected_element = None
    cursor = Cursor(1, 1)

    def __init__(self, *, document=None, css=None):
        if document:
            self.set_document(document)
        if css:
            self.set_css(css)

    def set_document(self, document):
        self.document = document
        self.set_document_fields(document)
        return self

    def set_document_fields(self, node):
        node.document = self
        for child in node.children:
            child.parent = node
            self.set_document_fields(child)

    def set_css(self, css: dict):
        self.css.update(css)
        return self

    def queryElement(self, query) -> Optional[Element]:
        return self.queryElementCompiled(self.document, Query(query))

    def queryElementCompiled(self, node, query: Query):
        for node in self.preorder_traversal(node):
            if query.match(node):
                return node

    def get_style(self, element: Element, key: str):
        ret = element.style and getattr(element.style, key)
        if ret is not None:
            return ret

        pseudol = ["", *element.pseudo]

        # basic one level CSS
        if element.className:
            ret = None
            for ps in pseudol:
                for className in element.className.split():
                    className = f".{className}{ps}"
                    css = self.css.get(className)
                    if css and key in css:
                        ret = css[key]
            if ret:
                return ret

        if element.parent is not None and key in INHERITABLE_STYLES:
            return self.get_style(element.parent, key)

        return getattr(DEFAULT_CSS, key)

    def calculate_proportion(self, current, rule):
        if rule is None:
            return None
        if isinstance(rule, int):
            return max(0, min(current, rule))
        if isinstance(rule, str):
            if rule == "auto":
                return None
            if rule.endswith("%"):
                return int(current * int(rule[:-1]) / 100)
            logger.warning("Invalid width rule: %s", rule)
        return None

    def calculate_layout(self):
        document = self.document
        document.layout.top = 1
        document.layout.left = 1
        document.layout.width = self.width
        document.layout.height = self.height
        self.calculate_layout_sizes(document, Constraints(
            self.width, self.width, self.height, self.height,
        ))
        return self.calculate_layout_element(document)

    def calculate_layout_sizes(self, node: Element, oconstraints: Constraints):
        constraints = oconstraints.dup()

        width = self.calculate_proportion(
            constraints.maxWidth,
            self.get_style(node, "width")
        )
        if width:
            constraints.maxWidth = width
            constraints.minWidth = width
        height = self.calculate_proportion(
            constraints.maxHeight,
            self.get_style(node, "height")
        )
        if height:
            constraints.maxHeight = height
            constraints.minHeight = height

        width = 0
        height = 0

        if hasattr(node, "text"):
            width = len(node.text)
            height = math.ceil(width / constraints.maxWidth)
            width = min(width, constraints.maxWidth)

        if self.get_style(node, "borderStyle"):
            constraints.maxWidth -= 2
            constraints.maxHeight -= 2

        padding = self.get_style(node, "padding")
        if padding:
            constraints.maxWidth -= padding * 2
            constraints.maxHeight -= padding * 2

        flexDirection = self.get_style(node, "flexDirection")
        if flexDirection == "column":
            w, h = self.calculate_layout_column(node, constraints)
            width += w
            height += h
        elif flexDirection == "row":
            w, h = self.calculate_layout_row(node, constraints)
            width += w
            height += h

        if self.get_style(node, "borderStyle"):
            width += 2
            height += 2

        padding = self.get_style(node, "padding")
        if padding:
            width += padding*2
            height += padding*2

        node.layout.width = max(
            min(width, constraints.maxWidth),
            constraints.minWidth
        )
        node.layout.height = max(
            min(height, constraints.maxHeight),
            constraints.minHeight
        )

    def calculate_layout_column(self, node, constraints):
        children_grow = [
            (x, self.get_style(x, "flexGrow"))
            for x in node.children
        ]
        fixed_children = [x[0] for x in children_grow if not x[1]]
        variable_children = [x for x in children_grow if x[1]]
        width = 0
        height = 0
        for child in fixed_children:
            self.calculate_layout_sizes(child, Constraints(
                0, constraints.maxWidth,
                0, constraints.maxHeight,
            ))
            height += child.layout.height
            width = max(width, child.layout.width)
            constraints.maxHeight = constraints.maxHeight-child.layout.height
            constraints.minWidth = max(constraints.minWidth, width)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = constraints.maxHeight / quants
            for child, grow in variable_children:
                cheight = math.floor(quant_size * grow)
                self.calculate_layout_sizes(child, Constraints(
                    constraints.minWidth,
                    constraints.maxWidth,
                    cheight,
                    cheight,
                ))
                height += child.layout.height
                width = max(width, child.layout.width)
                constraints.maxHeight = constraints.maxHeight-child.layout.height
                constraints.minWidth = max(constraints.minWidth, width)

        # this is equivalent to align items stretch
        for child in node.children:
            child.layout.width = width
        return (width, height)

    def calculate_layout_row(self, node: Element, constraints: Constraints):
        children_grow = [
            (x, self.get_style(x, "flexGrow"))
            for x in node.children
        ]
        fixed_children = [x[0] for x in children_grow if not x[1]]
        variable_children = [x for x in children_grow if x[1]]
        width = 0
        height = 0
        for child in fixed_children:
            self.calculate_layout_sizes(child, Constraints(
                0, constraints.maxWidth,
                0, constraints.maxHeight,
            ))
            width += child.layout.width
            height = max(height, child.layout.height)
            constraints.maxWidth = constraints.maxWidth-child.layout.width
            constraints.minWidth = max(constraints.minWidth, width)

        if variable_children:
            quants = sum(x[1] for x in variable_children)
            quant_size = constraints.maxWidth / quants
            for child, grow in variable_children:
                cwidth = math.floor(quant_size * grow)
                self.calculate_layout_sizes(child, Constraints(
                    0,
                    cwidth,
                    constraints.minHeight,
                    constraints.maxHeight,
                ))
                height += child.layout.height
                width = max(width, child.layout.width)
                constraints.maxWidth = constraints.maxWidth-child.layout.height
                constraints.minWidth = max(constraints.minWidth, width)
        return (width, height)

    def calculate_layout_element(self, node: Element):
        top = node.layout.top
        left = node.layout.left
        flexDirection = self.get_style(node, "flexDirection")

        if self.get_style(node, "borderStyle"):
            top += 1
            left += 1

        padding = self.get_style(node, "padding")
        if padding:
            top += padding
            left += padding

        for child in node.children:
            child.layout.top = top
            child.layout.left = left

            self.calculate_layout_element(child)
            if flexDirection == "column":
                top += child.layout.height
            else:
                left += child.layout.width

    def handle_event(self, event: Event):
        HANDLER_NAMES = {
            KeyPress: "on_keypress",
            Click: "on_click",
            Focus: "on_focus",
        }
        handler_name = HANDLER_NAMES.get(event.__class__, "on_event")
        if self.selected_element:
            handler = getattr(self.selected_element, handler_name, None)
            if handler:
                handler(event)

        if not event.stopPropagation:
            handler = getattr(self, handler_name, None)
            if handler:
                handler(event)

        if not event.stopPropagation:
            return event
        return None

    def on_keypress(self, event: KeyPress):
        if event.key == "TAB":
            self.focus_next()
        if event.key == "ENTER":
            self.handle_event(Click())

    def preorder_traversal(self, node):
        yield node
        for child in node.children:
            yield from self.preorder_traversal(child)

    def focus_next(self):
        for item in self.preorder_traversal(self.document):
            item.pseudo = [x for x in item.pseudo if x != ":focus"]

        for item in self.preorder_traversal(self.document):
            if item.on_focus:
                if self.selected_element is None:
                    self.selected_element = item

                    parent = item
                    while parent:
                        parent.pseudo.append(":focus")
                        parent = parent.parent

                    return item
                elif self.selected_element is item:
                    self.selected_element = None

        # got nothing, ensure we reset to nothing
        self.selected_element = None
        return None

    def rgbcolor(self, color: str):
        if color.startswith("#"):
            return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"
        if color in COLORS:
            color = COLORS[color]
            if isinstance(color, tuple):
                return ';'.join(map(str, color))
            if color.startswith("#"):
                return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"

        return ';'.join(map(str, COLORS["black"]))

    def print_layout(self, dom: Element, indent=0, printer=print):
        printer(
            f"{' '*indent} {dom} {dom.layout} {dom.style} className={repr(dom.className or '')}")
        for child in dom.children:
            self.print_layout(child, indent + 2, printer=printer)

    def render(self):
        raise NotImplementedError()


class XtermRenderer(TuiRenderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        width, height = shutil.get_terminal_size()
        self.width = width
        self.height = height

        fd = sys.stdin.fileno()
        self.oldtermios = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~(termios.ECHO | termios.ICANON)        # lflags
        termios.tcsetattr(fd, termios.TCSADRAIN, new)

    def close(self):
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self.oldtermios)

    def read_key(self):
        return os.read(sys.stdin.fileno(), 1)

    def read_event(self):
        key = self.read_key()
        if 0 < ord(key) < 27:
            key = chr(ord(key) + ord('A') - 1)
            if key == "I":
                key = "TAB"
            elif key == "J":
                key = "ENTER"
            else:
                key = f"CONTROL+{key}"
            return KeyPress(key)
        return KeyPress(key.decode())

    def render(self, *, file=sys.stdout):
        self.calculate_layout()

        ret = self.render_element(self.document)
        # ret.append(
        #     f"\033[{self.width};{self.height}H",  # position
        # )
        ret.append(
            f"\033[{self.cursor.top};{self.cursor.left}H",  # position
        )
        if file:
            print(strlist_to_str(ret), file=file, end="")
        return ret

    def render_rectangle(self, layout: Layout, table_chars=None):
        if not table_chars:
            return[
                f"\033[{layout.top};{layout.left}H",  # position
                [
                    [
                        f"\033[{top};{layout.left}H",  # position
                        " "*layout.width,  # write bg lines
                    ]
                    for top in range(layout.top, layout.top + layout.height)
                ]
            ]
        else:
            return[
                f"\033[{layout.top};{layout.left}H",  # position
                table_chars[0],
                table_chars[4]*(layout.width-2),
                table_chars[1],
                # position
                [
                    [
                        f"\033[{top};{layout.left}H",  # position
                        table_chars[5],
                        " "*(layout.width-2),  # write bg lines
                        table_chars[5],
                    ] for top in range(layout.top+1, layout.top + layout.height-1)
                ],
                # position
                f"\033[{layout.top + layout.height - 1};{layout.left}H",
                table_chars[2],
                table_chars[4]*(layout.width-2),
                table_chars[3],
            ]

    def render_element(self, node: Element):
        background = self.rgbcolor(self.get_style(node, "background"))
        color = self.rgbcolor(self.get_style(node, "color"))
        layout = node.layout

        table_chars = None
        match self.get_style(node, "borderStyle"):
            case "single":
                table_chars = "┌┐└┘─│"
            case "double":
                table_chars = "╔╗╚╝═║"

        ret = [
            # "\033[38;5;",
            f"\033[48;2;{background}m\033[38;2;{color}m",  # colors
            f"\033[{layout.top};{layout.left}H",  # position
            self.render_rectangle(layout, table_chars)
        ]

        if isinstance(node, Span):
            ret.append(self.render_span(node))

        for children in node.children:
            ret.append(self.render_element(children))
        return ret

    def render_span(self, node: Element):
        ret = []
        layout = node.layout
        left, top = layout.left, layout.top

        if self.get_style(node, "borderStyle"):
            left += 1
            top += 1
        padding = self.get_style(node, "padding")
        if padding:
            left += padding
            top += padding

        bold = self.get_style(node, "bold")
        if bold:
            ret.append(
                f"\033[1m",
            )
        underline = self.get_style(node, "underline")
        if underline:
            ret.append(
                f"\033[4m",
            )

        for lineno, line in enumerate(node.text.split("\n")):
            ret.append(
                f"\033[{layout.top+lineno};{layout.left}H",  # position
            )
            ret.append(line)

        if bold or underline:
            ret.append(
                f"\033[0m",  # normal
            )
        return ret

    def reset(self):
        return '\033\143'


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return ''.join(strlist_to_str(x) for x in strl)


# https://www.xfree86.org/current/ctlseqs.html
