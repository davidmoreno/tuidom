#!/usr/bin/python3

import logging
import unittest

from retui.tests import *
from retui import document
from retui.renderer import Renderer

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    document.default_renderer = Renderer
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Start TESTS")
    unittest.main()
