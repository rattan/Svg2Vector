from Point2D import Point2DF, Point2D
from AffineTransform import AffineTransform
import math

class EllipseSolver:
    # Constructs the solver with all necessary parameters, and all the output values will
    # be ready after this constructor is called.
    # <p>
    # Note that all the x y values are in absolute coordinates, such that we can apply
    # the transform directly.
    def __init__(self, totalTransform: AffineTransform, currentX: float, currentY: float, rx: float, ry: float, xAxisRotation: float, largeArcFlag: float, sweepFlag: float, destX: float, destY: float):
        self.mMajorAxis = 0.0
        self.mMinorAxis = 0.0
        self.mRotationDegree = 0.0
        self.mDirectionChanged = False

        if rx == 0 or ry == 0:
            # From https://www.w3.org/TR/SVG11/implnote.html#ArcOutOfRangeParameters:
            # "If rx = 0 or ry = 0 then this arc is treated as a straight line segment
            # (a "lineto") joining the endpoints."
            return
        
        largeArc = largeArcFlag != 0
        sweep = sweepFlag != 0
        # Compute the cx and cy first.
        originalCenter = self.computeOriginalCenter(currentX, currentY, rx, ry, xAxisRotation, largeArc, sweep, destX, destY)
        # Compute 3 points from original ellipse.
        majorAxisPoint = Point2DF(rx, 0)
        minorAxisPoint = Point2DF(0, ry)
        majorAxisPoint = self.rotatePoint2D(majorAxisPoint, xAxisRotation)
        minorAxisPoint = self.rotatePoint2D(minorAxisPoint, xAxisRotation)
        majorAxisPoint.x += originalCenter.x
        majorAxisPoint.y += originalCenter.y
        minorAxisPoint.x += originalCenter.x
        minorAxisPoint.y += originalCenter.y
        middleRadians = math.pi / 4 # This number can be anything between 0 and PI/2.
        middleR = rx * ry / math.hypot(ry * math.cos(middleRadians), rx * math.sin(middleRadians))
        middlePoint = Point2DF(middleR * math.cos(middleRadians),middleR * math.sin(middleRadians))
        middlePoint = self.rotatePoint2D(middlePoint, xAxisRotation)
        middlePoint.x += originalCenter.x
        middlePoint.y += originalCenter.y
        # Transform 3 points and center point into destination.
        mDstMiddlePoint = totalTransform.transform2(middlePoint, None)
        mDstMajorAxisPoint = totalTransform.transform2(majorAxisPoint, None)
        mDstMinorAxisPoint = totalTransform.transform2(minorAxisPoint, None)
        dstCenter = totalTransform.transform2(originalCenter, None)
        dstCenterX = dstCenter.getX()
        dstCenterY = dstCenter.getY()
        # Compute the relative 3 points:
        relativeDstMiddleX = mDstMiddlePoint.x - dstCenterX
        relativeDstMiddleY = mDstMiddlePoint.y - dstCenterY
        relativeDstMajorAxisPointX = mDstMajorAxisPoint.x - dstCenterX
        relativeDstMajorAxisPointY = mDstMajorAxisPoint.y - dstCenterY
        relativeDstMinorAxisPointX = mDstMinorAxisPoint.x - dstCenterX
        relativeDstMinorAxisPointY = mDstMinorAxisPoint.y - dstCenterY
        # Check if the direction has changed.
        self.mDirectionChanged = self.computeDirectionChange(middlePoint, majorAxisPoint, minorAxisPoint, mDstMiddlePoint, mDstMajorAxisPoint, mDstMinorAxisPoint)
        # From 3 dest points, recompute the a, b and theta.
        if self.computeABThetaFromControlPoints(relativeDstMiddleX, relativeDstMiddleY, relativeDstMajorAxisPointX, relativeDstMajorAxisPointY, relativeDstMinorAxisPointX, relativeDstMinorAxisPointY):
            # print('Early return in the ellipse transformation computation!')
            pass

    # After a random transformation, the controls points may change its direction, left handed <->
    # right handed. In this case, we better flip the flag for the ArcTo command.
    # Here, we use the cross product to figure out the direction of the 3 control points for the
    # src and dst ellipse.
    @classmethod
    def computeDirectionChange(cls, middlePoint: Point2DF, majorAxisPoint: Point2DF, minorAxisPoint: Point2DF, dstMiddlePoint: Point2DF, dstMajorAxisPoint: Point2DF, dstMinorAxisPoint: Point2DF) -> float:
        # Compute both cross product, then compare the sign.
        srcCrossProduct = cls.getCrossProduct(middlePoint, majorAxisPoint, minorAxisPoint)
        dstCrossProduct = cls.getCrossProduct(dstMiddlePoint, dstMajorAxisPoint, dstMinorAxisPoint)
        return srcCrossProduct * dstCrossProduct < 0

    @classmethod
    def getCrossProduct(cls, middlePoint: Point2DF, majorAxisPoint: Point2DF, minorAxisPoint: Point2DF):
        majorMinusMiddleX = majorAxisPoint.x - middlePoint.x
        majorMinusMiddleY = majorAxisPoint.y - middlePoint.y
        minorMinusMiddleX = minorAxisPoint.x - middlePoint.x
        minorMinusMiddleY = minorAxisPoint.y - middlePoint.y
        return majorMinusMiddleX * minorMinusMiddleY - majorMinusMiddleY * minorMinusMiddleX

    # Returns true if there is an error, either due to the ellipse not being specified
    # correctly or some computation error. This error is ignorable, but the output ellipse
    # will not be correct.
    def computeABThetaFromControlPoints(self, relMiddleX: float, relMiddleY: float, relativeMajorAxisPointX: float, relativeMajorAxisPointY: float, relativeMinorAxisPointX: float, relativeMinorAxisPointY: float) -> bool:
        m11 = relMiddleX * relMiddleX
        m12 = relMiddleX * relMiddleY
        m13 = relMiddleY * relMiddleY
        m21 = relativeMajorAxisPointX * relativeMajorAxisPointX
        m22 = relativeMajorAxisPointX * relativeMajorAxisPointY
        m23 = relativeMajorAxisPointY * relativeMajorAxisPointY
        m31 = relativeMinorAxisPointX * relativeMinorAxisPointX
        m32 = relativeMinorAxisPointX * relativeMinorAxisPointY
        m33 = relativeMinorAxisPointY * relativeMinorAxisPointY
        det = -(m13 * m22 * m31 - m12 * m23 * m31 - m13 * m21 * m32 + m11 * m23 * m32 + m12 * m21 * m33 - m11 * m22 * m33)
        if det == 0:
            return True
        A = (-m13 * m22 + m12 * m23 + m13 * m32 - m23 * m32 - m12 * m33 + m22 * m33) / det
        B = (m13 * m21 - m11 * m23 - m13 * m31 + m23 * m31 + m11 * m33 - m21 * m33) / det
        C = (m12 * m21 - m11 * m22 - m12 * m31 + m22 * m31 + m11 * m32 - m21 * m32) / (-det)
        # Now we know A = cos(t)^2 / a^2 + sin(t)^2 / b^2
        # B = -2 cos(t) sin(t) (1/a^2 - 1/b^2)
        # C = sin(t)^2 / a^2 + cos(t)^2 / b^2
        # Solve it, we got
        # 2*t = arctan ( B / (A - C));
        if A - C == 0:
            # We know that a == b now.
            self.mMinorAxis = float(math.hypot(relativeMajorAxisPointX, relativeMajorAxisPointY))
            self.mMajorAxis = self.mMinorAxis
            self.mRotationDegree = 0
            return False
        doubleThetaInRadians = math.atan(B / (A - C))
        thetaInRadians = doubleThetaInRadians / 2
        if math.sin(doubleThetaInRadians) == 0:
            self.mMinorAxis = float(math.sqrt(1 / C))
            self.mMajorAxis = float(math.sqrt(1 / A))
            self.mRotationDegree = 0
            # This is a valid answer, so return false.
            return False
        bSqInv = (A + C + B / math.sin(doubleThetaInRadians)) / 2
        aSqInv = A + C - bSqInv
        if bSqInv == 0 or aSqInv == 0:
            return True
        self.mMinorAxis = float(math.sqrt(1 / bSqInv))
        self.mMajorAxis = float(math.sqrt(1 / aSqInv))
        self.mRotationDegree = float(math.degrees(math.pi / 2 + thetaInRadians))
        return False

    @classmethod
    def computeOriginalCenter(cls, x1: float, y1: float, rx: float, ry: float, phi: float, largeArc :bool, sweep: bool, x2: float, y2: float) -> Point2DF:
        cosPhi = math.cos(phi)
        sinPhi = math.sin(phi)
        xDelta = (x1 - x2) / 2
        yDelta = (y1 - y2) / 2
        tempX1 = cosPhi * xDelta + sinPhi * yDelta
        tempY1 = -sinPhi * xDelta + cosPhi * yDelta
        rxSq = rx * rx
        rySq = ry * ry
        tempX1Sq = tempX1 * tempX1
        tempY1Sq = tempY1 * tempY1
        tempCenterFactor = rxSq * rySq - rxSq * tempY1Sq - rySq * tempX1Sq
        tempCenterFactor /= rxSq * tempY1Sq + rySq * tempX1Sq
        if tempCenterFactor < 0:
            tempCenterFactor = 0
        tempCenterFactor = math.sqrt(tempCenterFactor)
        if largeArc == sweep:
            tempCenterFactor = -tempCenterFactor
        tempCx = tempCenterFactor * rx * tempY1 / ry
        tempCy = -tempCenterFactor * ry * tempX1 / rx
        xCenter = (x1 + x2) / 2
        yCenter = (y1 + y2) / 2
        return Point2DF(cosPhi * tempCx - sinPhi * tempCy + xCenter, sinPhi * tempCx + cosPhi * tempCy + yCenter)

    def getMajorAxis(self) -> float:
        return self.mMajorAxis

    def getMinorAxis(self) -> float:
        return self.mMinorAxis

    def getRotationDegree(self) -> float:
        return self.mRotationDegree

    def getDirectionChanged(self) -> bool:
        return self.mDirectionChanged

    # Rotates a point by the given angle.
    # @param inPoint the point to rotate
    # @param radians the rotation angle in radians
    # @return the rotated point
    @classmethod
    def rotatePoint2D(cls, inPoint: Point2D, radians: float) -> Point2D:
        cos = math.cos(radians)
        sin = math.sin(radians)
        return Point2DF(inPoint.x * cos - inPoint.y * sin, inPoint.x * sin + inPoint.y * cos)