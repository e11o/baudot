from icu import CharsetDetector, CharsetMatch

class Encoding():
    '''
    Provides all functionality for managing character encodings
    '''
    def __init__(self):
        self.detector = CharsetDetector()

    def getAvailableEncodings(self):
        pass
        
    def detectEncoding(self, file):
        data = self.__getContent(file)
        return self.__detect(data)

    def convertEncoding(self, input, output, encoding):
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
