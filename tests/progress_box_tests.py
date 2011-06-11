import unittest

from baudot.gui import ProgressBox


class ProgressBoxTest(unittest.TestCase):

    def test_change_charset(self):
        box = ProgressBox()
        self.assertIsNotNone(box)
        