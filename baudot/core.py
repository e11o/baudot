from icu import CharsetDetector, CharsetMatch, UnicodeString
from path import path

class CharsetConverter():
    '''
    Wrapper for charset handling library
    '''
    def __init__(self):
        self.detector = CharsetDetector()

    def get_encodings(self):
        # remove duplicated charsets
        seen = set()
        seen_add = seen.add
        return [ x for x in self.detector.getAllDetectableCharsets()
                if x not in seen and not seen_add(x)]

    def detect_encoding(self, src_file):
        src_file = path(src_file)
        data = src_file.bytes()
        return self.detect(data)

    def convert_encoding(self, src_file, dst_file, src_charset, dst_charset):
        src_file = path(src_file)
        dst_file = path(dst_file)
        data = src_file.bytes()
        if data:
            encoded = UnicodeString(data, src_charset).encode(dst_charset)
            dst_file.write_bytes(encoded)

    def detect(self, text):
        self.detector.setText(text)
        m = self.detector.detect()
        return Match.fromICU(m)

class Match(object):
    def __init__(self, charset, confidence):
        self.charset = charset
        self.confidence = confidence

    @staticmethod
    def fromICU(m):
        return Match(m.getName(), m.getConfidence()) if m else None
                     