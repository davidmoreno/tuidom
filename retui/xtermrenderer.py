import os
import shutil
import sys
import termios
import tty

from .events import EventKeyPress
from .renderer import Renderer


class XtermRenderer(Renderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        width, height = shutil.get_terminal_size()
        self.size = (width, height)

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

    def drawText(self, position, text):
        for lineno, line in enumerate(text.split("\n")):
            self.print(
                f"\033[{position[1]+lineno};{position[0]}H",  # position
                line
            )

    def setBackground(self, color):
        super().setBackground(color)
        self.background = ';'.join(str(x) for x in self.background)
        self.print(f"\033[48;2;{self.background}")

    def setColor(self, color):
        super().setColor(color)
        self.color = ';'.join(str(x) for x in self.color)
        self.print(f"m\033[38;2;{self.color}m")

    def drawSquare(self, orig, size):
        self.print(
            [
                # colors
                [
                    f"\033[{top};{orig[1]}H",  # position
                    " "*size[1],  # write bg lines
                ]
                for top in range(orig[0], orig[0] + size[0])
            ]
        )


def strlist_to_str(strl):
    if isinstance(strl, str):
        return strl
    return ''.join(strlist_to_str(x) for x in strl)
