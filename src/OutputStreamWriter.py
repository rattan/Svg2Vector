
# This is not original class.
# fake java OutputOutputStreamWriter for write result on original library.
class OutputStreamWriter:
    def __init__(self):
        self.buffer = ''

    def write(self, out):
        self.buffer += out
    
    def toString(self):
        return self.buffer