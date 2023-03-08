

import logging
import shutil
import sys
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
class Element:
    children: List['Element'] = field(default_factory=list)
    style: Optional[Style] = None

    # these is set by the renderer
    parent: Optional['Element'] = None
    layout: Layout = field(default_factory=Layout)


class Div(Element):
    pass


@ dataclass
class Span(Element):
    text: str = ""


def Welcome():
    return Div(
        [
            Div([
                Span(text="Hola Mundo!"),
            ], style=Style(
                borderWidth=1,
                borderStyle="solid",
                borderColor="white",
                background="#AABBDD",
                color="black",
                width=20,
                height=4,
                top="20%",
                left="50%",
            )),
            Div([
                Span(text="Hola Mundo!"),
            ], style=Style(
                borderWidth=1,
                borderStyle="solid",
                borderColor="white",
                background="#AABBDD",
                color="black",
            ))
        ],
        style=Style(
            background="#9999EE",
            color="white",
            width="100%",
            height="100%",
            alignItems="center",
            justifyItems="center"
        )
    )


class TuiRenderer:
    width, height = shutil.get_terminal_size()

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
        return self.calculate_layout_element(dom)

    def calculate_layout_element(self, parent):
        ret = [parent.layout]
        for child in parent.children:
            print(parent.__class__.__name__, parent.layout,
                  child.__class__.__name__, child.style)
            child.parent = parent
            child.layout.width = self.calculate_pos(
                parent.layout.width,
                child.style and child.style.width
            )
            child.layout.height = self.calculate_pos(
                parent.layout.height,
                child.style and child.style.height
            )
            child.layout.top = parent.layout.top + self.calculate_pos(
                parent.layout.height - child.layout.height - parent.layout.top,
                child.style and child.style.top or 0
            )
            child.layout.left = parent.layout.left + self.calculate_pos(
                parent.layout.width - child.layout.width - parent.layout.left,
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
        return ret

    def rgbcolor(self, color: str):
        if color.startswith("#"):
            return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"
        if color in COLORS:
            return ';'.join(map(str, COLORS[color]))
        return ';'.join(map(str, COLORS["black"]))

    def render(self, dom):
        raise NotImplementedError()


class XtermRenderer(TuiRenderer):
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


if __name__ == '__main__':
    dom = Welcome()
    renderer = XtermRenderer()
    if sys.argv[1:] == ["layout"]:
        import json
        print(
            renderer.calculate_layout(dom),
        )
    else:
        print(
            strlist_to_str(
                renderer.render(dom))
        )
        input()

# https://www.xfree86.org/current/ctlseqs.html
