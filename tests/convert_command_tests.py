import unittest
import tempfile
from pkg_resources import ResourceManager
from path import path

from baudot.gui import ConvertCommand

class FileManagerTest(unittest.TestCase):

    def setUp(self):
        self.cmd = ConvertCommand(None, None, None)
        self.samples = path(ResourceManager().resource_filename(__package__, "samples"))

    # pylint: disable-msg=W0212
    # Required for unit tests
    def test_create_backup(self):
        tmp = path(tempfile.mkdtemp())
        try:
            orig = tmp / "orig.txt"
            backup = tmp / "orig.txt~"
            
            orig.touch()
            self.assertTrue(orig.exists())
            self.assertFalse(backup.exists())
            self.cmd._create_backup(orig)
            self.assertTrue(backup.exists())
        finally:
            tmp.rmtree()
            self.assertFalse(tmp.exists())
            