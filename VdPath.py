from VdElement import VdElement
from AffineTransform import AffineTransform
from Point2D import Point2DF

import math

# Used to represent one VectorDrawable's path element.
class VdPath(VdElement):
    PATH_ID = 'android:name'
    PATH_DESCRIPTION = 'android:pathData'
    PATH_FILL = 'android:fillColor'
    PATH_FILL_OPACITY = 'android:fillAlpha'
    PATH_FILL_TYPE = 'android:fillType'
    PATH_STROKE = 'android:strokeColor'
    PATH_STROKE_OPACITY = 'android:strokeAlpha'
    FILL_TYPE_EVEN_ODD = 'evenOdd'
    PATH_STROKE_WIDTH = 'android:strokeWidth'
    PATH_TRIM_START = 'android:trimPathStart'
    PATH_TRIM_END = 'android:trimPathEnd'
    PATH_TRIM_OFFSET = 'android:trimPathOffset'
    PATH_STROKE_LINE_CAP = 'android:strokeLineCap'
    PATH_STROKE_LINE_JOIN = 'android:strokeLineJoin'
    PATH_STROKE_MITER_LIMIT = 'android:strokeMiterLimit'
    LINE_CAP_BUTT = 'butt'
    LINE_CAP_ROUND = 'round'
    LINE_CAP_SQUARE = 'square'
    LINE_JOIN_MITER = 'miter'
    LINE_JOIN_ROUND = 'round'
    LINE_JOIN_BEVEL = 'bevel'
    EPSILON = 1e-6
    INIT_TYPE = ' '
    COMMAND_STEP_MAP = {
        'z': 2,
        'Z': 2,
        'm': 2,
        'M': 2,
        'l': 2,
        'L': 2,
        't': 2,
        'T': 2,
        'h': 1,
        'H': 1,
        'v': 1,
        'V': 1,
        'c': 6,
        'C': 6,
        's': 4,
        'S': 4,
        'q': 4,
        'Q': 4,
        'a': 7,
        'A': 7
    }

    class Node:
        def __init__(self, tp: str, params: list):
            self.mType = tp
            self.mParams = params

        def getType(self) -> str:
            return self.mType
        
        def getParams(self) -> list:
            return self.mParams
        
        @classmethod
        def hasRelMoveAfterClose(cls, nodes: list) -> bool:
            preType = ' '
            for n in nodes:
                if (preType == 'z' or preType == 'Z') and n.mType == 'm':
                    return True
                preType = n.mType
            return False

        @classmethod
        def NodeListToString(cls, nodes: list, svgTree: 'SvgTree') -> str:
            result = ''
            for node in nodes:
                result += node.mType
                ln = len(node.mParams)
                implicitLineTo = False
                lineToType = ' '
                if (node.mType == 'm' or node.mType == 'M') and 2 < ln:
                    implicitLineTo = True
                    lineToType = 'l' if node.mType == 'm' else 'L'
                for j in range(ln):
                    if 0 < j:
                        result += ',' if (j % 2) != 0 else ' '
                    if implicitLineTo and j == 2:
                        result += lineToType
                    param = node.mParams[j]
                    if not math.isfinite(param):
                        raise ValueError(f'Invalid number: {param}')
                    result += svgTree.formatCoordinate(param)
            return result

        @classmethod
        def transform(cls, totalTransform: AffineTransform, nodes: list):
            currentPoint = Point2DF()
            currentSegmentStartPoint = Point2DF()
            previousType = VdPath.INIT_TYPE
            for n in nodes:
                n.transformImpl(totalTransform, currentPoint, currentSegmentStartPoint, previousType)
                previousType = n.mType

        def transformImpl(self, totalTransform: AffineTransform, currentPoint: Point2DF, currentSegmentStartPoint: Point2DF, previousType: str):
            # For horizontal and vertical lines, we have to convert to LineTo with 2 parameters.
            # And for arcTo, we also need to isolate the parameters for transformation.
            # Therefore, looping will be necessary for such commands.
            #
            # Note that if the matrix is translation only, then we can save many computations.
            paramsLen = len(self.mParams)
            tempParams = [0.0] * paramsLen * 2
            # These have to be pre-transformed values. In other words, the same as it is
            # in the pathData.
            currentX = currentPoint.x
            currentY = currentPoint.y
            currentSegmentStartX = currentSegmentStartPoint.x
            currentSegmentStartY = currentSegmentStartPoint.y
            step = VdPath.COMMAND_STEP_MAP.get(self.mType)
            if self.mType in ['z', 'Z']:
                currnetX = currentSegmentStartX
                currentY = currentSegmentStartY
            elif self.mType == 'M':
                currentSegmentStartX = self.mParams[0]
                currentSegmentStartY = self.mParams[1]
                currentX = self.mParams[paramsLen - 2]
                currentY = self.mParams[paramsLen - 1]
                totalTransform.transform5(self.mParams, 0, self.mParams, 0, paramsLen / 2)
            elif self.mType in ['L', 'T', 'C', 'S', 'Q']:
                currentX = self.mParams[paramsLen - 2]
                currentY = self.mParams[paramsLen - 1]
                totalTransform.transform5(self.mParams, 0, self.mParams, 0, paramsLen / 2)
            elif self.mType == 'm':
                if previousType == 'z' or previousType == 'Z':
                    # Replace 'm' with 'M' to work around a bug in API 21 that is triggered
                    # when 'm' follows 'z'.
                    self.mType = 'M'
                    self.mParams[0] += currentSegmentStartX
                    self.mParams[1] += currentSegmentStartY
                    currentSegmentStartX = self.mParams[0]   # Start a new segment.
                    currentSegmentStartY = self.mParams[1]
                    for i in range(step, paramsLen, step):
                        self.mParams[i] += self.mParams[i - step]
                        self.mParams[i + 1] += self.mParams[i + 1 - step]
                    currentX = self.mParams[paramsLen - 2]
                    currentY = self.mParams[paramsLen - 1]
                    totalTransform.transform5(self.mParams, 0, self.mParams, 0, paramsLen / 2)
                else:
                    headLen = 2
                    currentX += self.mParams[0]
                    currentY += self.mParams[1]
                    currentSegmentStartX = currentX # Start a new segment.
                    currentSegmentStartY = currentY
                    if previousType == self.INIT_TYPE:
                        # 'm' at the start of a path is handled similar to 'M'.
                        # The coordinates are transformed as absolute.
                        totalTransform.transform5(self.mParams, 0, self.mParams, 0, headLen / 2)
                    elif not self.isTranslationOnly(totalTransform):
                        self.deltaTransform(totalTransform, self.mParams, 0, headLen)
                    for i in range(headLen, paramsLen, step):
                        currentX += self.mParams[i]
                        currentY += self.mParams[i + 1]
                    if not self.isTranslationOnly(totalTransform):
                        self.deltaTransform(totalTransform, self.mParams, headLen, paramsLen - headLen)
            elif self.mType in ['l', 't', 'c', 's', 'q']:
                for i in range(0, paramsLen - step + 1, step):
                    currentX += self.mParams[i + step - 2]
                    currentY += self.mParams[i + step - 1]
                if not self.isTranslationOnly(totalTransform):
                    self.deltaTransform(totalTransform, self.mParams, 0, paramsLen)
            elif self.mType == 'H':
                self.mType = 'L'
                for i in range(paramsLen):
                    tempParams[i * 2] = self.mParams[i]
                    tempParams[i * 2 + 1] = currentY
                    currentX = self.mParams[i]
                totalTransform.transform5(tempParams, 0, tempParams, 0, paramsLen)
                self.mParams = tempParams
            elif self.mType == 'V':
                self.mType = 'L'
                for i in range(paramsLen):
                    tempParams[i * 2] = currentX
                    tempParams[i * 2 + 1] = self.mParams[i]
                    currentY = self.mParams[i]
                totalTransform.transform5(tempParams, 0, tempParams, 0, paramsLen)
                self.mParams = tempParams
            elif self.mType == 'h':
                for i in range(paramsLen):
                    currentX += self.mParams[i]
                    # tempParams may not be used but is assigned here to avoid a second loop.
                    tempParams[i * 2] = self.mParams[i]
                    tempParams[i * 2 + 1] = 0
                if not self.isTranslationOnly(totalTransform):
                    mType = 'l'
                    deltaTransform(totalTransform, tempParams, 0, 2 * paramsLen)
                    self.mParams = tempParams
            elif self.mType == 'v':
                for i in range(paramsLen):
                    # tempParams may not be used but is assigned here to avoid a second loop.
                    tempParams[i * 2] = 0
                    tempParams[i * 2 + 1] = self.mParams[i]
                    currentY += self.mParams[i]
                if not self.isTranslationOnly(totalTransform):
                    mType = 'l'
                    deltaTransform(totalTransform, tempParams, 0, 2 * paramsLen)
                    self.mParams = tempParams
            elif self.mType == 'A':
                for i in range(0, paramsLen - step + 1, step):
                    # (0:rx 1:ry 2:x-axis-rotation 3:large-arc-flag 4:sweep-flag 5:x 6:y)
                    # [0, 1, 2]
                    if not self.isTranslationOnly(totalTransform):
                        ellipseSolver = EllipseSolver(totalTransform, currentX, currentY, self.mParams[i], self.mParams[i + 1], self.mParams[i + 2], self.mParams[i + 3], self.mParams[i + 4], self.mParams[i + 5], self.mParams[i + 6])
                        self.mParams[i] = ellipseSolver.getMajorAxis()
                        self.mParams[i + 1] = ellipseSolver.getMinorAxis()
                        self.mParams[i + 2] = ellipseSolver.getRotationDegree()
                        if ellipseSolver.getDirectionChanged():
                            self.mParams[i + 4] = 1 - self.mParams[i + 4]
                    # [5, 6]
                    currentX = self.mParams[i + 5]
                    currentY = self.mParams[i + 6]
                    totalTransform.transform5(self.mParams, i + 5, self.mParams, i + 5, 1)
            elif self.mType == 'a':
                for i in range(0, paramsLen - step + 1, step):
                    oldCurrentX = currentX
                    oldCurrentY = currentY
                    currentX += self.mParams[i + 5]
                    currentY += self.mParams[i + 6]
                    if not self.isTranslationOnly(totalTransform):
                        ellipseSolver = EllipseSolver(totalTransform, oldCurrentX, oldCurrentY, self.mParams[i], self.mParams[i + 1], self.mParams[i + 2], self.mParams[i + 3], self.mParams[i + 4], oldCurrentX + self.mParams[i + 5],  oldCurrentY + self.mParams[i + 6])
                        # (0:rx 1:ry 2:x-axis-rotation 3:large-arc-flag 4:sweep-flag 5:x 6:y)
                        # [5, 6]
                        self.deltaTransform(totalTransform, self.mParams, i + 5, 2)
                        # [0, 1, 2]
                        self.mParams[i] = ellipseSolver.getMajorAxis()
                        self.mParams[i + 1] = ellipseSolver.getMinorAxis()
                        self.mParams[i + 2] = ellipseSolver.getRotationDegree()
                        if ellipseSolver.getDirectionChanged():
                            self.mParams[i + 4] = 1 - self.mParams[i + 4]
            else:
                raise ValueError(f'Unexpected type {self.mType}')
            currentPoint.setLocation(currentX, currentY)
            currentSegmentStartPoint.setLocation(currentSegmentStartX, currentSegmentStartY)

        @classmethod
        def isTranslationOnly(cls, totalTransform: AffineTransform) -> bool:
            _type = totalTransform.getType()
            return _type == AffineTransform.TYPE_IDENTITY or _type == AffineTransform.TYPE_TRANSLATION

        # Applies delta transform to a set of points represented by a float array.
        #
        # @param totalTransform the transform to apply
        # @param coordinates coordinates of points to apply the transform to
        # @param offset in number of floats, not points
        # @param paramsLen in number of floats, not points
        @classmethod
        def deltaTransform(totalTransform: AffineTransform, coordinates: list, offset: int, paramsLen: int):
            doubleArray = [0.0] * paramsLen
            for i in range(paramsLen):
                doubleArray[i] = coordinates[i + offset]
            totalTransform.deltaTransform(doubleArray, 0, doubleArray, 0, paramsLen / 2)
            for i in range(paramsLen):
                coordinates[i + offset] = doubleArray[i]

    @classmethod
    def applyAlpha(cls, color: int, alpha: float) -> int:
        alphaBytes = (color >> 24) & 0xff
        color &= 0x00FFFFFF;
        color |= int(alphaBytes * alpha) << 24
        return color