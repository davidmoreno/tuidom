
import os
import termios
import logging
import math
import shutil
from dataclasses import dataclass, field
import sys
import tty
from typing import List, Literal, Optional

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
    background="#333333",
    padding=0,
    scroll="auto",
    width="auto",
    height="auto",
    alignItems="top",
    justifyItems="left"
)

INHERITABLE_STYLES = set(["color", "background"])

COLORS = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "bg-primary": "#590696",
    "bg-secondary": "#37E2D5",
    "bg-tertiary": "#C70A80",
    "bg-quaternary": "#FBCB0A",

    "text-primary": "#ffffff",
    "text-secondary": "#000000",
    "text-tertiary": "#ffffff",
    "text-quaternary": "#000000",
}
# COLORS = {
#     "black": "#000000",
#     "red": "#ff0000",
#     "green": "#00ff00",
#     "blue": "#0000ff",
#     "white": "#ffFFFF",
# }


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

    # these is set by the renderer
    parent: Optional['Element'] = None
    layout: Layout = field(default_factory=Layout)

    def __init__(self, children=[], *, style=False, id=None):
        super().__init__()
        self.children = children
        if not style:  # this allows to pass None or False
            style = Style()
        self.style = style
        self.id = id
        self.layout = Layout()

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


@dataclass
class Event:
    pass


@dataclass
class KeyPress:
    key: str


class TuiRenderer:
    width = 80
    height = 25

    def get_style(self, element: Element, name):
        ret = element.style and getattr(element.style, name)
        if ret is not None:
            return ret
        if element.parent is not None and name in INHERITABLE_STYLES:
            return self.get_style(element.parent, name)

        return getattr(DEFAULT_CSS, name)

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

    def calculate_layout(self, dom):
        dom.layout.top = 1
        dom.layout.left = 1
        dom.layout.width = self.width
        dom.layout.height = self.height
        self.calculate_layout_sizes(dom, Constraints(
            self.width, self.width, self.height, self.height,
        ))
        return self.calculate_layout_element(dom)

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

        flexDirection = node.style.flexDirection or "column"
        if flexDirection == "column":
            w, h = self.calculate_layout_column(node, constraints)
            width += w
            height += h
        elif flexDirection == "row":
            w, h = self.calculate_layout_row(node, constraints)
            width += w
            height += h

        if node.style.borderStyle:
            width += 2
            height += 2

        if node.style.padding:
            width += node.style.padding*2
            height += node.style.padding*2

        node.layout.width = max(
            min(width, constraints.maxWidth),
            constraints.minWidth
        )
        node.layout.height = max(
            min(height, constraints.maxHeight),
            constraints.minHeight
        )

    def calculate_layout_column(self, node, constraints):
        fixed_children = [x for x in node.children if not x.style.flexGrow]
        variable_children = [x for x in node.children if x.style.flexGrow]
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
            constraints.minWidth = width

        if variable_children:
            quants = sum(x.style.flexGrow for x in variable_children)
            quant_size = constraints.maxHeight / quants
            for child in variable_children:
                cheight = math.floor(quant_size * child.style.flexGrow)
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
        fixed_children = [x for x in node.children if not x.style.flexGrow]
        variable_children = [x for x in node.children if x.style.flexGrow]
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
            constraints.minWidth = width

        if variable_children:
            quants = sum(x.style.flexGrow for x in variable_children)
            quant_size = constraints.maxWidth / quants
            for child in variable_children:
                cwidth = math.floor(quant_size * child.style.flexGrow)
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
        flexDirection = node.style.flexDirection or "column"

        if self.get_style(node, "borderStyle"):
            top += 1
            left += 1

        padding = self.get_style(node, "padding")
        if padding:
            top += padding
            left += padding

        for child in node.children:
            child.parent = node
            child.layout.top = top
            child.layout.left = left

            self.calculate_layout_element(child)
            if flexDirection == "column":
                top += child.layout.height
            else:
                left += child.layout.width

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

    def print_layout(self, dom: Element, indent=0):
        print(' '*indent, dom, dom.layout, dom.style)
        for child in dom.children:
            self.print_layout(child, indent + 2)

    def render(self, dom):
        raise NotImplementedError()


class XtermRenderer(TuiRenderer):
    def __init__(self):
        width, height = shutil.get_terminal_size()
        self.width = width
        self.height = height - 1

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
            key = f"CONTROL+{key}"
            return KeyPress(key)
        return KeyPress(key.decode())

    def render(self, dom: Element, file=sys.stdout):
        self.calculate_layout(dom)

        ret = self.render_element(dom)
        # ret.append(
        #     f"\033[{self.width};{self.height}H",  # position
        # )
        if file:
            print(strlist_to_str(ret), file=file)
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
        if node.style and node.style.borderStyle:
            style = node.style.borderStyle
            if style == "single":
                table_chars = "┌┐└┘─│"
            elif style == "double":
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
        ret.append(
            f"\033[{layout.top};{layout.left}H",  # position
        )

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

        ret.append(node.text)

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
