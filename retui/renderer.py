
import logging
from .events import Event
from . import defaults

logger = logging.getLogger(__name__)


class Renderer:
    color = "white"
    background = "blue"
    size = (25, 80)

    def setColor(self, color):
        self.color = defaults.COLORS[color]

    def setBackground(self, color):
        self.background = defaults.COLORS[color]

    def drawSquare(self, orig, size):
        """
        Orig is (width, height). All pairs are like this: (x, y).
        """
        logger.debug("sq %s %s", orig, size)
        pass

    def drawText(self, position, text):
        print(text)
        logger.debug("TEXT %s %s", position, text)
        pass

    def close(self):
        pass

    def readEvent(self) -> Event:
        pass
