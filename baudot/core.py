from icu import CharsetDetector, CharsetMatch

class FileEncoder():
    '''
    Provides all functionality for managing character encodings
    '''
    def __init__(self):
        self.detector = CharsetDetector()

    def get_available_encodings(self):
        pass
        
    def detect_encoding(self, file):
        data = self.__getContent(file)
        return self.__detect(data)

    def convert_encoding(self, input, output, encoding):
        data = self.__getContent(input)
        detected = self.__detect(data)
        data = data.decode(detected)
        out = open(output, 'w')
        out.write(data.encode(encoding))
        out.close()

    def __detect(self, text):
        self.detector.setText(text)
        m = self.detector.detect()
        return m.getName()
        
    def __getContent(self, file):
        f = open(file, 'r')
        data = f.read()
        f.close()
        return data
