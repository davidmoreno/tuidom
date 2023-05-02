import os
import shutil
import sys
import termios
import tty
from typing import Generator

from .events import Event, EventMouseClick, EventExit, EventKeyPress, EventMouseClick, EventMouseDown, EventMouseUp
from .renderer import Renderer
from .defaults import COLORS
from retui import defaults


class XtermRenderer(Renderer):
    """
    Implementation for Xterm
    """
    foreground = "white"
    background = "blue"
    lineWidth = 1  # depending on width the stroke will use diferent unicode chars

    stdout = None
    stdin = None
    prev_mouse_buttons = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stdout = sys.stdout
        self.stdin = sys.stdin

        width, height = shutil.get_terminal_size()
        self.width = width
        # TODO Fix last row can not be fill until the end or does a CR
        self.height = height - 1
        self.captureKeyboard(True)
        self.pushScreen()

    def captureKeyboard(self, is_on):
        if is_on:
            fd = self.stdin.fileno()
            self.oldtermios = termios.tcgetattr(fd)
            tty.setcbreak(fd)
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~(termios.ECHO | termios.ICANON)        # lflags
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            print("\033[?1000h")
        else:
            fd = self.stdin.fileno()
            termios.tcsetattr(fd, termios.TCSADRAIN, self.oldtermios)
            print("\033[?10001h")

    def pushScreen(self):
        # save screen state
        print("\033[?1049h")

    def popScreen(self):
        print("\033[?1049l")

    def print(self, *str_or_list):
        """
        Indirect call just in case there are optimization oportunities
        """
        self.stdout.write(strlist_to_str(str_or_list))

    def flush(self):
        self.stdout.flush()

    def close(self):
        # recover saved state
        self.captureKeyboard(False)
        self.popScreen()

    def readEvents(self) -> Generator[Event, None, None]:
        try:
            key = os.read(self.stdin.fileno(), 10)
        except KeyboardInterrupt:
            return EventExit()
        if key in defaults.XTERM_KEYCODES:
            key = defaults.XTERM_KEYCODES[key]

        elif key.startswith(b"\033[M"):
            buttons = int(key[3])
            if buttons == 32:
                buttons = 1
            if buttons == 34:
                buttons = 2
            if buttons == 35:
                buttons = 0
            x = int(key[4])-33
            y = int(key[5])-33
            if buttons:
                yield EventMouseDown(
                    buttons=buttons,
                    position=(x, y)
                )
            else:
                yield EventMouseUp(
                    buttons=buttons,
                    position=(x, y)
                )
                yield EventMouseClick(
                    buttons=self.prev_mouse_buttons,
                    position=(x, y)
                )
            self.prev_mouse_buttons = buttons
            return

        elif len(key) == 1:
            if 0 < ord(key) < 27:
                ckey = chr(ord(key) + ord('A') - 1)
                if ckey == "I":
                    key = "TAB"
                elif ckey == "J":
                    key = "ENTER"
            else:
                key = key.decode("iso8859-15")
        else:
            # just try decode
            try:
                key = key.decode()
            except:
                pass

        yield EventKeyPress(key)

    def rgbcolor(self, color: str):
        """
        From any color string to the xterm ; separated color components
        """
        if color.startswith("#"):
            return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"
        if color in COLORS:
            color = COLORS[color]
            if isinstance(color, tuple):
                return ';'.join(map(str, color))
            if color.startswith("#"):
                return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"

        return ';'.join(map(str, COLORS["black"]))

    def __set_color(self):
        return f"\033[48;2;{self.rgbcolor(self.background)}m\033[38;2;{self.rgbcolor(self.foreground)}m"

    def fillText(self, text, x, y, bold=False, italic=False, underline=False):
        if y < 0 or y > self.height:
            return
        if bold:
            self.print(
                f"\033[1m",
            )
        if italic:
            self.print(
                f"\033[3m",
            )
        if underline:
            self.print(
                f"\033[4m",
            )

        for lineno, line in enumerate(text.split("\n")):
            py = y+lineno
            if py < 0 or py > self.height:
                continue
            self.print(
                self.__set_color(),
                f"\033[{py};{x}H",  # position
                line
            )

        if bold or italic or underline:
            self.print(
                f"\033[0m",  # normal
            )

    def fillRect(self, x, y, width, height):
        self.print(
            self.__set_color(),
            [
                [
                    self.__set_cursor(x, top),
                    " "*width,  # write bg lines
                ]
                for top in range(y, y + height)
            ]
        )

    def setCursor(self, x, y):
        self.print(self.__set_cursor(x, y))

    def setBackgroundColor(self, color):
        if self.background != color:
            self.background = color
            self.print(self.__set_color())

    def setForegroundColor(self, color):
        if self.foreground != color:
            self.foreground = color
            self.print(self.__set_color())

    def setLineWidth(self, width):
        self.lineWidth = width

    def __set_cursor(self, x, y):
        return f"\033[{y+1};{x+1}H",  # position

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

        self.print(self.__set_cursor(x, y))
        self.print(table_chars[1], table_chars[2]*(width-2), table_chars[3])
        for ny in range(y+1, y+height):
            self.print(self.__set_cursor(x, ny))
            self.print(table_chars[7])
            self.print(self.__set_cursor(x+width-1, ny))
            self.print(table_chars[0])
        self.print(self.__set_cursor(x, y+height-1))
        self.print(table_chars[4], table_chars[5]*(width-2), table_chars[6],)

    def breakpoint(self, callback=None, document=None):
        self.captureKeyboard(False)

        self.foreground = "white"
        self.background = "black"
        self.setCursor(1, 1)
        self.fillRect(1, 1, self.width, self.height)
        super().breakpoint(callback, document)

        self.captureKeyboard(True)


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return ''.join(strlist_to_str(x) for x in strl)
