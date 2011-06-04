import unittest
import tempfile

from md5 import md5
from pkg_resources import resource_filename
from path import path

from baudot.core import CharsetConverter

class FileEncoderTest(unittest.TestCase):

    def setUp(self):
        self.converter = CharsetConverter()
        self.samples = path(resource_filename(__package__, "samples"))

    def test_detection(self):
        file = self.samples / "sample1-ISO-8859-1.txt"
        self.assertEquals("ISO-8859-1", self.converter.detect_encoding(file))
        file = self.samples / "sample1-UTF-8.txt"
        self.assertEquals("UTF-8", self.converter.detect_encoding(file))

    def test_convertion_from_iso_to_utf(self):
        # setup files
        iso = self.samples / "sample1-ISO-8859-1.txt"
        iso_checksum = self.__checksum(iso)
        utf = self.samples / "sample1-UTF-8.txt"
        utf_checksum = self.__checksum(utf)
        # create temp file
        fd, filename = tempfile.mkstemp(prefix="baudot")
        tmp = path(filename)
        tmp_checksum = self.__checksum(tmp)
        # validate before convertion
        self.assertNotEquals(iso_checksum, utf_checksum)
        self.assertNotEquals(tmp_checksum, utf_checksum)
        self.assertNotEquals(iso_checksum, tmp_checksum)
        # convert files
        self.converter.convert_encoding(iso, tmp, "ISO-8859-1", "UTF-8")
        tmp_checksum = self.__checksum(tmp)
        # validate output
        self.assertNotEquals(iso_checksum, tmp_checksum)
        self.assertEquals(tmp_checksum, utf_checksum)
        tmp.remove()
        self.assertFalse(tmp.exists())

    def test_get_encodings(self):
        available = self.converter.get_encodings()
        self.assertIn("UTF-8", available)
        self.assertIn("ISO-8859-1", available)
        self.assertIn("windows-1251", available)

    def __checksum(self, file):
        block_size = 0x10000
        def upd(m, data):
            m.update(data)
            return m
        fd = open(file, "rb")
        try:
            contents = iter(lambda: fd.read(block_size), "")
            m = reduce(upd, contents, md5())
            return m.hexdigest()
        finally:
            fd.close()
