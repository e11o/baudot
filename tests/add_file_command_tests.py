import unittest
from pkg_resources import ResourceManager
from path import path

from baudot.gui import AddFileCommand

class AddFileCommandTest(unittest.TestCase):

    def setUp(self):
        self.cmd = AddFileCommand(None, None)
        self.samples = path(ResourceManager().resource_filename(__package__, "samples"))

    # pylint: disable-msg=W0212
    # Required for unit tests
    def test_get_filetype(self):
        text_file = self.samples / "sample1-ISO-8859-1.txt"
        self.assertEqual("text/plain", self.cmd._get_mime_type(text_file))
    
    # pylint: disable-msg=W0212
    # Required for unit tests
    # pylint: disable-msg=W0212
    # Required for unit tests
    def test_count_files(self):
        dir1 = self.samples / "dir1"
        self.assertEqual(9, self.cmd._count_files(dir1))
        txt = dir1 / "sample1-ISO-8859-1.txt"
        self.assertEqual(1, self.cmd._count_files(txt))
