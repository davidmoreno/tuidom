#!/usr/bin/python3

import logging
import unittest

from retui.tests import *

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Start TESTS")
    unittest.main()
