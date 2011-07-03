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
        dir = self.samples / "dir1"
        txt = dir / "sample1-ISO-8859-1.txt"
        image = dir / "locked.svg"
        empty = dir / "empty"

        self.assertEqual(0, len(self.fm))
        cmd = self.fm.add(dir)
        cmd.start()
        cmd.join()

        self.assertEqual(1, len(self.fm))

        dir_row = cmd.search(dir)
        self.assertIsNotNone(dir_row)
        self.assertEqual(6, len(dir.listdir()))
        self.assertEqual(dir, dir_row[0])
        self.assertEqual(gtk.STOCK_DIRECTORY, dir_row[1])
        self.assertEqual(dir, dir_row[2])
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
        dir = self.samples / "dir1"
        self.assertEqual(0, len(self.fm))
        cmd = self.fm.add(dir)
        cmd.start()
        cmd.join()
        self.assertEqual(1, len(self.fm))
        class Namespace(object): pass
        ns = Namespace()
        ns.duplicated = False
        def on_command_aborted(cmd, msg):
            ns.duplicated = True
        cmd = self.fm.add(dir)
        cmd.connect("command-aborted", on_command_aborted)
        cmd.start()
        cmd.join()
        self.assertTrue(ns.duplicated) 
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
    