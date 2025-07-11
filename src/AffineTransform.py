import math
from typing import Self
import sys

from Point2D import Point2DF, Point2D

class AffineTransform:
    TYPE_UNKNOWN = -1
    TYPE_IDENTITY = 0
    TYPE_TRANSLATION = 1
    TYPE_UNIFORM_SCALE = 2
    TYPE_GENERAL_SCALE = 4
    TYPE_MASK_SCALE = TYPE_UNIFORM_SCALE | TYPE_GENERAL_SCALE
    TYPE_FLIP = 64
    TYPE_QUADRANT_ROTATION = 8
    TYPE_GENERAL_ROTATION = 16
    TYPE_MASK_ROTATION = TYPE_QUADRANT_ROTATION | TYPE_GENERAL_ROTATION
    TYPE_GENERAL_TRANSFORM = 32
    APPLY_IDENTITY = 0
    APPLY_TRANSLATE = 1
    APPLY_SCALE = 2
    APPLY_SHEAR = 4
    HI_SHIFT = 3
    HI_IDENTITY = APPLY_IDENTITY << HI_SHIFT
    HI_TRANSLATE = APPLY_TRANSLATE << HI_SHIFT
    HI_SCALE = APPLY_SCALE << HI_SHIFT
    HI_SHEAR = APPLY_SHEAR << HI_SHIFT

    def __init__(self, m00: float = 1.0, m10: float = 0.0, m01: float = 0.0, m11: float = 1.0, m02: float = 0.0, m12: float = 0.0):
        self.m00 = m00
        self.m10 = m10
        self.m01 = m01
        self.m11 = m11
        self.m02 = m02
        self.m12 = m12

        self.state = self.APPLY_IDENTITY
        self.type = self.TYPE_UNKNOWN
        self.updateState()

    def updateState(self):
        if self.m01 == 0.0 and self.m10 == 0.0:
            if self.m00 == 1.0 and self.m11 == 1.0:
                if self.m02 == 0.0 and self.m12 == 0.0:
                    self.state = self.APPLY_IDENTITY
                    self.type = self.TYPE_IDENTITY
                else:
                    self.state = self.APPLY_TRANSLATE
                    self.type = self.TYPE_TRANSLATION
            else:
                if self.m02 == 0.0 and self.m12 == 0.0:
                    self.state = self.APPLY_SCALE
                    self.type = self.TYPE_UNKNOWN
                else:
                    self.state = self.APPLY_SCALE | self.APPLY_TRANSLATE
                    self.type = self.TYPE_UNKNOWN
        else:
            if self.m00 == 0.0 and self.m11 == 0.0:
                if self.m02 == 0.0 and self.m12 == 0.0:
                    self.state = self.APPLY_SHEAR
                    self.type = self.TYPE_UNKNOWN
                else:
                    self.state = self.APPLY_SHEAR | self.APPLY_TRANSLATE
                    self.type = self.TYPE_UNKNOWN
            else:
                if self.m02 == 0.0 and self.m12 == 0.0:
                    self.state = self.APPLY_SHEAR | self.APPLY_SCALE
                    self.type = self.TYPE_UNKNOWN
                else:
                    self.state = self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE
                    self.type = self.TYPE_UNKNOWN

    def arg_type_matcher(self, args: list, types: list):
        assert len(args) == len(types)
        for i in range(len(args)):
            if not isinstance(args[i], types[i]):
                return False
        return True

    def setTransform(self, *args):
        if len(args) == 1 and self.arg_type_matcher(args, [object]):
            self.setTransform_A(args[0])
        elif len(args) == 6 and self.arg_type_matcher(args, [float] * 6):
            self.setTransform_ffffff(args[0], args[1], args[2], args[3], args[4], args[5])
        else:
            raise ValueError(f'setTransform args wrong {args}')

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L2193
    def setTransform_A(self, Tx: Self):
        self.m00 = Tx.m00
        self.m10 = Tx.m10
        self.m01 = Tx.m01
        self.m11 = Tx.m11
        self.m02 = Tx.m02
        self.m12 = Tx.m12
        self.state = Tx.state
        self.type = Tx.type

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L2216
    def setTransform_ffffff(self, m00: float, m10: float, m01: float, m11: float, m02: float, m12: float):
        self.m00 = m00
        self.m10 = m10
        self.m01 = m01
        self.m11 = m11
        self.m02 = m02
        self.m12 = m12

    def getType(self):
        if self.type == self.TYPE_UNKNOWN:
            self.calculateType()
        return self.type

    # This is the utility function to calculate the flag bits when
    # they hava not been cached.
    # see #getType
    def calculateType(self):
        ret = self.TYPE_IDENTITY
        sgn0 = False
        sgn1 = False
        M0 = 0.0
        M1 = 0.0
        M2 = 0.0
        M3 = 0.0
        self.updateState()
        if self.state == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
            M0 = self.m00
            M2 = self.m01
            M3 = self.m10
            M1 = self.m11
            if M0 * M2 + M3 * M1 != 0:
                self.type = self.TYPE_GENERAL_TRANSFORM
                return
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 == sgn1:
                # sgn(M0) == sgn(M1) therefore sgn(M2) == -sgn(M3)
                # This is the "unflipped" (right-handed) state
                if M0 != M1 or M2 != -M3:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_GENERAL_SCALE
                elif M0 * M1 - M2 * M3 != 1.0:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_GENERAL_ROTATION
            else:
                # sgn(M0) == -sgn(M1) therefore sgn(M2) == sgn(M3)
                # This is the "flipped" (left-handed) state
                if M0 != -M1 or M2 != M3:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
                elif M0 * M1 - M2 * M3 != 1.0:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP
        elif self.state == self.APPLY_SHEAR | self.APPLY_SCALE:
            M0 = self.m00
            M2 = self.m01
            M3 = self.m10
            M1 = self.m11
            if M0 * M2 + M3 * M1 != 0:
                self.type = self.TYPE_GENERAL_TRANSFORM
                return
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 == sgn1:
                # sgn(M0) == sgn(M1) therefore sgn(M2) == -sgn(M3)
                # This is the "unflipped" (right-handed) state
                if M0 != M1 or M2 != -M3:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_GENERAL_SCALE
                elif M0 * M1 - M2 * M3 != 1.0:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_GENERAL_ROTATION
            else:
                # sgn(M0) == -sgn(M1) therefore sgn(M2) == sgn(M3)
                # This is the "flipped" (left-handed) state
                if M0 != -M1 or M2 != M3:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
                elif M0 * M1 - M2 * M3 != 1.0:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_GENERAL_ROTATION | self.TYPE_FLIP
        elif self.state == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
            M0 = self.m01
            M1 = self.m10
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 != sgn1:
                # Different signs - simple 90 degree rotation
                if M0 != -M1:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_GENERAL_SCALE
                elif M0 != 1.0 and M0 != -1.0:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_QUADRANT_ROTATION
            else:
                # Same signs - 90 degree rotation plus an axis flip too
                if M0 == M1:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
        elif self.state == self.APPLY_SHEAR:
            M0 = self.m01
            M1 = self.m10
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 != sgn1:
                # Different signs - simple 90 degree rotation
                if M0 != -M1:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_GENERAL_SCALE
                elif M0 != 1.0 and M0 != -1.0:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_QUADRANT_ROTATION
            else:
                # Same signs - 90 degree rotation plus an axis flip too
                if M0 == M1:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
        elif self.state == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
            M0 = self.m00
            M1 = self.m11
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 == sgn1:
                if sgn0:
                    # Both scaling factors non-negative - simple scale
                    # Note: APPLY_SCALE implies M0, M1 are not both 1
                    if M0 == M1:
                        ret |= self.TYPE_UNIFORM_SCALE
                    else:
                        ret |= self.TYPE_GENERAL_SCALE
                else:
                    # Both scaling factors negative - 180 degree rotation
                    if M0 != M1:
                        ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_GENERAL_SCALE
                    elif M0 != -1.0:
                        ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_UNIFORM_SCALE
                    else:
                        ret |= self.TYPE_QUADRANT_ROTATION
            else:
                # Scaling factor signs different - flip about some axis
                if M0 == -M1:
                    if M0 == 1.0 or M0 == -1.0:
                        ret |= self.TYPE_FLIP
                    else:
                        ret |= self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
        elif self.state == self.APPLY_SCALE:
            M0 = self.m00
            M1 = self.m11
            sgn0 = 0.0 <= M0
            sgn1 = 0.0 <= M1
            if sgn0 == sgn1:
                if sgn0:
                    # Both scaling factors non-negative - simple scale
                    # Note: APPLY_SCALE implies M0, M1 are not both 1
                    if M0 == M1:
                        ret |= self.TYPE_UNIFORM_SCALE
                    else:
                        ret |= self.TYPE_GENERAL_SCALE
                else:
                    # Both scaling factors negative - 180 degree rotation
                    if M0 != M1:
                        ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_GENERAL_SCALE
                    elif M0 != -1.0:
                        ret |= self.TYPE_QUADRANT_ROTATION | self.TYPE_UNIFORM_SCALE
                    else:
                        ret |= self.TYPE_QUADRANT_ROTATION
            else:
                # Scaling factor signs different - flip about some axis
                if M0 == -M1:
                    if M0 == 1.0 or M0 == -1.0:
                        ret |= self.TYPE_FLIP
                    else:
                        ret |= self.TYPE_FLIP | self.TYPE_UNIFORM_SCALE
                else:
                    ret |= self.TYPE_FLIP | self.TYPE_GENERAL_SCALE
        elif self.state == self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
        elif self.state == self.APPLY_IDENTITY:
            pass
        else:
            self.stateError()
        self.type = ret

    def getDeterminant(self) -> float:
        if self.state in {
            self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            return self.m00 * self.m11 - self.m01 * self.m10
        elif self.state in {
            self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR,
        }:
            return -self.m01 * self.m10
        elif self.state in {
            self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SCALE
        }:
            return self.m00 * self.m11
        elif self.state in {
            self.APPLY_TRANSLATE,
            self.APPLY_IDENTITY
        }:
            return 1.0
        else:
            self.stateError()


    def transform(self, *args):
        if len(args) == 2 and self.arg_type_matcher(args, [Point2D, object]):
            return self.transform_PP(args[0], args[1])
        elif len(args) == 5 and self.arg_type_matcher(args, [list, int, list, int, int]):
            self.transform_lilii(args[0], args[1], args[2], args[3], args[4])
        else:
            raise ValueError(f'transform args wrong {args}')

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L2899
    def transform_PP(self, ptSrc: Point2D, ptDst: Point2D) -> Point2D:
        if ptDst is None:
            ptDst = Point2DF()
        
        # Copy soruce coords into local variables in case src == dst
        x = ptSrc.getX()
        y = ptSrc.getY()
        if self.state == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ptDst.setLocation(x * self.m00 + y * self.m01 + self.m02, x * self.m10 + y * self.m11 + self.m12)
        elif self.state  == self.APPLY_SHEAR | self.APPLY_SCALE:
            ptDst.setLocation(x * self.m00 + y * self.m01, x * self.m10 + y * self.m11)
        elif self.state == self.APPLY_SHEAR:
            ptDst.setLocation(y * self.m01, x * self.m10)
        elif self.state == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ptDst.setLocation(x * self.m00 + self.m02, y * self.m11 + self.m12)
        elif self.state == self.APPLY_SCALE:
            ptDst.setLocation(x * self.m00, y * self.m11)
        elif self.state == self.APPLY_TRANSLATE:
            ptDst.setLocation(x + self.m02, y + self.m12)
        elif self.state == self.APPLY_IDENTITY:
            ptDst.setLocation(x, y)
        else:
            self.stateError()
            return None
        return ptDst

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L3051
    def transform_lilii(self, srcPts: list[float], srcOff: int, dstPts: list[float], dstOff: int, numPts: int):
        M00 = 0.0
        M01 = 0.0
        M02 = 0.0
        M10 = 0.0
        M11 = 0.0
        M12 = 0.0
        if dstPts == srcPts and srcOff < dstOff and desOff < srcOff + numPts * 2:
            dstPts[dstOff:dstOff + numPts * 2] = srcPts[srcOff:srcOff + numPts * 2]
            srcOff = dstOff
        if self.state == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M00 = self.m00
            M01 = self.m01
            M02 = self.m02
            M10 = self.m10
            M11 = self.m11
            M12 = self.m12
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                y = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = float(M00 * x + M01 * y + M02)
                dstOff += 1
                dstPts[dstOff] = float(M10 * x + M11 * y + M12)
                dstOff += 1
            return
        elif self.state == self.APPLY_SHEAR | self.APPLY_SCALE:
            M00 = self.m00
            M01 = self.m01
            M10 = self.m10
            M11 = self.m11
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                y = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = float(M00 * x + M01 * y)
                dstOff += 1
                dstPts[dstOff] = float(M10 * x + M11 * y)
                dstOff += 1
            return
        elif self.state == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            M01 = self.m01
            M02 = self.m02
            M10 = self.m10
            M12 = self.m12
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = float(M01 * srcPts[srcOff] + M02)
                srcOff += 1
                dstOff += 1
                dstPts[dstOff] = float(M10 * x + M12)
                dstOff += 1
            return
        elif self.state == self.APPLY_SHEAR:
            M01 = self.m01
            M10 = self.m10
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = float(M01 * srcPts[srcOff])
                srcOff += 1
                dstOff += 1
                dstPts[dstOff] = float(M10 * x)
                dstOff += 1
            return
        elif self.state == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M00 = self.m00
            M02 = self.m02
            M11 = self.m11
            M12 = self.m12
            for _ in range(numPts):
                dstPts[dstOff] = float(M00 * srcPts[srcOff] + M02)
                srcOff += 1
                dstOff += 1
                dstPts[dstOff] = float(M11 * srcPts[srcOff] + M12)
                srcOff += 1
                dstOff += 1
            return
        elif self.state == self.APPLY_SCALE:
            M00 = self.m00
            M11 = self.m11
            for _ in range(numPts):
                dstPts[dstOff] = float(M00 * srcPts[srcOff])
                srcOff += 1
                dstOff += 1
                dstPts[dstOff] = float(M11 * srcPts[srcOff])
                srcOff += 1
                dstOff += 1
            return
        elif self.state == self.APPLY_TRANSLATE:
            M02 = self.m02
            M12 = self.m12
            for _ in range(numPts):
                dstPts[dstOff] = float(srcPts[srcOff] + M02)
                srcOff += 1
                dstOff += 1
                dstPts[dstOff] = float(srcPts[srcOff] + M12)
                srcOff += 1
                dstOff += 1
            return
        elif self.state == self.APPLY_IDENTITY:
            if srcPts is not dstPts or srcOff != dstOff:
                dstPts[dstOff:dstOff + numPts * 2] = srcPts[srcOff:srcOff + numPts * 2]
            return
        else:
            self.state_error()

    def invert(self):
        M00 = 0.0
        M01 = 0.0
        M02 = 0.0
        M10 = 0.0
        M11 = 0.0
        M12 = 0.0
        det = 0.0

        if self.state == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M00 = self.m00
            M01 = self.m01
            M02 = self.m02
            M10 = self.m10
            M11 = self.m11
            M12 = self.m12
            det = M00 * M11 - M01 * M10
            if abs(det) <= sys.float_info.min:
                raise ValueError(f'Determinant is {det}')

            self.m00 =  M11 / det
            self.m10 = -M10 / det
            self.m01 = -M01 / det
            self.m11 =  M00 / det
            self.m02 = (M01 * M12 - M11 * M02) / det
            self.m12 = (M10 * M02 - M00 * M12) / det
            
        elif self.state  == self.APPLY_SHEAR | self.APPLY_SCALE:
            M00 = self.m00
            M01 = self.m01
            M10 = self.m10
            M11 = self.m11
            det = M00 * M11 - M01 * M10
            if abs(det) <= Double.MIN_VALUE:
                raise ValueError(f'Determinant is {det}')
            self.m00 =  M11 / det
            self.m10 = -M10 / det
            self.m01 = -M01 / det
            self.m11 =  M00 / det
            # self.m02 = 0.0
            # self.m12 = 0.0
        elif self.state == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            M01 = self.m01
            M02 = self.m02
            M10 = self.m10
            M12 = self.m12
            if M01 == 0.0 or M10 == 0.0:
                raise ValueError(f'Determinant is 0')
            # self.m00 = 0.0
            self.m10 = 1.0 / M01
            self.m01 = 1.0 / M10
            # self.m11 = 0.0
            self.m02 = -M12 / M10
            self.m12 = -M02 / M01
        elif self.state == self.APPLY_SHEAR:
            M01 = self.m01
            M10 = self.m10
            if M01 == 0.0 or M10 == 0.0:
                raise ValueError(f'Determinant is 0')
            # self.m00 = 0.0
            self.m10 = 1.0 / M01
            self.m01 = 1.0 / M10
            # self.m11 = 0.0
            # self.m02 = 0.0
            # self.m12 = 0.0
        elif self.state == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M00 = self.m00
            M02 = self.m02
            M11 = self.m11
            M12 = self.m12
            if M00 == 0.0 or M11 == 0.0:
                raise ValueError(f'Determinant is 0')
            self.m00 = 1.0 / M00
            # self.m10 = 0.0
            # self.m01 = 0.0
            self.m11 = 1.0 / M11
            self.m02 = -M02 / M00
            self.m12 = -M12 / M11
        elif self.state == self.APPLY_SCALE:
            M00 = self.m00
            M11 = self.m11
            if M00 == 0.0 or M11 == 0.0:
                raise ValueError(f'Determinant is 0')
            self.m00 = 1.0 / M00
            # self.m10 = 0.0
            # self.m01 = 0.0
            self.m11 = 1.0 / M11
            # self.m02 = 0.0
            # self.m12 = 0.0
        elif self.state == self.APPLY_TRANSLATE:
            # self.m00 = 1.0
            # self.m10 = 0.0
            # self.m01 = 0.0
            # self.m11 = 1.0
            self.m02 = -self.m02
            self.m12 = -self.m12
        elif self.state == self.APPLY_IDENTITY:
            # self.m00 = 1.0
            # self.m10 = 0.0
            # self.m01 = 0.0
            # self.m11 = 1.0
            # self.m02 = 0.0
            # self.m12 = 0.0
            pass
        else:
            self.stateError()
            return

    def deltaTransform(self, *args):
        if len(args) == 2 and self.arg_type_matcher(args, [Point2D, object]):
            self.deltaTransform_PP(args[0], args[1])
        elif len(args) == 5 and self.arg_type_matcher(args, [list, int, list, int, int]):
            self.deltaTransform_lilii(args[0], args[1], args[2], args[3], args[4])
        else:
            raise ValueError(f'deltaTransform args wrong {args}')

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L3701
    def deltaTransform_PP(self, ptSrc: Point2D, ptDst: Point2D) -> Point2D:
        if not ptDst:
            ptDst = Point2DF()

        # Copy source coords into local variables in case src == dst
        x = ptSrc.getX()
        y = ptSrc.getY()
        if self.state in {
            self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            ptDst.setLocation(x * self.m00 + y * self.m01, x * self.m10 + y * self.m11)
            return ptDst
        elif self.state in {
            self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR
        }:
            ptDst.setLocation(y * self.m01, x * self.m10)
            return ptDst
        elif self.state in {
            self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SCALE
        }:
            ptDst.setLocation(x * self.m00, y * self.m11)
            return ptDst
        elif self.state in {
            self.APPLY_TRANSLATE,
            self.APPLY_IDENTITY
        }:
            ptDst.setLocation(x, y)
            return ptDst
        else:
            self.stateError()

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L3769
    def deltaTransform_lilii(self, srcPts: list[float], srcOff: int, dstPts: list[float], dstOff: int, numPts: int):
        if dstPts is srcPts and dstOff > srcOff and dstOff < srcOff + numPts * 2:
            # Handle overlapping arrays by copying to a temporary location first
            dstPts[dstOff:dstOff + numPts * 2] = srcPts[srcOff : srcOff + numPts * 2]
            srcOff = dstOff

        if self.state in {
            self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            M00 = self.m00
            M01 = self.m01
            M10 = self.m10
            M11 = self.m11
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                y = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = x * M00 + y * M01
                dstOff += 1
                dstPts[dstOff] = x * M10 + y * M11
                dstOff += 1
            return
        elif self.state in {
            self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR
        }:
            M01 = self.m01
            M10 = self.m10
            for _ in range(numPts):
                x = srcPts[srcOff]
                srcOff += 1
                y = srcPts[srcOff]
                srcOff += 1
                dstPts[dstOff] = x * M00 + y * M01
                dstOff += 1
                dstPts[dstOff] = x * M10 + y * M11
                dstOff
            return
        elif self.state in {
            self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SCALE
        }:
            M00 = self.m00
            M11 = self.m11
            for _ in range(numPts):
                dstPts[dstOff] = srcPts[srcOff] * M00
                dstOff += 1
                srcOff += 1
                dstPts[dstOff] = srcPts[srcOff] * M11
                dstOff += 1
                srcOff += 1
            return
        elif self.state in {
            self.APPLY_TRANSLATE,
            self.APPLY_IDENTITY
        }:
            if srcPts is not dstPts or srcOff != dstOff:
                # Python's list slicing creates a shallow copy, which works like arraycopy for primitive types.
                dstPts[dstOff : dstOff + numPts * 2] = srcPts[srcOff : srcOff + numPts * 2]
            return
        else:
            self.stateError()

    def concatenate(self, Tx: Self):
        M0 = 0.0
        M1 = 0.0
        T00 = 0.0
        T01 = 0.0
        T02 = 0.0
        T10 = 0.0
        T11 = 0.0
        T12 = 0.0
        mystate = self.state
        txstate = Tx.state

        combined_state = (txstate << self.HI_SHIFT) | mystate

        # ---------- Tx == IDENTITY cases ----------
        if combined_state in {
            self.HI_IDENTITY | self.APPLY_IDENTITY,
            self.HI_IDENTITY | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SCALE,
            self.HI_IDENTITY | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SHEAR,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_SCALE,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE
        }:
            return
        # ---------- this == IDENTITY cases ----------
        elif combined_state == self.HI_SHEAR | self.HI_SCALE | self.HI_TRANSLATE | self.APPLY_IDENTITY:
            self.m01 = Tx.m01
            self.m10 = Tx.m10
            self.m00 = Tx.m00
            self.m11 = Tx.m11
            self.m02 = Tx.m02
            self.m12 = Tx.m12
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_SCALE | self.HI_TRANSLATE | self.APPLY_IDENTITY:
            self.m00 = Tx.m00
            self.m11 = Tx.m11
            self.m02 = Tx.m02
            self.m12 = Tx.m12
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_TRANSLATE | self.APPLY_IDENTITY:
            self.m02 = Tx.m02
            self.m12 = Tx.m12
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_SHEAR | self.HI_SCALE | self.APPLY_IDENTITY:
            self.m01 = Tx.m01
            self.m10 = Tx.m10
            self.m00 = Tx.m00
            self.m11 = Tx.m11
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_SCALE | self.APPLY_IDENTITY:
            self.m00 = Tx.m00
            self.m11 = Tx.m11
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_SHEAR | self.HI_TRANSLATE | self.APPLY_IDENTITY:
            self.m02 = Tx.m02
            self.m12 = Tx.m12
            self.m01 = Tx.m01
            self.m10 = Tx.m10
            self.m00 = 0.0
            self.m11 = 0.0
            self.state = txstate
            self.type = Tx.type
            return
        elif combined_state == self.HI_SHEAR | self.APPLY_IDENTITY:
            self.m01 = Tx.m01
            self.m10 = Tx.m10
            self.m00 = 0.0
            self.m11 = 0.0
            self.state = txstate
            self.type = Tx.type
            return

        # ---------- Tx == TRANSLATE cases ----------
        elif combined_state in {
            self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_SCALE,
            self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.HI_TRANSLATE | self.APPLY_SHEAR,
            self.HI_TRANSLATE | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_TRANSLATE | self.APPLY_SCALE,
            self.HI_TRANSLATE | self.APPLY_TRANSLATE
        }:
            self.translate(Tx.m02, Tx.m12)
            return

        # ---------- Tx == SCALE cases ----------
        elif combined_state in {
            self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_SCALE,
            self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.HI_SCALE | self.APPLY_SHEAR,
            self.HI_SCALE | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_SCALE | self.APPLY_SCALE,
            self.HI_SCALE | self.APPLY_TRANSLATE
        }:
            self.scale(Tx.m00, Tx.m11)
            return

        # ---------- Tx == SHEAR cases ----------
        elif combined_state in {
            self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            T01 = Tx.m01
            T10 = Tx.m10
            M0 = self.m00
            self.m00 = self.m01 * T10
            self.m01 = M0 * T01
            M0 = self.m10
            self.m10 = self.m11 * T10
            self.m11 = M0 * T01
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
            self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.HI_SHEAR | self.APPLY_SHEAR
        }:
            self.m00 = self.m01 * Tx.m10
            self.m01 = 0.0
            self.m11 = self.m10 * Tx.m01
            self.m10 = 0.0
            self.state = mystate ^ (self.APPLY_SHEAR | self.APPLY_SCALE)
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
            self.HI_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_SHEAR | self.APPLY_SCALE
        }:
            self.m01 = self.m00 * Tx.m01
            self.m00 = 0.0
            self.m10 = self.m11 * Tx.m10
            self.m11 = 0.0
            self.state = mystate ^ (self.APPLY_SHEAR | self.APPLY_SCALE)
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state == self.HI_SHEAR | self.APPLY_TRANSLATE:
            self.m00 = 0.0
            self.m01 = Tx.m01
            self.m10 = Tx.m10
            self.m11 = 0.0
            self.state = self.APPLY_TRANSLATE | self.APPLY_SHEAR
            self.type = self.TYPE_UNKNOWN
            return

        # If Tx has more than one attribute, it is not worth optimizing
        # all of those cases...
        T00 = Tx.m00
        T01 = Tx.m01
        T02 = Tx.m02
        T10 = Tx.m10
        T11 = Tx.m11
        T12 = Tx.m12

        # Second switch based on mystate
        if mystate == self.APPLY_SHEAR | self.APPLY_SCALE:
            self.state = mystate | txstate
            M0 = self.m00
            M1 = self.m01
            self.m00 = T00 * M0 + T10 * M1
            self.m01 = T01 * M0 + T11 * M1
            self.m02 += T02 * M0 + T12 * M1

            M0 = self.m10
            M1 = self.m11
            self.m10 = T00 * M0 + T10 * M1
            self.m11 = T01 * M0 + T11 * M1
            self.m12 += T02 * M0 + T12 * M1
            self.type = self.TYPE_UNKNOWN
            return
        elif mystate == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M0 = self.m00
            M1 = self.m01
            self.m00 = T00 * M0 + T10 * M1
            self.m01 = T01 * M0 + T11 * M1
            self.m02 += T02 * M0 + T12 * M1

            M0 = self.m10
            M1 = self.m11
            self.m10 = T00 * M0 + T10 * M1
            self.m11 = T01 * M0 + T11 * M1
            self.m12 += T02 * M0 + T12 * M1
            self.type = self.TYPE_UNKNOWN
            return
        elif mystate in {self.APPLY_SHEAR | self.APPLY_TRANSLATE, self.APPLY_SHEAR}:
            M0 = self.m01
            self.m00 = T10 * M0
            self.m01 = T11 * M0
            self.m02 += T12 * M0

            M0 = self.m10
            self.m10 = T00 * M0
            self.m11 = T01 * M0
            self.m12 += T02 * M0
        elif mystate in {self.APPLY_SCALE | self.APPLY_TRANSLATE, self.APPLY_SCALE}:
            M0 = self.m00
            self.m00 = T00 * M0
            self.m01 = T01 * M0
            self.m02 += T02 * M0

            M0 = self.m11
            self.m10 = T10 * M0
            self.m11 = T11 * M0
            self.m12 += T12 * M0
        elif mystate == self.APPLY_TRANSLATE:
            self.m00 = T00
            self.m01 = T01
            self.m02 += T02

            self.m10 = T10
            self.m11 = T11
            self.m12 += T12
            self.state = txstate | self.APPLY_TRANSLATE
            self.type = self.TYPE_UNKNOWN
            return
        else:
            self.stateError()
            pass

        self.udpateState()

    def preConcatenate(self, Tx: Self):
        M0 = 0.0
        M1 = 0.0
        T00 = 0.0
        T01 = 0.0
        T10 = 0.0
        T11 = 0.0
        T02 = 0.0
        T12 = 0.0
        mystate = self.state
        txstate = Tx.state
        combined_state = (txstate << self.HI_SHIFT) | mystate

        if combined_state in {
            self.HI_IDENTITY | self.APPLY_IDENTITY,
            self.HI_IDENTITY | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SCALE,
            self.HI_IDENTITY | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SHEAR,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_SCALE,
            self.HI_IDENTITY | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE
        }:
            # Tx is IDENTITY...
            return
        elif combined_state in {
        	self.HI_TRANSLATE | self.APPLY_IDENTITY,
        	self.HI_TRANSLATE | self.APPLY_SCALE,
        	self.HI_TRANSLATE | self.APPLY_SHEAR,
        	self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_SCALE,
        }:
            # Tx is TRANSLATE, this has no TRANSLATE
            self.m02 = Tx.m02
            self.m12 = Tx.m12
            self.state = mystate | self.APPLY_TRANSLATE
            self.type |= self.TYPE_TRANSLATION
            return
        elif combined_state in {
        	self.HI_TRANSLATE | self.APPLY_TRANSLATE,
        	self.HI_TRANSLATE | self.APPLY_SCALE | self.APPLY_TRANSLATE,
        	self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
        	self.HI_TRANSLATE | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE
        }:
            # Tx is TRANSLATE, this has one too
            self.m02 = self.m02 + Tx.m02
            self.m12 = self.m12 + Tx.m12
            return
        elif combined_state in {
        	self.HI_SCALE | self.APPLY_TRANSLATE,
        	self.HI_SCALE | self.APPLY_IDENTITY
        }:
            # Only these two existing states need a new state
            self.state = mystate | self.APPLY_SCALE
            T00 = Tx.m00
            T11 = Tx.m11
            if (mystate & self.APPLY_SHEAR) != 0:
                self.m01 = self.m01 * T00
                self.m10 = self.m10 * T11
                if (mystate & self.APPLY_SCALE) != 0:
                    self.m00 = self.m00 * T00
                    self.m11 = self.m11 * T11
            else:
                self.m00 = self.m00 * T00
                self.m11 = self.m11 * T11
            if (mystate & self.APPLY_TRANSLATE) != 0:
                self.m02 = self.m02 * T00
                self.m12 = self.m12 * T11
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
        	self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
        	self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_SCALE,
        	self.HI_SCALE | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
        	self.HI_SCALE | self.APPLY_SHEAR,
        	self.HI_SCALE | self.APPLY_SCALE | self.APPLY_TRANSLATE,
        	self.HI_SCALE | self.APPLY_SCALE
        }:
            # Tx is SCALE, this is anything
            T00 = Tx.m00
            T11 = Tx.m11
            if (mystate & self.APPLY_SHEAR) != 0:
                self.m01 = self.m01 * T00
                self.m10 = self.m10 * T11
                if (mystate & self.APPLY_SCALE) != 0:
                    self.m00 = self.m00 * T00
                    self.m11 = self.m11 * T11
            else:
                self.m00 = self.m00 * T00
                self.m11 = self.m11 * T11
            if (mystate & self.APPLY_TRANSLATE) != 0:
                self.m02 = self.m02 * T00
                self.m12 = self.m12 * T11
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
        	self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_TRANSLATE,
        	self.HI_SHEAR | self.APPLY_SHEAR
        }:
            mystate = mystate | self.APPLY_SCALE
            self.state = mystate ^ self.APPLY_SHEAR
            # Tx is SHEAR, this is anything
            T01 = Tx.m01
            T10 = Tx.m10

            M0 = self.m00
            self.m00 = self.m10 * T01
            self.m10 = M0 * T10

            M0 = self.m01
            self.m01 = self.m11 * T01
            self.m11 = M0 * T10

            M0 = self.m02
            self.m02 = self.m12 * T01
            self.m12 = M0 * T10
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
        	self.HI_SHEAR | self.APPLY_TRANSLATE,
        	self.HI_SHEAR | self.APPLY_IDENTITY,
        	self.HI_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
        	self.HI_SHEAR | self.APPLY_SCALE
        }:
            self.state = mystate ^ self.APPLY_SHEAR
            # Tx is SHEAR, this is anything
            T01 = Tx.m01
            T10 = Tx.m10

            M0 = self.m00
            self.m00 = self.m10 * T01
            self.m10 = M0 * T10

            M0 = self.m01
            self.m01 = self.m11 * T01
            self.m11 = M0 * T10

            M0 = self.m02
            self.m02 = self.m12 * T01
            self.m12 = M0 * T10
            self.type = self.TYPE_UNKNOWN
            return
        elif combined_state in {
        	self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
        	self.HI_SHEAR | self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            # Tx is SHEAR, this is anything
            T01 = Tx.m01
            T10 = Tx.m10

            M0 = self.m00
            self.m00 = self.m10 * T01
            self.m10 = M0 * T10

            M0 = self.m01
            self.m01 = self.m11 * T01
            self.m11 = M0 * T10

            M0 = self.m02
            self.m02 = self.m12 * T01
            self.m12 = M0 * T10
            self.type = self.TYPE_UNKNOWN
            return

        # If Tx has more than one attribute, it is not worth optimizing
        # all of those cases...
        T00 = Tx.m00
        T01 = Tx.m01
        T02 = Tx.m02
        T10 = Tx.m10
        T11 = Tx.m11
        T12 = Tx.m12

        if mystate == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M0 = self.m02
            M1 = self.m12
            T02 += M0 * T00 + M1 * T01
            T12 += M0 * T10 + M1 * T11

            self.m02 = T02
            self.m12 = T12

            M0 = self.m00
            M1 = self.m10
            self.m00 = M0 * T00 + M1 * T01
            self.m10 = M0 * T10 + M1 * T11

            M0 = self.m01
            M1 = self.m11
            self.m01 = M0 * T00 + M1 * T01
            self.m11 = M0 * T10 + M1 * T11
        elif mystate == self.APPLY_SHEAR | self.APPLY_SCALE:
            self.m02 = T02
            self.m12 = T12

            M0 = self.m00
            M1 = self.m10
            self.m00 = M0 * T00 + M1 * T01
            self.m10 = M0 * T10 + M1 * T11

            M0 = self.m01
            M1 = self.m11
            self.m01 = M0 * T00 + M1 * T01
            self.m11 = M0 * T10 + M1 * T11
        elif mystate == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            M0 = self.m02
            M1 = self.m12
            T02 += M0 * T00 + M1 * T01
            T12 += M0 * T10 + M1 * T11

            self.m02 = T02
            self.m12 = T12

            M0 = self.m10
            self.m00 = M0 * T01
            self.m10 = M0 * T11

            M0 = self.m01
            self.m01 = M0 * T00
            self.m11 = M0 * T10
        elif mystate == self.APPLY_SHEAR:
            self.m02 = T02
            self.m12 = T12

            M0 = self.m10
            self.m00 = M0 * T01
            self.m10 = M0 * T11

            M0 = self.m01
            self.m01 = M0 * T00
            self.m11 = M0 * T10
        elif mystate == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            M0 = self.m02
            M1 = self.m12
            T02 += M0 * T00 + M1 * T01
            T12 += M0 * T10 + M1 * T11

            self.m02 = T02
            self.m12 = T12

            M0 = self.m00
            self.m00 = M0 * T00
            self.m10 = M0 * T10

            M0 = self.m11
            self.m01 = M0 * T01
            self.m11 = M0 * T11
        elif mystate == self.APPLY_SCALE:
            self.m02 = T02
            self.m12 = T12

            M0 = self.m00
            self.m00 = M0 * T00
            self.m10 = M0 * T10

            M0 = self.m11
            self.m01 = M0 * T01
            self.m11 = M0 * T11
        elif mystate == self.APPLY_TRANSLATE:
            M0 = self.m02
            M1 = self.m12
            T02 += M0 * T00 + M1 * T01
            T12 += M0 * T10 + M1 * T11

            self.m02 = T02
            self.m12 = T12

            self.m00 = T00
            self.m10 = T10

            self.m01 = T01
            self.m11 = T11

            self.state = mystate | txstate
            self.type = self.TYPE_UNKNOWN

            return
        elif mystate == self.APPLY_IDENTITY:
            self.m02 = T02
            self.m12 = T12

            self.m00 = T00
            self.m10 = T10

            self.m01 = T01
            self.m11 = T11

            self.state = mystate | txstate
            self.type = self.TYPE_UNKNOWN
            return
        else:
            self.stateError()
        self.updateState()

    def translate(self, tx: float, ty: float):
        current_state = self.state
        if current_state == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            self.m02 = tx * self.m00 + ty * self.m01 + self.m02
            self.m12 = tx * self.m10 + ty * self.m11 + self.m12
            if self.m02 == 0.0 and self.m12 == 0.0:
                self.state = self.APPLY_SHEAR | self.APPLY_SCALE
                if self.type != self.TYPE_UNKNOWN:
                    self.type -= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_SHEAR | self.APPLY_SCALE:
            self.m02 = tx * self.m00 + ty * self.m01
            self.m12 = tx * self.m10 + ty * self.m11
            if self.m02 != 0.0 or self.m12 != 0.0:
                self.state = self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE
                self.type |= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            self.m02 = ty * self.m01 + self.m02
            self.m12 = tx * self.m10 + self.m12
            if self.m02 == 0.0 and self.m12 == 0.0:
                self.state = self.APPLY_SHEAR
                if self.type != self.TYPE_UNKNOWN:
                    self.type -= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_SHEAR:
            self.m02 = ty * self.m01
            self.m12 = tx * self.m10
            if self.m02 != 0.0 or self.m12 != 0.0:
                self.state = self.APPLY_SHEAR | self.APPLY_TRANSLATE
                self.type |= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            self.m02 = tx * self.m00 + self.m02
            self.m12 = ty * self.m11 + self.m12
            if self.m02 == 0.0 and self.m12 == 0.0:
                self.state = self.APPLY_SCALE
                if self.type != self.TYPE_UNKNOWN:
                    self.type -= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_SCALE:
            self.m02 = tx * self.m00
            self.m12 = ty * self.m11
            if self.m02 != 0.0 or self.m12 != 0.0:
                self.state = self.APPLY_SCALE | self.APPLY_TRANSLATE
                self.type |= self.TYPE_TRANSLATION
            return
        elif current_state == self.APPLY_TRANSLATE:
            self.m02 = tx + self.m02
            self.m12 = ty + self.m12
            if self.m02 == 0.0 and self.m12 == 0.0:
                self.state = self.APPLY_IDENTITY
                self.type = self.TYPE_IDENTITY
            return
        elif current_state == self.APPLY_IDENTITY:
            self.m02 = tx
            self.m12 = ty
            if tx != 0.0 or ty != 0.0:
                self.state = self.APPLY_TRANSLATE
                self.type = self.TYPE_TRANSLATION
            return
        else: # default case
            self.stateError()
            # If state_error raises an exception, this 'return' is unreachable.
            return

    def rotate90(self):
        M0 = self.m00
        self.m00 = self.m01
        self.m01 = -M0
        M0 = self.m10
        self.m10 = self.m11
        self.m11 = -M0
        state = rot90conversion[self.state]
        if (state & (self.APPLY_SHEAR | self.APPLY_SCALE)) == self.APPLY_SCALE and self.m00 == 1.0 and self.m11 == 1.0:
            state -= APPLY_SCALE
        self.state = state
        self.type = TYPE_UNKNOWN

    def rotate180(self):
        self.m00 = -self.m00
        self.m11 = -self.m11
        state = self.state
        if (self.state & self.APPLY_SHEAR) != 0:
            self.m01 = -self.m01
            self.m10 = -self.m10
        else:
            if self.m00 == 1.0 and self.m11 == 1.0:
                self.state = state & ~APPLY_SCALE
            else:
                self.state = state | APPLY_SCALE
        self.type = TYPE_UNKNOWN
    
    def rotate270(self):
        M0 = self.m00
        self.m00 = -self.m01
        self.m01 = M0
        M0 = self.m10
        self.m10 = -self.m11
        self.m11 = M0
        state = rot90conversion[self.state]
        if self.state & (self.APPLY_SHEAR | self.APPLY_SCALE) == self.APPLY_SCALE and self.m00 == 1.0 and self.m11 == 1.0:
            state -= APPLY_SCALE
        self.state = state
        self.type = TYPE_UNKNOWN

    def rotate(self, *args):
        if len(args) == 1 and self.arg_type_matcher(args, [float]):
            self.rotate_f(args[0])
        elif len(args) == 3 and self.arg_type_matcher(args, [float] * 3):
            self.rotate_fff(args[0], args[1], args[2])
        else:
            raise ValueError(f'rotate args wrong {args}')

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L1429
    def rotate_f(self, theta: float):
        sin = math.sin(theta)
        if sin == 1.0:
            self.rotate90()
        elif sin == -1.0:
            self.rotate270()
        else:
            cos = math.cos(theta)
            if cos == -1.0:
                rotate180()
            elif cos != 1.0:
                M0 = self.m00
                M1 = self.m01
                self.m00 =  cos * M0 + sin * M1
                self.m01 = -sin * M0 + cos * M1
                M0 = self.m10
                M1 = self.m11
                self.m10 =  cos * M0 + sin * M1
                self.m11 = -sin * M0 + cos * M1
                self.updateState()

    # https://github.com/openjdk/jdk/blob/76442f39b9dd583f09a7adebb0fc5f37b6ef88ef/src/java.desktop/share/classes/java/awt/geom/AffineTransform.java#L1480
    def rotate_fff(self, theta: float, anchorx: float, anchory: float):
        self.translate(anchorx, anchory)
        self.rotate(theta)
        self.translate(-anchorx, -anchory)

    def scale(self, sx: float, sy: float):
        current_state = self.state
        if current_state in {
            self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE, 
            self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            self.m00 *= sx
            self.m11 *= sy
            self.m01 *= sy
            self.m10 *= sx
            if self.m01 == 0 and self.m10 == 0:
                current_state &= self.APPLY_TRANSLATE
                if self.m00 == 1.0 and self.m11 == 1.0:
                    self.type = self.TYPE_IDENTITY if current_state == self.APPLY_IDENTITY else self.TYPE_TRANSLATION
                else:
                    current_state |= self.APPLY_SCALE
                    self.type = self.TYPE_UNKNOWN
                self.state = current_state
            return
        elif current_state in {
            self.APPLY_SHEAR | self.APPLY_TRANSLATE, 
            self.APPLY_SHEAR
        }:
            self.m01 *= sy
            self.m10 *= sx
            if self.m01 == 0 and self.m10 == 0:
                current_state &= self.APPLY_TRANSLATE
                if self.m00 == 1.0 and self.m11 == 1.0:
                    self.type = self.TYPE_IDENTITY if current_state == self.APPLY_IDENTITY else self.TYPE_TRANSLATION
                else:
                    current_state |= self.APPLY_SCALE
                    self.type = self.TYPE_UNKNOWN
                self.state = current_state
            return
        elif current_state in {
            self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SCALE
        }:
            self.m00 *= sx
            self.m11 *= sy
            if self.m00 == 1.0 and self.m11 == 1.0:
                current_state &= self.APPLY_TRANSLATE
                self.state = current_state
                self.type = self.TYPE_IDENTITY if current_state == self.APPLY_IDENTITY else self.TYPE_TRANSLATION
            else:
                self.type = self.TYPE_UNKNOWN
            return
        elif current_state in {
            self.APPLY_TRANSLATE, self.APPLY_IDENTITY
        }:
            self.m00 = sx
            self.m11 = sy
            if sx != 1.0 or sy != 1.0:
                self.state = current_state | self.APPLY_SCALE
                self.type = self.TYPE_UNKNOWN
            return
        else:
            self.stateError()

    def shear(self, shx: float, shy: float):
        current_state = self.state
        if current_state in {
            self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR | self.APPLY_SCALE
        }:
            M0 = self.m00
            M1 = self.m01
            self.m00 = M0 + M1 * shy
            self.m01 = M0 * shx + M1

            M0 = self.m10
            M1 = self.m11
            self.m10 = M0 + M1 * shy
            self.m11 = M0 * shx + M1
            self.updateState()
            return
        elif current_state in { 
            self.APPLY_SHEAR | self.APPLY_TRANSLATE,
            self.APPLY_SHEAR 
        }:
            self.m00 = self.m01 * shy
            self.m11 = self.m10 * shx
            if self.m00 != 0.0 or self.m11 != 0.0:
                self.state = current_state | self.APPLY_SCALE
            self.type = self.TYPE_UNKNOWN
            return
        elif current_state in { 
            self.APPLY_SCALE | self.APPLY_TRANSLATE,
            self.APPLY_SCALE 
        }:
            self.m01 = self.m00 * shx
            self.m10 = self.m11 * shy
            if self.m01 != 0.0 or self.m10 != 0.0:
                self.state = current_state | self.APPLY_SHEAR
            self.type = self.TYPE_UNKNOWN
            return
        elif current_state in { self.APPLY_TRANSLATE, self.APPLY_IDENTITY }:
            self.m01 = shx
            self.m10 = shy
            if self.m01 != 0.0 or self.m10 != 0.0:
                self.state = current_state | self.APPLY_SCALE | self.APPLY_SHEAR
                self.type = self.TYPE_UNKNOWN
            return
        else: # default case
            self.stateError()
            # If state_error raises an exception, this 'return' is unreachable.
            return

    def isIdentity(self) -> bool:
        return self.state == self.APPLY_IDENTITY or (self.getType() == self.TYPE_IDENTITY)

    def stateError(self):
        raise Exception('missing case in transform state switch')