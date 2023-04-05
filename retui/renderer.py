
import logging

logger = logging.getLogger(__name__)


class Renderer:
    color = "white"
    background = "blue"

    def setColor(self, color):
        self.color = color

    def setBackground(self, color):
        self.background = color

    def drawSquare(self, orig, size):
        logger.debug("sq %s %s", orig, size)
        pass

    def drawText(self, position, text):
        print(text)
        logger.debug("TEXT %s %s", position, text)
        pass

    def close(self):
        pass

    def readEvent(self) -> 'Event':
        pass
