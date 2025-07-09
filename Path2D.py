from Curve import Curve
from Rectangle2D import Rectangle2DF

from abc import *
from typing import Self

import math
import sys

class Path2D(metaclass = ABCMeta):
    WIND_EVEN_ODD = 0
    WIND_NON_ZERO = 1

    SEG_MOVETO = 0
    SEG_LINETO = 1
    SEG_QUADTO = 2
    SEG_CUBICTO = 3
    SEG_CLOSE = 4

    INIT_SIZE = 20
    EXPAND_MAX = 500
    EXPAND_MAX_COORDS = EXPAND_MAX * 2
    EXPAND_MIN = 10 # ensure > 6 (cubics)

    def __init__(self, rule: int, initialTypes: int):
        self.setWindingRule(rule)
        self.pointTypes = [''] * initialTypes
        self.pointTypes = []
        self.numTypes = 0
        self.numCoords = 0
    
    def setWindingRule(self, rule: int):
        if rule != self.WIND_EVEN_ODD and rule != self.WIND_NON_ZERO:
            raise ValueError('winding rule must be WIND_EVEN_ODD or WIND_NON_ZERO')
        self.windingRule = rule

    @classmethod
    def expandPointTypes(cls, oldPointTypes: list[float], needed: int) -> list[str]:
        oldSize = len(oldPointTypes)
        newSizeMin = oldSize + needed
        if newSizeMin < oldSize:
            raise IndexError('pointTypes exceeds maximum capacity !')
        
        grow = oldSize
        if cls.EXPAND_MAX < grow:
            grow = max(cls.EXPAND_MAX_COORDS, oldSize >> 3)
        elif grow < cls.EXPAND_MIN:
            grow = cls.EXPAND_MIN
        assert 0 < grow

        newSize = oldSize + grow
        if newSize < newSizeMin:
            newSize = sys.maxint
        
        while True:
            try:
                newList = list(oldPointTypes)
                newList.extend([0.0] * (newSize - oldSize))
                return newList
            except MemoryError as e:
                if newSize == newSizeMin:
                    raise MemoryError(e)
            newSize = newSizeMin + (newSize - newSizeMin) / 2

    @abstractmethod
    def needRoom(self, needMove: bool, newCoords: int):
        pass

    @abstractmethod
    def moveTo(self, x: float, y: float):
        pass

    @abstractmethod
    def lineTo(self, x: float, y: float):
        pass

    @abstractmethod
    def quadTo(self, x1: float, y1: float, x2: float, y2: float):
        pass

    @abstractmethod
    def curveTo(self, x1: float,y1: float,x2: float,y2: float,x3: float,y3: float):
        pass
        
    @abstractmethod
    def clostPath(self):
        pass

class Path2DIt:
    curvecoords = [2, 2, 4, 6, 0]
    def __init__(self, path: Path2D):
        self.typeIdx = 0
        self.pointIdx = 0
        self.path = path
        self.floatCoords = path.floatCoords

    def getWindingRule(self) -> int:
        self.path.getWindingRule()

    def isDone(self) -> bool:
        return self.path.numTypes <= self.typeIdx
    
    def next(self):
        _type = self.path.pointTypes[self.typeIdx]
        self.typeIdx += 1
        self.pointIdx += self.curvecoords[_type]

    def currentSegment(self, coords: list[float]) -> int:
        _type = self.path.pointTypes[self.typeIdx]
        numCoords = self.curvecoords[_type]
        if 0 < numCoords:
            coords[: numCoords] = self.floatCoords[self.pointIdx: self.pointIdx + numCoords]
        return _type

    
