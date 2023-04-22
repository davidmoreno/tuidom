import logging
from unittest import TestCase
from retui.component import Component

logger = logging.getLogger(__name__)


class ComponentTestCase(TestCase):
    def test_update_props(self):
        compa = Component(a=1, b=2, c=3)
        compb = Component(a=11, b=2, d=4)

        compa.updateProps(compb)
        logger.debug(compa.props)
        logger.debug(compb.props)

        self.assertIn("a", compa.props)
        self.assertIn("b", compa.props)
        self.assertNotIn("c", compa.props)
        self.assertIn("d", compa.props)

        self.assertEqual(compa.props["a"], 11)
        self.assertEqual(compa.props["b"], 2)
        self.assertEqual(compa.props["d"], 4)
