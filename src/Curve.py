import math

class Curve:
    # https://github.com/openjdk/jdk/blob/0bd2f9cba2118ed5a112b4c70b8ff4a1a58f21dd/src/java.desktop/share/classes/sun/awt/geom/Curve.java#L738
    @classmethod
    def accumulateExtremaBoundsForQuad(cls, bounds: list[float], boundsOffset: int, x1: float, ctrlX: float, x2: float, coeff: list[float], deriv_coeff: list[float]):
        if ctrlX < boundss[boundsOffset] or bounds[boundsOffset + 1] < ctrlX:
            dx21 = ctrlX - x1
            coeff[2] = (x2 - ctrlX) - dx21
            coeff[1] = 2.0 * dx21
            coeff[0] = x1

            deriv_coeff[0] = coeff[1]
            deriv_coeff[1] = 2.0 * coeff[2]

            t = -deriv_coeff[0] / deriv_coeff[1]
            if 0.0 < t < 1.0:
                v = coeff[0] + t * (coeff[1] + t * coeff[2])

                margin = math.ulp(abs(coeff[0]) + abs(coeff[1]) + abs(coeff[2]))

                if v - margin < bounds[boundsOffset]:
                    bounds[boundsOffset] = v - margin
                if v + margin > bounds[boundsOffset + 1]:
                    bounds[boundsOffset + 1] = v + margin

    # https://github.com/openjdk/jdk/blob/0bd2f9cba2118ed5a112b4c70b8ff4a1a58f21dd/src/java.desktop/share/classes/java/awt/geom/QuadCurve2D.java#L854
    @classmethod
    def solveQuadratic(cls, eqn: list[float], res: list[float]):
        a = eqn[2]
        b = eqn[1]
        c = eqn[0]
        roots = 0
        if a == 0.0:
            if b == 0.0:
                return -1
            res[roots] = -c / b
            roots += 1
        else:
            d = b * b - 4.0 * a * c
            if d < 0.0:
                return 0
            d = math.sqrt(d)
            if b < 0.0:
                d = -d
            q = (b + d) / -2.0
            res[roots] = q / a
            roots += 1
            if q != 0.0:
                res[roots] = c / q
                roots += 1
        return roots


    # https://github.com/openjdk/jdk/blob/0bd2f9cba2118ed5a112b4c70b8ff4a1a58f21dd/src/java.desktop/share/classes/sun/awt/geom/Curve.java#L792
    @classmethod
    def accumulateExtremaBoundsForCubic(cls, bounds: list[float], boundsOffset: int, x1: float, ctrlX1: float, ctrlX2: float, x2: float, coeff: list[float], deriv_coeff: list[float]):
        if ctrlX1 < bounds[boundsOffset] or ctrlX1 > bounds[boundsOffset + 1] or ctrlX2 < bounds[boundsOffset] or ctrlX2 > bounds[boundsOffset + 1]:
            dx32 = 3.0 * (ctrlX2 - ctrlX1)
            dx21 = 3.0 * (ctrlX1 - x1)
            coeff[3] = (x2 - x1) - dx32
            coeff[2] = (dx32 - dx21)
            coeff[1] = dx21
            coeff[0] = x1

            deriv_coeff[0] = coeff[1]
            deriv_coeff[1] = 2.0 * coeff[2]
            deriv_coeff[2] = 3.0 * coeff[3]

            tExtrema = [0.0, 0.0] 

            tExtremaCount = cls.solveQuadratic(deriv_coeff, tExtrema)
            
            if tExtremaCount > 0:
                margin = math.ulp(abs(coeff[0]) + abs(coeff[1]) + abs(coeff[2]) + abs(coeff[3]))

                for i in range(tExtremaCount):
                    t = tExtrema[i]
                    if 0.0 < t < 1.0:
                        v = coeff[0] + t * (coeff[1] + t * (coeff[2] + t * coeff[3]))
                        if v - margin < bounds[boundsOffset]:
                            bounds[boundsOffset] = v - margin
                        if v + margin > bounds[boundsOffset + 1]:
                            bounds[boundsOffset + 1] = v + margin