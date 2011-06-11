import unittest
import tempfile
from pkg_resources import ResourceManager
from path import path
import gtk

from baudot.gui import FileManager, DuplicatedFileException
from baudot.core import CharsetConverter

class FileManagerTest(unittest.TestCase):

    def setUp(self):
        self.converter = CharsetConverter()
        self.fm = FileManager()
        self.samples = path(ResourceManager().resource_filename(__package__, "samples"))

    def test_normalize(self):
        self.assertEqual("/var/log/", self.fm._normalize("/var/log/"))
        self.assertEqual("/var/log/", self.fm._normalize("/var/log"))
        self.assertEqual("/var/log/", self.fm._normalize(path("/var/log/")))
        self.assertEqual("/var/log/", self.fm._normalize(path("/var/log/")))
        
    def test_get_filetype(self):
        file = self.samples / "sample1-ISO-8859-1.txt"
        self.assertEqual("text/plain", self.fm._get_mime_type(file))
    
    def test_count_files(self):
        dir = self.samples / "dir1"
        self.assertEqual(9, self.fm.count_files(dir))
        txt = dir / "sample1-ISO-8859-1.txt"
        self.assertEqual(1, self.fm.count_files(txt))

    def test_add_search(self):
        dir = self.samples / "dir1"
        txt = dir / "sample1-ISO-8859-1.txt"
        image = dir / "locked.svg"
        empty = dir / "empty"

        self.assertEqual(0, len(self.fm))
        self.fm.add(dir)
        self.assertEqual(1, len(self.fm))

        dir_row = self.fm.search(dir)
        self.assertIsNotNone(dir_row)
        self.assertEqual(6, len(dir.listdir()))
        self.assertEqual(dir, dir_row[0])
        self.assertEqual(gtk.STOCK_DIRECTORY, dir_row[1])
        self.assertEqual(dir, dir_row[2])
        self.assertEqual("4 items", dir_row[3])
        self.assertEqual("Folder", dir_row[4])
        self.assertIsNone(dir_row[5])
        
        txt_row = self.fm.search(txt)
        self.assertIsNotNone(txt_row)
        self.assertEqual(txt, txt_row[0])
        self.assertEqual(gtk.STOCK_FILE, txt_row[1])
        self.assertEqual("sample1-ISO-8859-1.txt", txt_row[2])
        self.assertEqual("1.16 KB", txt_row[3])
        self.assertEqual("text/plain", txt_row[4])
        self.assertEqual("ISO-8859-1", txt_row[5])
        
        self.assertTrue(image.exists())
        self.assertIsNone(self.fm.search(image))
        
        self.assertTrue(empty.exists())
        self.assertIsNone(self.fm.search(empty))

        self.fm.add(empty)
        self.assertEqual(2, len(self.fm))

    def test_add_duplicate(self):
        dir = self.samples / "dir1"
        self.assertEqual(0, len(self.fm))
        self.fm.add(dir)
        self.assertEqual(1, len(self.fm))
        self.assertRaises(DuplicatedFileException, self.fm.add, dir)
        self.assertEqual(1, len(self.fm))

    def test_convert_copy(self):
        orig = self.samples / "dir1"
        copy = path(tempfile.mkdtemp())

        try:
            self.fm.add(orig)
            self.fm.convert_files("ISO-8859-1", copy)
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
            self.fm.add(copy)
            self.fm.convert_files("ISO-8859-1")
            converted = copy / "sample2-UTF-8.txt"
            self.assertTrue(converted.exists())
            self.assertEqual("ISO-8859-1", self.converter.detect_encoding(converted).charset)
        finally:
            tmp.rmtree()
            self.assertFalse(tmp.exists())
    
    def test_create_backup(self):
        tmp = path(tempfile.mkdtemp())
        try:
            orig = tmp / "orig.txt"
            backup = tmp / "orig.txt~"
            
            orig.touch()
            self.assertTrue(orig.exists())
            self.assertFalse(backup.exists())
            self.fm._create_backup(orig)
            self.assertTrue(backup.exists())
        finally:
            tmp.rmtree()
            self.assertFalse(tmp.exists())
            