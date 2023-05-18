from dataclasses import dataclass, field
from enum import Enum
import logging
import sys
from typing import Generator

from .events import Event, EventExit, EventKeyPress
from . import defaults

logger = logging.getLogger(__name__)


@dataclass
class ScreenChar:
    class FontModifier(Enum):
        BOLD = 1
        ITALIC = 2
        UNDERLINE = 3

    text: str = " "
    background: str = ""
    foreground: str = ""
    fontModifier: set[FontModifier] = field(default_factory=set)
    zIndex: int = 0

    def update(self, **kwargs):
        return ScreenChar(
            text=kwargs.get("char", self.text),
            foreground=kwargs.get("fg", self.foreground),
            background=kwargs.get("bg", self.background),
            fontModifier=kwargs.get("fontModifier", self.fontModifier),
            zIndex=kwargs.get("zIndex", self.zIndex),
        )

    @property
    def bold(self):
        return ScreenChar.FontModifier.BOLD in self.fontModifier

    @property
    def italic(self):
        return ScreenChar.FontModifier.ITALIC in self.fontModifier

    @property
    def underline(self):
        return ScreenChar.FontModifier.UNDERLINE in self.fontModifier


class Renderer:
    """
    Base class for all renderers.

    Must implement all drawing functions.

    Will call close before exit.

    The renderer is also in charge of reading events,
    as keystrokes, mouse clicks and so on.
    """

    foreground = "white"
    background = "blue"
    lineWidth = 1  # depending on width the stroke will use diferent unicode chars

    width = 80
    height = 25

    translate = (0, 0)
    clipping = ((0, 0), (80, 25))
    zIndex = 0
    translateStack = [(0, 0)]
    clippingStack = [(80, 25)]
    stdout = sys.stdout
    stdin = sys.stdin

    def __init__(self):
        """
        Inheritors, set width and height before calling super().__init__()
        """
        self.clipping = ((0, 0), (self.width, self.height))
        self.clippingStack = [self.clipping]

        self.screen = [ScreenChar() for _ in range(0, self.width * self.height)]
        self.screen_back = [ScreenChar() for _ in range(0, self.width * self.height)]

    def close(self):
        pass

    def renderLine(self, x: int, y: int, chr: ScreenChar):
        """
        Renders a line, given the data at chr, at pos xy
        """
        pass

    def pushTranslate(self, trns):
        self.translateStack.append(trns)
        self.translate = trns

    def popTranslate(self):
        self.translateStack.pop()
        self.translate = self.translateStack[-1]
        return self.translate

    def pushClipping(self, clipping):
        self.clippingStack.append(clipping)
        self.clipping = clipping

    def popClipping(self):
        self.clippingStack.pop()
        self.clipping = self.clippingStack[-1]
        return self.clipping

    def addZIndex(self, z_index):
        self.zIndex += z_index

    def clip(self, x, y):
        x = min(max(x, self.clipping[0][0]), self.clipping[1][0])
        y = min(max(y, self.clipping[0][1]), self.clipping[1][1])
        return (x, y)

    def pos(self, x, y):
        return x + (y * self.width)

    def setBackground(self, color):
        self.background = color

    def setForeground(self, color):
        self.foreground = color

    def setLineWidth(self, width):
        self.lineWidth = width

    def drawChar(self, x: int, y: int, char: ScreenChar):
        if x < self.clipping[0][0]:
            return False
        elif x >= self.clipping[1][0]:
            return False
        if y < self.clipping[0][1]:
            return False
        elif y >= self.clipping[1][1]:
            return False

        pos = self.pos(x, y)
        if self.screen[pos].zIndex > self.zIndex:
            return

        self.screen[pos] = char.update(zIndex=self.zIndex)

    def setCursor(self, x, y):
        x += self.translate[0]
        y += self.translate[1]
        self.cursor = (x, y)

    def fillRect(self, x, y, width, height):
        x += self.translate[0]
        y += self.translate[1]
        cur = ScreenChar(
            text=" ",
            background=self.background,
            foreground=self.foreground,
            zIndex=self.zIndex,
        )
        mx = x + width
        my = y + height
        if x > self.clipping[1][0] or x < self.clipping[0][0]:
            return
        if y > self.clipping[1][1] or y < self.clipping[0][1]:
            return

        x, y = self.clip(x, y)
        mx, my = self.clip(x + width, y + height)

        z_index = self.zIndex
        for h in range(y, my):
            for p in range(self.pos(x, h), self.pos(mx, h)):
                if self.screen[p].zIndex <= z_index:
                    self.screen[p] = cur

    def fillText(self, text, x, y, bold=False, italic=False, underline=False):
        x += self.translate[0]
        y += self.translate[1]
        for lineno, line in enumerate(text.split("\n")):
            py = y + lineno
            if py < 0 or py > self.height:
                continue
            for n, c in enumerate(line):
                self.drawChar(
                    x + n,
                    py,
                    ScreenChar(
                        c,
                        background=self.background,
                        foreground=self.foreground,
                    ),
                )

    def fillStroke(self, x, y, width, height):
        """
        Draw rects with border
        """
        self.fillRect(x, y, width, height)
        # if self.lineWidth == 0:
        #     table_chars = "╭╮╰╯┄┆"
        if self.lineWidth == 1:
            table_chars = "│┌─┐└─┘│"
        elif self.lineWidth == 2:
            table_chars = "┃┏━┓┗━┛┃"
        elif self.lineWidth == 3:
            table_chars = "║╔═╗╚═╝║"
        elif self.lineWidth >= 4:
            table_chars = "▐▛▀▜▙▄▟▌"

        sc = ScreenChar(background=self.background, foreground=self.foreground)
        self.drawChar(x, y, sc.update(char=table_chars[1]))
        for p in range(x + 1, x + width - 1):
            self.drawChar(p, y, sc.update(char=table_chars[2]))
        self.drawChar(x + width - 1, y, sc.update(char=table_chars[3]))

        for ny in range(y + 1, y + height):
            self.drawChar(x, ny, sc.update(char=table_chars[7]))
            self.drawChar(x + width - 1, ny, sc.update(char=table_chars[0]))

        ny = y + height - 1
        self.drawChar(x, ny, sc.update(char=table_chars[4]))
        for p in range(x + 1, x + width - 1):
            self.drawChar(p, ny, sc.update(char=table_chars[5]))
        self.drawChar(x + width - 1, ny, sc.update(char=table_chars[6]))

    def readEvents(self) -> Generator[Event, None, None]:
        return []

    def flush(self):
        p = 0
        prev_char = ScreenChar()
        screen = self.screen
        screen_back = self.screen_back

        pos = (-1, -1)
        line = ""

        def dumpline():
            nonlocal line
            if not line:
                return
            x, y = pos
            x -= len(line)
            self.renderLine(x, y, prev_char.update(char=line))
            line = ""

        for y in range(0, self.height):
            for x in range(0, self.width):
                cur = screen[p]
                prev = screen_back[p]
                if cur != prev:
                    # skipped chars
                    if pos != (x, y):
                        dumpline()
                        pos = (x, y)
                    # change bg
                    if prev_char.background != cur.background:
                        dumpline()
                        prev_char = cur
                    # change fg
                    if prev_char.foreground != cur.foreground:
                        dumpline()
                        prev_char = cur
                    # change mods
                    if prev_char.fontModifier != cur.fontModifier:
                        dumpline()
                        prev_char = cur

                    # store more chars on this line
                    line += cur.text
                    # uncomment to zindex debug
                    # line += str(cur.zIndex)
                    pos = (x + 1, y)
                p += 1
        dumpline()

        self.screen_back = screen
        self.screen = screen_back
        for char in self.screen:
            char.zIndex = 0

    def close(self):
        pass

    def breakpoint(self, callback=None, document=None):
        """
        set up to do a breakpoint to debug.
        may need to clean screen, reenable echo and whatnot

        Can call something after terminal is ready
        """
        if callback:
            callback()
        import IPython

        print("Started ipython terminal. Control+D to continue.")
        print()
        IPython.start_ipython(
            user_ns={
                "document": document,
                "renderer": self,
            }
        )

    def print(self, *str_or_list):
        """
        Indirect call just in case there are optimization oportunities
        """
        self.stdout.write(strlist_to_str(str_or_list))


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return "".join(strlist_to_str(x) for x in strl)
