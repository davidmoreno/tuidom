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

    def print(self, *str):
        """
        Indirect call just in case there are optimization oportunities
        """
        print(*str)

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
                f"\033[{position[0]+lineno};{position[1]}H",  # position
                line
            )
