import os
import shutil
import sys
import termios
import tty

from .events import EventKeyPress
from .renderer import Renderer
from .defaults import COLORS


class XtermRenderer(Renderer):
    """
    Implementation for Xterm
    """

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

        # save screen state
        # print("\033[?1049h;")

    def print(self, *str_or_list):
        """
        Indirect call just in case there are optimization oportunities
        """
        print(strlist_to_str(str_or_list))

    def close(self):
        # recover saved state
        # print("\033[?1049l;")

        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self.oldtermios)

    def readEvent(self):
        key = os.read(sys.stdin.fileno(), 1)

        if 0 < ord(key) < 27:
            key = chr(ord(key) + ord('A') - 1)
            if key == "I":
                key = "TAB"
            elif key == "J":
                key = "ENTER"
            else:
                key = f"CONTROL+{key}"
            return EventKeyPress(key)
        return EventKeyPress(key.decode("iso8859-15"))

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
        return f"\033[48;2;{self.rgbcolor(self.fillStyle)}m\033[38;2;{self.rgbcolor(self.strokeStyle)}m"

    def fillText(self, text, x, y):
        for lineno, line in enumerate(text.split("\n")):
            self.print(
                self.__set_color(),
                f"\033[{y+lineno};{x}H",  # position
                line
            )

    def fillRect(self, x, y, width, height):
        self.print(
            self.__set_color(),
            [
                [
                    f"\033[{top};{x}H",  # position
                    " "*width,  # write bg lines
                ]
                for top in range(y, y + height)
            ]
        )

    def strokeRect(self, x, y, width, height):
        """
        Draw rects with border
        """
        raise NotImplemented("WIP")


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return ''.join(strlist_to_str(x) for x in strl)
