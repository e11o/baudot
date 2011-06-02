from icu import CharsetDetector, CharsetMatch, UnicodeString

class FileEncoder():
    '''
    Provides all functionality for managing character encodings
    '''
    def __init__(self):
        self.detector = CharsetDetector()

    def get_available_encodings(self):
        # remove duplicated charsets
        seen = set()
        seen_add = seen.add
        return [ x for x in self.detector.getAllDetectableCharsets()
                if x not in seen and not seen_add(x)]

    def detect_encoding(self, src_file):
        data = self.__get_content(src_file)
        return self.detect(data)

    def convert_encoding(self, src_file, dst_file, src_charset, dst_charset):
        data = self.__get_content(src_file)
        if data:
            encoded = UnicodeString(data, src_charset).encode(dst_charset)
            out = open(dst_file, 'w')
            out.write(encoded)
            out.close()

    def detect(self, text):
        self.detector.setText(text)
        m = self.detector.detect()
        return m.getName()

    def __get_content(self, file):
        f = open(file, 'r')
        data = f.read()
        f.close()
        return data
