import abc

# Used to represent one VectorDrawable's element, can be a group or path
class VdElement(metaclass=abc.ABCMeta):
    def __init__(self):
        self.mName = ''
        self.isClipPath = False

    def getName(self) -> str:
        return self.nName

    def setClipPath(self, isClip: bool):
        self.isClipPath = isClip