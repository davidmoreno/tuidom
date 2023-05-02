from dataclasses import dataclass
from typing import Generator, Tuple
from retui.events import Event, EventKeyPress
from retui.renderer import Renderer


@dataclass
class ScreenChar:
    char: str = " "
    bg: str = ""
    fg: str = ""
    bold: bool = False
    italic: bool = False
    underline: bool = False

    def update(self, **kwargs):
        return ScreenChar(
            char=kwargs.get("char", self.char),
            fg=kwargs.get("fg", self.fg),
            bg=kwargs.get("bg", self.bg),
            bold=kwargs.get("bold", self.bold),
            italic=kwargs.get("italic", self.italic),
            underline=kwargs.get("underline", self.underline),
        )


class BufferedRenderer(Renderer):
    renderer: Renderer
    screen: list[ScreenChar]
    screen_back: list[ScreenChar]
    cursor: Tuple[int, int] = (0, 0)

    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height
        self.screen = [
            ScreenChar()
            for _ in range(0, self.width*self.height)
        ]
        self.screen_back = [
            ScreenChar()
            for _ in range(0, self.width*self.height)
        ]

    def pos(self, x, y):
        return x + (y*self.width)

    def setCursor(self, x, y):
        self.cursor = (x, y)

    def fillRect(self, x, y, width, height):
        cur = ScreenChar(
            char=" ",
            bg=self.fillStyle,
            fg=self.strokeStyle,
        )
        for h in range(y, y+height):
            for p in range(self.pos(x, h), self.pos(x+width, h)):
                self.screen[p] = cur

    def fillText(self, text, x, y, bold=False, italic=False, underline=False):
        for lineno, line in enumerate(text.split("\n")):
            py = y+lineno
            if py < 0 or py > self.height:
                continue
            for n, c in enumerate(line):
                self.screen[self.pos(x+n, py)] = ScreenChar(
                    c,
                    bg=self.fillStyle,
                    fg=self.strokeStyle,
                    bold=bold,
                    italic=italic,
                    underline=underline,
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

        sc = ScreenChar(bg=self.fillStyle, fg=self.strokeStyle)
        self.screen[self.pos(x, y)] = sc.update(char=table_chars[1])
        for p in range(x+1, x+width-1):
            self.screen[self.pos(p, y)] = sc.update(char=table_chars[2])
        self.screen[self.pos(x+width-1, y)] = sc.update(char=table_chars[3])

        for ny in range(y+1, y+height):
            self.screen[self.pos(x, ny)] = sc.update(char=table_chars[7])
            self.screen[self.pos(x+width-1, ny)
                        ] = sc.update(char=table_chars[0])

        ny = y+height-1
        self.screen[self.pos(x, ny)] = sc.update(char=table_chars[4])
        for p in range(x+1, x+width-1):
            self.screen[self.pos(p, ny)] = sc.update(char=table_chars[5])
        self.screen[self.pos(x+width-1, ny)] = sc.update(char=table_chars[6])

    def readEvents(self) -> Generator[Event, None, None]:
        for ev in self.renderer.readEvents():
            if isinstance(ev, EventKeyPress) and ev.keycode == "CONTROL-L":
                self.screen_back = [
                    ScreenChar()
                    for _ in range(0, self.width*self.height)
                ]
                self.flush()
        yield ev

    def flush(self):
        p = 0
        prev_char = ScreenChar()
        screen = self.screen
        screen_back = self.screen_back

        pos = (-1, -1)
        for y in range(0, self.height):
            for x in range(0, self.width):
                cur = screen[p]
                prev = screen_back[p]
                if cur != prev:
                    if pos != (x, y):
                        self.renderer.setCursor(x, y)
                        pos = (x, y)
                    if prev_char.bg != cur.bg:
                        self.renderer.setBackgroundColor(cur.bg)
                    if prev_char.fg != cur.fg:
                        self.renderer.setForegroundColor(cur.fg)
                    self.renderer.print(cur.char)
                    pos = (x+1, y)
                p += 1

        self.renderer.setCursor(*self.cursor)
        self.renderer.flush()
        self.screen_back = screen
        self.screen = screen_back

    def close(self):
        return self.renderer.close()
