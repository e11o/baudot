import unittest
import tempfile

from pkg_resources import resource_filename
from path import path

from baudot.gui import CharsetChooser

class CharsetChooserTest(unittest.TestCase):

    def setUp(self):
        self.samples = path(resource_filename(__package__, "samples"))

    def test_change_charset(self):
        file = self.samples / "sample1-ISO-8859-1.txt"
        chooser = CharsetChooser(file, "ISO-8859-1")
        self.assertIsNotNone(chooser)
        