# Represents an SVG gradient stop or Android's GradientColorItem.
class GradientStop:
    def __init__(self, color: str, offset: str):
        self.color = color
        self.offset = offset
        self.opacity = ''

    def getColor(self) -> str:
        return self.color
    
    def getOffset(self) -> str:
        return self.offset
    
    def getOpacity(self) -> str:
        return self.opacity

    def setOpacity(self, opacity: str):
        self.opacity = opacity