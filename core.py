from icu import CharsetDetector, CharsetMatch

class FileEncoder():
    '''
    Provides all functionality for managing character encodings
    '''
    def __init__(self):
        self.detector = CharsetDetector()

    def get_available_encodings(self):
        return self.detector.getAllDetectableCharsets()

    def detect_encoding(self, file):
        data = self.__get_content(file)
        return self.__detect(data)

    def convert_encoding(self, input, output, charset):
        data = self.__get_content(input)
        if not data is None:
            detected = self.__detect(data)
            data = data.decode(detected).encode(charset)
            out = open(output, 'w')
            out.write(data)
            out.close()

    def __detect(self, text):
        self.detector.setText(text)
        m = self.detector.detect()
        return m.getName()

    def __get_content(self, file):
        f = open(file, 'r')
        data = f.read()
        f.close()
        return data
