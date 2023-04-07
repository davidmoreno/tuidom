
import logging
from .events import Event
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
    strokeStyle = "white"
    fillStyle = "blue"
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

    def fillText(self, text, x, y):
        print(text)
        logger.debug("TEXT %s %s", (x, y), text)
        pass

    def close(self):
        pass

    def setCursor(self, x, y):
        """
        Just to set th eposition of the curso at the end of 
        painting.
        """
        pass

    def flush(self):
        """
        This pass is finished, flush data
        """
        pass

    def readEvent(self) -> Event:
        pass
