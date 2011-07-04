import unittest
import tempfile
from pkg_resources import ResourceManager
from path import path
import gtk

from baudot.gui import FileManager
from baudot.core import CharsetConverter

class FileManagerTest(unittest.TestCase):

    def setUp(self):
        self.converter = CharsetConverter()
        self.fm = FileManager()
        self.samples = path(ResourceManager().resource_filename(__package__, "samples"))

    def test_add_search(self):
        dir1 = self.samples / "dir1"
        txt = dir1 / "sample1-ISO-8859-1.txt"
        image = dir1 / "locked.svg"
        empty = dir1 / "empty"

        self.assertEqual(0, len(self.fm))
        cmd = self.fm.add(dir1)
        cmd.start()
        cmd.join()

        self.assertEqual(1, len(self.fm))

        dir_row = cmd.search(dir1)
        self.assertIsNotNone(dir_row)
        self.assertEqual(6, len(dir1.listdir()))
        self.assertEqual(dir1, dir_row[0])
        self.assertEqual(gtk.STOCK_DIRECTORY, dir_row[1])
        self.assertEqual(dir1, dir_row[2])
        self.assertEqual("4 items", dir_row[3])
        self.assertEqual("Folder", dir_row[4])
        self.assertIsNone(dir_row[5])
        
        txt_row = cmd.search(txt)
        self.assertIsNotNone(txt_row)
        self.assertEqual(txt, txt_row[0])
        self.assertEqual(gtk.STOCK_FILE, txt_row[1])
        self.assertEqual("sample1-ISO-8859-1.txt", txt_row[2])
        self.assertEqual("1.16 KB", txt_row[3])
        self.assertEqual("text/plain", txt_row[4])
        self.assertEqual("ISO-8859-1", txt_row[5])
        
        self.assertTrue(image.exists())
        self.assertIsNone(cmd.search(image))
        
        self.assertTrue(empty.exists())
        self.assertIsNone(cmd.search(empty))

        cmd = self.fm.add(empty)
        cmd.start()
        cmd.join()
        
        self.assertEqual(2, len(self.fm))

    def test_add_duplicate(self):
        dir1 = self.samples / "dir1"
        self.assertEqual(0, len(self.fm))
        cmd = self.fm.add(dir1)
        cmd.start()
        cmd.join()
        self.assertEqual(1, len(self.fm))
        mock = MockListener()
        cmd = self.fm.add(dir1)
        cmd.connect("command-aborted", mock.slot)
        cmd.start()
        cmd.join()
        self.assertTrue(mock.invoked) 
        self.assertEqual(1, len(self.fm))

    def test_convert_copy(self):
        orig = self.samples / "dir1"
        copy = path(tempfile.mkdtemp())

        try:
            cmd = self.fm.add(orig)
            cmd.start()
            cmd.join()
            cmd = self.fm.convert("ISO-8859-1", copy)
            cmd.start()
            cmd.join()
            converted = copy / "sample2-UTF-8.txt"
            self.assertTrue(converted.exists())
            self.assertEqual("ISO-8859-1", self.converter.detect_encoding(converted).charset)
        finally:
            copy.rmtree()
    
    def test_convert_in_place(self):
        orig = self.samples / "dir1"
        tmp = path(tempfile.mkdtemp())
        copy = tmp / "copy"
        orig.copytree(copy)
        try:
            cmd = self.fm.add(copy)
            cmd.start()
            cmd.join()
            cmd = self.fm.convert("ISO-8859-1")
            cmd.start()
            cmd.join()
            converted = copy / "sample2-UTF-8.txt"
            self.assertTrue(converted.exists())
            self.assertEqual("ISO-8859-1", self.converter.detect_encoding(converted).charset)
        finally:
            tmp.rmtree()
            self.assertFalse(tmp.exists())


class MockListener(object):
    def __init__(self):
        self.args = None
        self.invoked = False
        
    def slot(self, *args):
        self.args = args
        self.invoked = True
            
    