class Path2DF(Path2D):
    def __init__(self):
        super().__init__(Path2D.WIND_NON_ZERO, Path2D.INIT_SIZE)
        self.floatCoords = []
    
    def reset(self):
        self.numTypes = 0
        self.numCoords = 0

    def needRoom(self, needMove: bool, newCoords: int):
        if self.numTypes == 0 and needMove:
            raise ValueError('missing inital moveto in path definition')
        if len(self.pointTypes) <= self.numTypes:
            self.pointTypes = self.expandPointTypes(self.pointTypes, 1)
        if (len(self.floatCoords) - newCoords) < self.numCoords:
            self.floatCoords = self.expandCoords(self.floatCoords, newCoords)

    @classmethod
    def expandCoords(cls, oldCoords: list[float], needed: int) -> list[float]:
        oldSize = len(oldCoords)
        newSizeMin = oldSize + needed
        if newSizeMin < oldSize:
            raise IndexError('coords exceeds maximum capacity !')
        
        grow = oldSize
        if cls.EXPAND_MAX_COORDS < grow:
            grow = max(cls.EXPAND_MAX_COORDS, oldSize >> 3)
        elif grow < cls.EXPAND_MIN:
            grow = cls.EXPAND_MIN
        assert needed < grow

        newSize = oldSize + grow
        if newSize < newSizeMin:
            newSize = sys.maxint
        
        while True:
            try:
                newList = list(oldCoords)
                newList.extend([0.0] * (newSize - oldSize))
                return newList
            except MemoryError as e:
                if newSize == newSizeMin:
                    raise MemoryError(e)
            newSize = newSizeMin + (newSize - newSizeMin) / 2

    def moveTo(self, x: float, y: float):
        if 0 < self.numTypes and self.pointTypes[self.numTypes - 1] == self.SEG_MOVETO:
            self.floatCoords[self.numCoords - 2] =  x
            self.floatCoords[self.numCoords - 1] =  y
        else:
            self.needRoom(False, 2)
            self.pointTypes[self.numTypes] = self.SEG_MOVETO
            self.numTypes += 1
            self.floatCoords[self.numCoords] =  x
            self.numCoords += 1
            self.floatCoords[self.numCoords] =  y
            self.numCoords += 1

    def lineTo(self, x: float, y: float):
            self.needRoom(True, 2)
            self.pointTypes[self.numTypes] = self.SEG_LINETO
            self.numTypes += 1
            self.floatCoords[self.numCoords] = x
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y
            self.numCoords += 1


    def quadTo(self, x1: float, y1: float, x2: float, y2: float):
            self.needRoom(True, 4)
            self.pointTypes[self.numTypes] = SEG_QUADTO
            self.numTypes += 1
            self.floatCoords[self.numCoords] = x1
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y1
            self.numCoords += 1
            self.floatCoords[self.numCoords] = x2
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y2
            self.numCoords += 1

    def curveTo(self, x1: float,y1: float,x2: float,y2: float,x3: float,y3: float):
            self.needRoom(True, 6)
            self.pointTypes[self.numTypes] = SEG_CUBICTO
            self.numTypes += 1
            self.floatCoords[self.numCoords] = x1
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y1
            self.numCoords += 1
            self.floatCoords[self.numCoords] = x2
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y2
            self.numCoords += 1
            self.floatCoords[self.numCoords] = x3
            self.numCoords += 1
            self.floatCoords[self.numCoords] = y3
            self.numCoords += 1

    def clostPath(self):
        if self.numTypes == 0 or self.pointTypes[self.numTypes - 1] != self.SEG_CLOSE:
            self.needRoom(True, 0)
            self.pointTypes[self.numTypes] = self.SEG_CLOSE
            self.numTypes += 1

    def getBounds2D(self):
        pi = Path2DIt(self)
        coeff = [0.0] * 4
        deriv_coeff = [0.0] * 3

        coords = [0.0] * 6

        bounds = None
        lastX = 0.0
        lastY = 0.0
        endX = 0.0
        endY = 0.0
        startX = 0.0
        startY = 0.0

        while not pi.isDone():
            _type = pi.currentSegment(coords)
            if _type == self.SEG_MOVETO:
                if not bounds:
                    bounds = [coords[0], coords[0], coords[1], coords[1]]
                startX = endX = coords[0]
                startY = endY = coords[1]
            elif _type == self.SEG_LINETO:
                endX = coords[0]
                endY = coords[1]
            elif _type == self.SEG_QUADTO:
                endX = coords[2]
                endY = coords[3]
            elif _type == self.SEG_CUBICTO:
                endX = coords[4]
                endY = coords[5]
            elif _type == self.SEG_CLOSE:
                endX = startX
                endY = startY
            else:
                pi.next()
                continue

            if endX < bounds[0]:
                bounds[0] = endX
            if endX > bounds[1]:
                bounds[1] = endX
            if endY < bounds[2]:
                bounds[2] = endY
            if endY > bounds[3]:
                bounds[3] = endY

            if _type == self.SEG_QUADTO:
                Curve.accumulateExtremaBoundsForQuad(bounds, 0, lastX, coords[0], coords[2], coeff, deriv_coeff)
                Curve.accumulateExtremaBoundsForQuad(bounds, 2, lastY, coords[1], coords[3], coeff, deriv_coeff)
            elif _type == self.SEG_CUBICTO:
                Curve.accumulateExtremaBoundsForCubic(bounds, 0, lastX, coords[0], coords[2], coords[4], coeff, deriv_coeff)
                Curve.accumulateExtremaBoundsForCubic(bounds, 2, lastY, coords[1], coords[3], coords[5], coeff, deriv_coeff)
            
            lastX = endX
            lastY = endY
            
            pi.next()

        if bounds:
            return Rectangle2DF(bounds[0], bounds[2], bounds[1] - bounds[0], bounds[3] - bounds[2])

        return Rectangle2DF()