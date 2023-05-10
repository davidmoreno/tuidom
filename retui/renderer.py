import logging
from typing import Generator

from .events import Event, EventExit, EventKeyPress
from . import defaults

logger = logging.getLogger(__name__)


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

    def fillRect(self, x, y, width, height):
        """
        Orig is (width, height). All pairs are like this: (x, y).
        """
        logger.debug("sq %s %s", (x, y), (width, height))
        pass

    def fillStroke(self, x, y, width, height):
        raise NotImplementedError("WIP")

    def fillText(self, text, x, y, bold=False, italic=False, underline=False):
        print(text)
        logger.debug("TEXT %s %s", (x, y), text)
        pass

    def close(self):
        pass

    def pushZIndex(self, z_index):
        pass

    def popZIndex(self):
        pass

    def setCursor(self, x, y):
        """
        Just to set th eposition of the curso at the end of
        painting.
        """
        pass

    def setBackground(self, color):
        self.background = color

    def setForeground(self, color):
        self.foreground = color

    def setLineWidth(self, width):
        pass

    def flush(self):
        """
        This pass is finished, flush data
        """
        pass

    def readEvents(self) -> Generator[Event, None, None]:
        yield EventKeyPress("ESC")

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
        pass
