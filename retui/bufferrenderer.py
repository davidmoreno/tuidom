from dataclasses import dataclass, field
from enum import Enum
from typing import Generator, Tuple
from retui.events import Event, EventKeyPress
from retui.renderer import Renderer


@dataclass
class ScreenChar:
    class FontModifier(Enum):
        BOLD = 1
        ITALIC = 2
        UNDERSCORE = 3

    char: str = " "
    bg: str = ""
    fg: str = ""
    fontModifier: set[FontModifier] = field(default_factory=set)
    zIndex: int = 0

    def update(self, **kwargs):
        return ScreenChar(
            char=kwargs.get("char", self.char),
            fg=kwargs.get("fg", self.fg),
            bg=kwargs.get("bg", self.bg),
            fontModifier=kwargs.get("fontModifier", self.fontModifier),
            zIndex=kwargs.get("zIndex", self.zIndex),
        )


class BufferedRenderer(Renderer):
    renderer: Renderer
    screen: list[ScreenChar]
    screen_back: list[ScreenChar]
    cursor: Tuple[int, int] = (0, 0)
    max_x: int
    max_y: int
    min_x: int
    min_y: int
    zIndex: int = 0

    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height
        self.max_x = self.width
        self.max_y = self.height
        self.min_x = 0
        self.min_y = 0

        self.screen = [ScreenChar() for _ in range(0, self.width * self.height)]
        self.screen_back = [ScreenChar() for _ in range(0, self.width * self.height)]

    def pos(self, x, y):
        return x + (y * self.width)

    def clip(self, x, y):
        if x < self.min_x:
            x = self.min_x
        elif x > self.max_x:
            x = self.max_x
        if y < self.min_y:
            y = self.min_y
        elif y > self.max_y:
            y = self.max_y

        return x, y

    def addZIndex(self, z_index):
        self.zIndex += z_index

    def drawChar(self, x: int, y: int, char: ScreenChar):
        if x < self.min_x:
            return False
        elif x >= self.max_x:
            return False
        if y < self.min_y:
            return False
        elif y >= self.max_y:
            return False

        pos = self.pos(x, y)
        if self.screen[pos].zIndex > self.zIndex:
            return

        self.screen[pos] = char.update(zIndex=self.zIndex)

    def setCursor(self, x, y):
        self.cursor = (x, y)

    def fillRect(self, x, y, width, height):
        cur = ScreenChar(
            char=" ",
            bg=self.background,
            fg=self.foreground,
            zIndex=self.zIndex,
        )
        mx = x + width
        my = y + height
        if x > self.max_x or x < self.min_x:
            return
        if y > self.max_y or y < self.min_y:
            return

        x, y = self.clip(x, y)
        mx, my = self.clip(x + width, y + height)

        z_index = self.zIndex
        for h in range(y, my):
            for p in range(self.pos(x, h), self.pos(mx, h)):
                if self.screen[p].zIndex <= z_index:
                    self.screen[p] = cur

    def fillText(self, text, x, y, bold=False, italic=False, underline=False):
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
                        bg=self.background,
                        fg=self.foreground,
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

        sc = ScreenChar(bg=self.background, fg=self.foreground)
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
        for ev in self.renderer.readEvents():
            if isinstance(ev, EventKeyPress) and ev.keycode == "CONTROL-L":
                self.screen_back = [
                    ScreenChar() for _ in range(0, self.width * self.height)
                ]
                self.flush()
            yield ev

    def flush(self):
        p = 0
        prev_char = ScreenChar()
        screen = self.screen
        screen_back = self.screen_back

        pos = (-1, -1)
        line = ""

        def dumpline():
            x, y = pos
            nonlocal line
            if line:
                self.renderer.setBackground(prev_char.bg)
                self.renderer.setForeground(prev_char.fg)
                bold = ScreenChar.FontModifier.BOLD in prev_char.fontModifier
                underline = ScreenChar.FontModifier.UNDERSCORE in prev_char.fontModifier
                italic = ScreenChar.FontModifier.ITALIC in prev_char.fontModifier
                self.renderer.fillText(
                    line,
                    x - len(line),
                    y,
                    bold=bold,
                    underline=underline,
                    italic=italic,
                )
                line = ""

        for y in range(0, self.height):
            for x in range(0, self.width):
                cur = screen[p]
                prev = screen_back[p]
                if cur != prev:
                    if pos != (x, y):
                        dumpline()
                        pos = (x, y)
                    if prev_char.bg != cur.bg:
                        dumpline()
                        prev_char = cur
                    if prev_char.fg != cur.fg:
                        dumpline()
                        prev_char = cur
                    if prev_char.fontModifier != cur.fontModifier:
                        dumpline()
                        prev_char = cur
                    line += cur.char
                    # line += str(cur.zIndex)
                    pos = (x + 1, y)
                p += 1
        dumpline()

        self.renderer.setCursor(*self.cursor)
        self.renderer.flush()
        self.screen_back = screen
        self.screen = screen_back
        for char in self.screen:
            char.zIndex = 0

    def close(self):
        return self.renderer.close()
