from abc import *
from typing import Self

import math

class Rectangle2D(metaclass = ABCMeta):
    OUT_LEFT = 1
    OUT_TOP = 2
    OUT_RIGHT = 4
    OUT_BOTTOM = 8


class Rectangle2DF(Rectangle2D):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: float = 0.0, h: float = 0.0):
        self.setRect(x, y, w, h)

    def setRect(self, x: float, y: float, w: float, h: float):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def getX(self) -> float:
        return self.x

    def getY(self) -> float:
        return self.y

    def getWidth(self) -> float:
        return self.width

    def getHeight(self) -> float:
        return self.height