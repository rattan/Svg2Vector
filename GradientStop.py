# Represents an SVG gradient stop or Android's GradientColorItem.
class GradientStop:
    def __init__(self, color, offset):
        self.color = color
        self.offset = offset
        self.opacity = ''

    def getColor(self):
        return self.color
    
    def getOffset(self):
        return self.offset
    
    def getOpacity(self):
        return self.opacity

    def setOpacity(opacity: str):
        self.opacity = opacity