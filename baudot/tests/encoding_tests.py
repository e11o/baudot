import unittest
import sys, os, tempfile

from md5 import md5
from baudot.core import FileEncoder

class EncodingTest(unittest.TestCase):

    def setUp(self):
        self.encoder = FileEncoder()
        pathname = os.path.abspath("baudot")
        self.samples_path = os.path.join(pathname, "tests", "samples")

    def test_detection(self):
        file = os.path.join(self.samples_path, "sample1-ISO-8859-1.txt")
        self.assertEquals("ISO-8859-1", self.encoder.detect_encoding(file))
        file = os.path.join(self.samples_path, "sample1-UTF-8.txt")
        self.assertEquals("UTF-8", self.encoder.detect_encoding(file))
        
    def test_convertion_from_iso_to_utf(self):
        # setup files
        iso = os.path.join(self.samples_path, "sample1-ISO-8859-1.txt")
        iso_checksum = self.__checksum(iso)
        utf = os.path.join(self.samples_path, "sample1-UTF-8.txt")
        utf_checksum = self.__checksum(utf)
        # create temp file
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        temp_checksum = self.__checksum(f.name)
        # validate before convertion
        self.assertNotEquals(iso_checksum, utf_checksum)
        self.assertNotEquals(temp_checksum, utf_checksum)
        self.assertNotEquals(iso_checksum, temp_checksum)
        # convert files
        self.encoder.convert_encoding(iso, f.name, "UTF-8")
        temp_checksum = self.__checksum(f.name)
        # validate output
        self.assertNotEquals(iso_checksum, temp_checksum)
        self.assertEquals(temp_checksum, utf_checksum)
        
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
