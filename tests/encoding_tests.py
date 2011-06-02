import unittest
import sys, os, tempfile
from md5 import md5
from pkg_resources import resource_filename

from baudot.core import FileEncoder

class EncodingTest(unittest.TestCase):

    def setUp(self):
        self.encoder = FileEncoder()
        self.samples_package = "tests.encoding_tests"

    def test_detection(self):
        file = resource_filename(self.samples_package, "samples/sample1-ISO-8859-1.txt")
        self.assertEquals("ISO-8859-1", self.encoder.detect_encoding(file))
        file = resource_filename(self.samples_package, "samples/sample1-UTF-8.txt")
        self.assertEquals("UTF-8", self.encoder.detect_encoding(file))

    def test_convertion_from_iso_to_utf(self):
        # setup files
        iso = resource_filename(self.samples_package, "samples/sample1-ISO-8859-1.txt")
        iso_checksum = self.__checksum(iso)
        utf = resource_filename(self.samples_package, "samples/sample1-UTF-8.txt")
        utf_checksum = self.__checksum(utf)
        # create temp file
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.close()
        temp_checksum = self.__checksum(temp.name)
        # validate before convertion
        self.assertNotEquals(iso_checksum, utf_checksum)
        self.assertNotEquals(temp_checksum, utf_checksum)
        self.assertNotEquals(iso_checksum, temp_checksum)
        # convert files
        self.encoder.convert_encoding(iso, temp.name, "ISO-8859-1", "UTF-8")
        temp_checksum = self.__checksum(temp.name)
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
