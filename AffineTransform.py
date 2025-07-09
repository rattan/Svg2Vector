from Point2D import Point2DF, Point2D

from typing import Self
import sys

import math

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

    # Sets this transform to a copy of the transform in the specified
    # {@code AffineTransform} object.
    # @param Tx the {@code AffineTransform} object from which to
    # copy the transform
    # @since 1.2
    def setTransform(self, Tx: Self):
        self.m00 = Tx.m00
        self.m10 = Tx.m10
        self.m01 = Tx.m01
        self.m11 = Tx.m11
        self.m02 = Tx.m02
        self.m12 = Tx.m12
        self.state = Tx.state
        self.type = Tx.type

    def setTransform6(self, m00: float, m10: float, m01: float, m11: float, m02: float, m12: float):
        self.m00 = m00
        self.m10 = m10
        self.m01 = m01
        self.m11 = m11
        self.m02 = m02
        self.m12 = m12


    # Retrieves the flag bits describing the conversion properties of
    # this transform.
    # The return value is either one of the constants TYPE_IDENTITY
    # or TYPE_GENERAL_TRANSFORM, or a combination of the
    # appropriate flag bits.
    # A valid combination of flag bits is an exclusive OR operation
    # that can combine
    # the TYPE_TRANSLATION flag bit
    # in addition to either of the
    # TYPE_UNIFORM_SCALE or TYPE_GENERAL_SCALE flag bits
    # as well as either of the
    # TYPE_QUADRANT_ROTATION or TYPE_GENERAL_ROTATION flag bits.
    # @return the OR combination of any of the indicated flags that
    # apply to this transform
    # @see #TYPE_IDENTITY
    # @see #TYPE_TRANSLATION
    # @see #TYPE_UNIFORM_SCALE
    # @see #TYPE_GENERAL_SCALE
    # @see #TYPE_QUADRANT_ROTATION
    # @see #TYPE_GENERAL_ROTATION
    # @see #TYPE_GENERAL_TRANSFORM
    # @since 1.2
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
        if self.type == self.APPLY_SHEAR | self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
        elif self.type == self.APPLY_SHEAR | self.APPLY_SCALE:
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
        elif self.type == self.APPLY_SHEAR | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
        elif self.type == self.APPLY_SHEAR:
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
        elif self.type == self.APPLY_SCALE | self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
        elif self.type == self.APPLY_SCALE:
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
        elif self.type == self.APPLY_TRANSLATE:
            ret = self.TYPE_TRANSLATION
        elif self.type == self.APPLY_IDENTITY:
            pass
        else:
            stateError()
        self.type = ret

    # Transforms the specified {@code ptSrc} and stores the result
    # in {@code ptDst}.
    # If {@code ptDst} is {@code null}, a new {@link Point2D}
    # object is allocated and then the result of the transformation is
    # stored in this object.
    # In either case, {@code ptDst}, which contains the
    # transformed point, is returned for convenience.
    # If {@code ptSrc} and {@code ptDst} are the same
    # object, the input point is correctly overwritten with
    # the transformed point.
    # @param ptSrc the specified {@code Point2D} to be transformed
    # @param ptDst the specified {@code Point2D} that stores the
    # result of transforming {@code ptSrc}
    # @return the {@code ptDst} after transforming
    # {@code ptSrc} and storing the result in {@code ptDst}.
    # @since 1.2
    def transform2(self, ptSrc, ptDst):
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
        return tpDst

    # Transforms an array of floating point coordinates by this transform.
    # The two coordinate array sections can be exactly the same or
    # can be overlapping sections of the same array without affecting the
    # validity of the results.
    # This method ensures that no source coordinates are overwritten by a
    # previous operation before they can be transformed.
    # The coordinates are stored in the arrays starting at the specified
    # offset in the order {@code [x0, y0, x1, y1, ..., xn, yn]}.
    # @param srcPts the array containing the source point coordinates.
    # Each point is stored as a pair of x,&nbsp;y coordinates.
    # @param srcOff the offset to the first point to be transformed
    # in the source array
    # @param dstPts the array into which the transformed point coordinates
    # are returned.  Each point is stored as a pair of x,&nbsp;y
    # coordinates.
    # @param dstOff the offset to the location of the first
    # transformed point that is stored in the destination array
    # @param numPts the number of points to be transformed
    # @since 1.2
    def transform5(self, srcPts: list[float], srcOff: int, dstPts: list[float], dstOff: int, numPts: int):
        M00 = 0.0
        M01 = 0.0
        M02 = 0.0
        M10 = 0.0
        M11 = 0.0
        M12 = 0.0
        if dstPts == srcPts and srcOff < dstOff and desOff < srcOff + numPts * 2:
            # If the arrays overlap partially with the destination higher
            # than the source and we transform the coordinates normally
            # we would overwrite some of the later source coordinates
            # with results of previous transformations.
            # To get around this we use arraycopy to copy the points
            # to their final destination with correct overwrite
            # handling and then transform them in place in the new
            # safer location.
            dstPts[dstOff:dstOff + numPts * 2] = srcPts[srcOff:srcOff + numPts * 2]
            # srcPts = dstPts;         // They are known to be equal.
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

    # Sets this transform to the inverse of itself.
    # The inverse transform Tx' of this transform Tx
    # maps coordinates transformed by Tx back
    # to their original coordinates.
    # In other words, Tx'(Tx(p)) = p = Tx(Tx'(p)).
    # <p>
    # If this transform maps all coordinates onto a point or a line
    # then it will not have an inverse, since coordinates that do
    # not lie on the destination point or line will not have an inverse
    # mapping.
    # The {@code getDeterminant} method can be used to determine if this
    # transform has no inverse, in which case an exception will be
    # thrown if the {@code invert} method is called.
    # @see #getDeterminant
    # @throws NoninvertibleTransformException
    # if the matrix cannot be inverted.
    # @since 1.6
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

    def deltaTransform(self, ptSrc: Point2D, ptDst: Point2D) -> Point2D:
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

    # Concatenates an {@code AffineTransform Tx} to
    # this {@code AffineTransform} Cx in the most commonly useful
    # way to provide a new user space
    # that is mapped to the former user space by {@code Tx}.
    # Cx is updated to perform the combined transformation.
    # Transforming a point p by the updated transform Cx' is
    # equivalent to first transforming p by {@code Tx} and then
    # transforming the result by the original transform Cx like this:
    # Cx'(p) = Cx(Tx(p))
    # In matrix notation, if this transform Cx is
    # represented by the matrix [this] and {@code Tx} is represented
    # by the matrix [Tx] then this method does the following:
    # <pre>
    #          [this] = [this] x [Tx]
    # </pre>
    # @param Tx the {@code AffineTransform} object to be
    # concatenated with this {@code AffineTransform} object.
    # @see #preConcatenate
    # @since 1.2
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

    # Concatenates an {@code AffineTransform Tx} to
    # this {@code AffineTransform} Cx
    # in a less commonly used way such that {@code Tx} modifies the
    # coordinate transformation relative to the absolute pixel
    # space rather than relative to the existing user space.
    # Cx is updated to perform the combined transformation.
    # Transforming a point p by the updated transform Cx' is
    # equivalent to first transforming p by the original transform
    # Cx and then transforming the result by
    # {@code Tx} like this:
    # Cx'(p) = Tx(Cx(p))
    # In matrix notation, if this transform Cx
    # is represented by the matrix [this] and {@code Tx} is
    # represented by the matrix [Tx] then this method does the
    # following:
    # <pre>
    #          [this] = [Tx] x [this]
    # </pre>
    # @param Tx the {@code AffineTransform} object to be
    # concatenated with this {@code AffineTransform} object.
    # @see #concatenate
    # @since 1.2
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

    # Concatenates this transform with a translation transformation.
    # This is equivalent to calling concatenate(T), where T is an
    # {@code AffineTransform} represented by the following matrix:
    # <pre>
    #          [   1    0    tx  ]
    #          [   0    1    ty  ]
    #          [   0    0    1   ]
    # </pre>
    # @param tx the distance by which coordinates are translated in the
    # X axis direction
    # @param ty the distance by which coordinates are translated in the
    # Y axis direction
    # @since 1.2
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
        elif current_state == (self.APPLY_SCALE | self.APPLY_TRANSLATE):
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

    def rotate1(self, theta: float):
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

    def rotate(self, theta: float, anchorx: float, anchory: float):
        self.translate(anchorx, anchory)
        self.rotate1(theta)
        self.translate(-anchorx, -anchory)

    # Concatenates this transform with a scaling transformation.
    # This is equivalent to calling concatenate(S), where S is an
    # {@code AffineTransform} represented by the following matrix:
    # <pre>
    #          [   sx   0    0   ]
    #          [   0    sy   0   ]
    #          [   0    0    1   ]
    # </pre>
    # @param sx the factor by which coordinates are scaled along the
    # X axis direction
    # @param sy the factor by which coordinates are scaled along the
    # Y axis direction
    # @since 1.2
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
                    self.type = self.TYPE_IDENTITY if current_state == APPLY_IDENTITY else self.TYPE_TRANSLATION
                else:
                    current_state |= APPLY_SCALE
                    self.type = TYPE_UNKNOWN
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
                    self.type = self.TYPE_IDENTITY if current_state == APPLY_IDENTITY else self.TYPE_TRANSLATION
                else:
                    current_state |= APPLY_SCALE
                    self.type = TYPE_UNKNOWN
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

    # Concatenates this transform with a shearing transformation.
    # This is equivalent to calling concatenate(SH), where SH is an
    # {@code AffineTransform} represented by the following matrix:
    # <pre>
    #          [   1   shx   0   ]
    #          [  shy   1    0   ]
    #          [   0    0    1   ]
    # </pre>
    # @param shx the multiplier by which coordinates are shifted in the
    # direction of the positive X axis as a factor of their Y coordinate
    # @param shy the multiplier by which coordinates are shifted in the
    # direction of the positive Y axis as a factor of their X coordinate
    # @since 1.2
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

    # Returns {@code true} if this {@code AffineTransform} is
    # an identity transform.
    # @return {@code true} if this {@code AffineTransform} is
    # an identity transform; {@code false} otherwise.
    # @since 1.2
    def isIdentity(self) -> bool:
        return self.state == self.APPLY_IDENTITY or (self.getType() == self.TYPE_IDENTITY)

    def stateError(self):
        raise Exception('missing case in transform state switch')