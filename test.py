#!/usr/bin/python3

import logging
import unittest

from tests.retui import *
from tests.tuidom import *

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Start TESTS")
    unittest.main()
