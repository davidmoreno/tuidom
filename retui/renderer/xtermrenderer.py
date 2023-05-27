import os
import shutil
import signal
import sys
import termios
import tty
from typing import Generator

from retui.events import (
    Event,
    EventMouseClick,
    EventExit,
    EventKeyPress,
    EventMouseDown,
    EventMouseUp,
)
from retui.renderer import Renderer, ScreenChar
from retui import defaults


class XtermRenderer(Renderer):
    """
    Implementation for Xterm
    """

    def __init__(self, **kwargs):
        self.stdout = sys.stdout
        self.stdin = sys.stdin

        signal.signal(signal.SIGWINCH, lambda a, b: self.update_terminal_resize())
        self.update_terminal_resize()
        super().__init__(**kwargs)

        self.captureKeyboard(True)
        self.pushScreen()

    def update_terminal_resize(self):
        width, height = shutil.get_terminal_size()
        self.width = width
        self.height = height - 1
        self.redraw()

    def captureKeyboard(self, is_on):
        if is_on:
            fd = self.stdin.fileno()
            self.oldtermios = termios.tcgetattr(fd)
            tty.setcbreak(fd)
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~(termios.ECHO | termios.ICANON)  # lflags
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

    def flush(self):
        super().flush()
        self.print(self.__set_cursor(self.cursor[0], self.cursor[1]))
        self.stdout.flush()

    def close(self):
        # recover saved state
        self.captureKeyboard(False)
        self.popScreen()

    prev_mouse_buttons = []

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
            x = int(key[4]) - 33
            y = int(key[5]) - 33
            if buttons:
                yield EventMouseDown(buttons=buttons, position=(x, y))
            else:
                yield EventMouseUp(buttons=buttons, position=(x, y))
                yield EventMouseClick(buttons=self.prev_mouse_buttons, position=(x, y))
            self.prev_mouse_buttons = buttons
            return

        elif len(key) == 1:
            if 0 < ord(key) < 27:
                ckey = chr(ord(key) + ord("A") - 1)
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

        if key == "CONTROL-L":
            self.redraw()

        yield EventKeyPress(key)

    def rgbcolor(self, color: str):
        """
        From any color string to the xterm ; separated color components
        """
        if color.startswith("#"):
            return f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"
        if color in defaults.COLORS:
            color = defaults.COLORS[color]
            if isinstance(color, tuple):
                return ";".join(map(str, color))
            if color.startswith("#"):
                return (
                    f"{int(color[1:3], 16)};{int(color[3:5], 16)};{int(color[5:7], 16)}"
                )

        return ";".join(map(str, defaults.COLORS["black"]))

    def __set_color(self, bg, fg):
        return f"\033[48;2;{self.rgbcolor(bg)}m\033[38;2;{self.rgbcolor(fg)}m"

    def renderLine(self, x: int, y: int, chr: ScreenChar):
        if chr.bold:
            self.print(
                f"\033[1m",
            )
        if chr.italic:
            self.print(
                f"\033[3m",
            )
        if chr.underline:
            self.print(
                f"\033[4m",
            )

        self.print(
            self.__set_color(chr.background, chr.foreground),
            self.__set_cursor(x, y),
            chr.text,
        )

        if chr.bold or chr.italic or chr.underline:
            self.print(
                f"\033[0m",  # normal
            )

    def __set_cursor(self, x, y):
        return (f"\033[{y+1};{x+1}H",)  # position

    def breakpoint(self, callback=None, document=None):
        self.captureKeyboard(False)
        super().breakpoint(callback, document)
        self.captureKeyboard(True)
