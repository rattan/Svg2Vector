
# This is not original class.
# fake java OutputStreamWriter for write result on original library.
class StreamWriter:
    def __init__(self):
        self.buffer = ''

    def write(self, out):
        self.buffer += out
    
    def toString(self):
        return self.buffer