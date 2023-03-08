

import logging
import math
import shutil
from dataclasses import dataclass, field
from typing import List, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class Style:
    color: Optional[str] = None
    background: Optional[str] = None
    padding: Optional[str | int] = None
    width: Optional[str | int] = None
    height: Optional[str | int] = None
    scroll: Optional[str] = None
    alignItems: Optional[Literal["top", "center", "bottom"]] = None
    justifyItems: Optional[Literal[
        "left", "center", "right", "justify"]] = None
    borderWidth: Optional[int] = None
    borderStyle: Optional[str] = None
    borderColor: Optional[str] = None
    top: Optional[str | int] = None
    left: Optional[str | int] = None
    flexDirection: Literal["row", "column"] = "column"
    flexGrow: int = 1


DEFAULT_CSS = Style(
    color="black",
    background="green",
    borderWidth=0,
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
    "bg-primary": "#37E2D5",
    "bg-secondary": "#590696",
    "bg-tertiary": "#C70A80",
    "bg-quaternary": "#FBCB0A",

    "text-primary": "#000000",
    "text-secondary": "#0000000",
    "text-tertiary": "#0000000",
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


@ dataclass
class Element:
    children: List['Element'] = field(default_factory=list)
    style: Optional[Style] = None
    id: Optional[str] = None

    # these is set by the renderer
    parent: Optional['Element'] = None
    layout: Layout = field(default_factory=Layout)


class Div(Element):
    pass


@ dataclass
class Span(Element):
    text: str = ""


class TuiRenderer:
    width = 80
    height = 25

    def get_style(self, element, name):
        ret = element.style and getattr(element.style, name)
        if ret is not None:
            return ret
        if element.parent is not None and name in INHERITABLE_STYLES:
            return self.get_style(element.parent, name)

        return getattr(DEFAULT_CSS, name)

    def calculate_pos(self, current, rule):
        if rule is None:
            return current
        if isinstance(rule, int):
            return max(0, min(current, rule))
        if isinstance(rule, str):
            if rule.endswith("%"):
                return int(current * int(rule[:-1]) / 100)
            logger.warning("Invalid width rule: %s", rule)
        return current

    def calculate_layout(self, dom):
        dom.layout.top = 0
        dom.layout.left = 0
        dom.layout.width = self.width
        dom.layout.height = self.height
        self.calculate_layout_sizes(dom, Constraints(
            0, self.width, 0, self.height,
        ))
        return self.calculate_layout_element(dom)

    def calculate_layout_sizes(self, node: Element, constraints: Constraints):
        fixed_children = [x for x in node.children if x.style.flexGrow == 0]
        variable_children = [x for x in node.children if x.style.flexGrow != 0]

        if node.style.width:
            tmp = self.calculate_pos(constraints.maxWidth, node.style.width)
            constraints.maxWidth = tmp
            constraints.minWidth = tmp
        if node.style.height:
            tmp = self.calculate_pos(constraints.maxHeight, node.style.height)
            constraints.maxHeight = tmp
            constraints.minHeight = tmp

        width = 0
        height = 0
        if node.style.borderColor:
            constraints.maxWidth = constraints.maxWidth-2
            constraints.maxHeight = constraints.maxHeight-2
            width += 2
            height += 2
        if node.style.padding:
            constraints.maxWidth = constraints.maxWidth-node.style.padding
            constraints.maxHeight = constraints.maxHeight-node.style.padding
            width += node.style.padding
            height += node.style.padding

        if hasattr(node, "text"):
            width = len(node.text)
            height = math.ceil(width / constraints.maxWidth)
            width = min(width, constraints.maxWidth)

        if node.style.flexDirection == "horizontal":
            for child in fixed_children:
                self.calculate_layout_sizes(child, constraints)
                width += child.width
                height = max(height, child.height)
                constraints.maxWidth = constraints.maxWidth-child.width
                constraints.minHeight = height

            if variable_children:
                quants = sum(x.style.flexGrow for x in variable_children)
                quant_size = constraints.maxWidth / quants
                for child in variable_children:
                    self.calculate_layout_sizes(Constraints(
                        quant_size * child.style.flexGrow,
                        quant_size * child.style.flexGrow,
                        constraints.minHeight,
                        constraints.maxHeight,
                    ))
                    width += child.width
                    height = max(height, child.height)
                    constraints.maxWidth = constraints.maxWidth-child.width
                    constraints.minHeight = height

        node.layout.width = max(
            min(width, constraints.maxWidth), constraints.minWidth)
        node.layout.height = max(
            min(height, constraints.maxHeight), constraints.minHeight)

    def calculate_layout_element(self, parent):
        ret = [parent.layout]
        top = parent.layout.top
        left = parent.layout.left
        for child in parent.children:
            # print(
            #     parent.__class__.__name__,
            #     "#", parent.id,
            #     "\n  ", parent.layout,
            #     "\n  ", child.__class__.__name__, "#", child.id,
            #     "\n  ", child.style
            # )
            child.parent = parent
            child.layout.top = top + self.calculate_pos(
                parent.layout.height - child.layout.height - top,
                child.style and child.style.top or 0
            )
            child.layout.left = left + self.calculate_pos(
                parent.layout.width - child.layout.width - left,
                child.style and child.style.left or 0
            )

            if parent.style and parent.style.borderColor:
                child.layout.top += 1
                child.layout.left += 1
                child.layout.width -= 2
                child.layout.height -= 2

            ret = [
                *ret,
                *self.calculate_layout_element(child),
            ]
            top += child.layout.height

        return ret

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

    def render(self, dom):
        raise NotImplementedError()


class XtermRenderer(TuiRenderer):
    def __init__(self):
        width, height = shutil.get_terminal_size()
        self.width = width
        self.height = height - 1

    def render(self, dom: Element):
        self.calculate_layout(dom)

        ret = self.render_element(dom)
        # ret.append(
        #     f"\033[{self.width};{self.height}H",  # position
        # )
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

    def render_element(self, dom: Element):
        background = self.rgbcolor(self.get_style(dom, "background"))
        color = self.rgbcolor(self.get_style(dom, "color"))
        layout = dom.layout

        if dom.style and dom.style.borderColor:
            table_chars = "╔╗╚╝═║"
        else:
            table_chars = None

        ret = [
            # "\033[38;5;",
            f"\033[48;2;{background}m\033[38;2;{color}m",  # colors
            f"\033[{layout.top};{layout.left}H",  # position
            self.render_rectangle(layout, table_chars)
        ]

        if isinstance(dom, Span):
            if dom.style and dom.style.borderColor:
                ret.append([
                    f"\033[{layout.top + 1};{layout.left + 2}H",  # position
                    dom.text,
                ])
            else:
                ret.append([
                    f"\033[{layout.top};{layout.left}H",  # position
                    dom.text,
                ])

        for children in dom.children:
            ret.append(self.render_element(children))
        return ret

    def reset(self):
        return '\033\143'


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return ''.join(strlist_to_str(x) for x in strl)


# https://www.xfree86.org/current/ctlseqs.html
