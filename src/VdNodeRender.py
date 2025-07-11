import math

from Path2D import Path2D
from VdPath import VdPath

class VdNodeRender:
    @classmethod
    def createPath(cls, nodes: list[VdPath.Node], path: Path2D):
        current = [0.0] * 6
        lastCmd = ' '
        for node in nodes:
            cls.addCommand(path, current, node.getType(), lastCmd, node.getParams())
            lastCmd = node.getType()

    @classmethod
    def addCommand(cls, path: Path2D, current: list[float], cmd: str, lastCmd: list[float], val: list[float]):
        incr = 2
        cx = current[0]
        cy = current[1]
        cpx = current[2]
        cpy = current[3]
        loopX = current[4]
        loopY = current[5]

        if cmd in ['z', 'Z']:
            cx = loopX
            vy = loopY
            incr = 2
        elif cmd in ['m', 'M', 'l', 'L', 't', 'T']:
            incr = 2
        elif cmd in ['h', 'H', 'v', 'V']:
            incr = 1
        elif cmd in ['c', 'C']:
            incr = 6
        elif cmd in ['s', 'S', 'q', 'Q']:
            incr = 4
        elif cmd in ['a', 'A']:
            incr = 7
        
        for k in range(0, len(val), incr):
            reflectCtrl = False
            tempReflectedX = 0.0
            tempReflectedY = 0.0

            if cmd == 'm':
                cx += val[k]
                cy += val[k + 1]
                if k > 0:
                    path.lineTo(cx, cy)
                else:
                    path.moveTo(cx, cy)
                    loopX = cx
                    loopY = cy
            elif cmd == 'M':
                cx = val[k]
                cy = val[k + 1]
                if k > 0:
                    path.lineTo(cx, cy)
                else:
                    path.moveTo(cx, cy)
                    loopX = cx
                    loopY = cy
            elif cmd == 'l':
                cx += val[k]
                cy += val[k + 1]
                path.lineTo(cx, cy)
            elif cmd == 'L':
                cx = val[k]
                cy = val[k + 1]
                path.lineTo(cx, cy)
            elif cmd in ['z', 'Z']:
                path.closePath()
                cx = loopX
                cy = loopY
            elif cmd == 'h':
                cx += val[k]
                path.lineTo(cx, cy)
            elif cmd == 'H':
                path.lineTo(val[k], cy)
                cx = val[k]
            elif cmd == 'v':
                cy += val[k]
                path.lineTo(cx, cy)
            elif cmd == 'V':
                path.lineTo(cx, val[k])
                cy = val[k]
            elif cmd == 'c':
                path.curveTo(cx + val[k], cy + val[k + 1], cx + val[k + 2], cy + val[k + 3], cx + val[k + 4], cy + val[k + 5])
                cpx = cx + val[k + 2]
                cpy = cy + val[k + 3]
                cx += val[k + 4]
                cy += val[k + 5]
            elif cmd == 'C':
                path.curveTo(val[k], val[k + 1], val[k + 2], val[k + 3], val[k + 4], val[k + 5])
                cx = val[k + 4]
                cy = val[k + 5]
                cpx = val[k + 2]
                cpy = val[k + 3]
            elif cmd == 's':
                reflectCtrl = lastCmd in ['c', 's', 'C', 'S']
                path.curveTo(reflectCtrl and 2 * cx - cpx or cx, reflectCtrl and 2 * cy - cpy or cy, cx + val[k], cy + val[k + 1], cx + val[k + 2], cy + val[k + 3])
                cpx = cx + val[k]
                cpy = cy + val[k + 1]
                cx += val[k + 2]
                cy += val[k + 3]
            elif cmd == 'S':
                reflectCtrl = (lastCmd in ['c', 's', 'C', 'S'])
                path.curveTo(reflectCtrl and 2 * cx - cpx or cx, reflectCtrl and 2 * cy - cpy or cy, val[k], val[k + 1], val[k + 2], val[k + 3])
                cpx = val[k]
                cpy = val[k + 1]
                cx = val[k + 2]
                cy = val[k + 3]
            elif cmd == 'q':
                path.quadTo(cx + val[k], cy + val[k + 1], cx + val[k + 2], cy + val[k + 3])
                cpx = cx + val[k]
                cpy = cy + val[k + 1]
                cx += val[k + 2]
                cy += val[k + 3]
            elif cmd == 'Q':
                path.quadTo(val[k], val[k + 1], val[k + 2], val[k + 3])
                cx = val[k + 2]
                cy = val[k + 3]
                cpx = val[k]
                cpy = val[k + 1]
            elif cmd == 't':
                reflectCtrl = lastCmd in ['q', 't', 'Q', 'T']
                tempReflectedX = 2 * cx - cpx if reflectCtrl else cx
                tempReflectedY = 2 * cy - cpy if reflectCtrl else cy
                path.quadTo(tempReflectedX, tempReflectedY, cx + val[k], cy + val[k + 1])
                cpx = tempReflectedX
                cpy = tempReflectedY
                cx += val[k]
                cy += val[k + 1]
            elif cmd == 'T':
                reflectCtrl = (lastCmd in ['q', 't', 'Q', 'T'])
                tempReflectedX = 2 * cx - cpx if reflectCtrl else cx
                tempReflectedY = 2 * cy - cpy if reflectCtrl else cy
                path.quadTo(tempReflectedX, tempReflectedY, val[k], val[k + 1])
                cx = val[k]
                cy = val[k + 1]
                cpx = tempReflectedX
                cpy = tempReflectedY
            elif cmd == 'a':
                cls.drawArc(path, cx, cy, val[k + 5] + cx, val[k + 6] + cy, abs(val[k]), abs(val[k + 1]), val[k + 2], val[k + 3] != 0, val[k + 4] != 0)
                cx += val[k + 5]
                cy += val[k + 6]
                cpx = cx
                cpy = cy
            elif cmd == 'A':
                cls.drawArc(path, cx, cy, val[k + 5], val[k + 6], abs(val[k]), abs(val[k + 1]), val[k + 2], val[k + 3] != 0, val[k + 4] != 0)
                cx = val[k + 5]
                cy = val[k + 6]
                cpx = cx
                cpy = cy
            lastCmd = cmd
        current[0] = cx
        current[1] = cy
        current[2] = cpx
        current[3] = cpy
        current[4] = loopX
        current[5] = loopY

    @classmethod
    def drawArc(cls, p: Path2D, x0: float, y0: float, x1: float, y1: float, a: float, b: float, theta: float, isMoreThanHalf: bool, isPositiveArc: bool):
        # print(f'({x0},{y0})-({x1},{y1}) {{{a} {b}}}')
        thetaD = theta * math.pi / 180.0
        cosTheta = math.cos(thetaD)
        sinTheta = math.sin(thetaD)
        x0p = (x0 * cosTheta + y0 * sinTheta) / a
        y0p = (-x0 * sinTheta + y0 * cosTheta) / b
        x1p = (x1 * cosTheta + y1 * sinTheta) / a
        y1p = (-x1 * sinTheta + y1 * cosTheta) / b
        # print(f'unit space ({x0p},{y0p})-({x1p},{y1p})')

        dx = x0p - x1p
        dy = y0p - y1p
        xm = (x0p + x1p) / 2
        ym = (y0p + y1p) / 2

        dsq = dx * dx + dy * dy
        if dsq == 0.0:
            # print(' Points are coincident')
            return

        disc = 1.0 / dsq - 1.0 / 4.0
        if disc < 0.0:
            # print(f'Points are too far apart {dsq}')
            adjust = math.sqrt(dsq) / 1.99999
            cls.drawArc(p, x0, y0, x1, y1, a * adjust, b * adjust, theta, isMoreThanHalf, isPositiveArc)
            return

        s = math.sqrt(disc)
        sdx = s * dx
        sdy = s * dy

        if isMoreThanHalf == isPositiveArc:
            cx = xm - sdy
            cy = ym + sdx
        else:
            cx = xm + sdy
            cy = ym - sdx

        eta0 = math.atan2(y0p - cy, x0p - cx)
        # print(f'eta0 = Math.atan2({y0p - cy}, {x0p - cx}) = {math.degrees(eta0)}')
        eta1 = math.atan2(y1p - cy, x1p - cx)
        # print(f'eta1 = Math.atan2({y1p - cy}, {x1p - cx}) = {math.degrees(eta1)}')

        sweep = eta1 - eta0
        if isPositiveArc != (sweep >= 0):
            if sweep > 0:
                sweep -= 2 * math.pi
            else:
                sweep += 2 * math.pi
        
        cx *= a
        cy *= b
        tcx = cx
        cx = cx * cosTheta - cy * sinTheta
        cy = tcx * sinTheta + cy * cosTheta
        # print(f'cx = {cx}, cy = {cy}, a = {a}, b = {b}, x0 = {x0}, y0 = {y0}, thetaD = {math.degrees(thetaD)}, eta0 = {math.degrees(eta0)}, sweep = {math.degrees(sweep)}')
        cls.arcToBezier(p, cx, cy, a, b, x0, y0, thetaD, eta0, sweep)

    @classmethod
    def arcToBezier(cls, p: Path2D, cx: float, cy: float, a: float, b: float, e1x: float, e1y: float, theta: float, start: float, sweep: float):
        numSegments = math.ceil(abs(sweep * 4 / math.pi))
        eta1 = start
        cosTheta = math.cos(theta)
        sinTheta = math.sin(theta)

        cosEta1 = math.cos(eta1)
        sinEta1 = math.sin(eta1)

        ep1x = (-a * cosTheta * sinEta1) - (b * sinTheta * cosEta1)
        ep1y = (-a * sinTheta * sinEta1) + (b * cosTheta * cosEta1)

        anglePerSegment = sweep / numSegments
        for i in range(numSegments):
            eta2 = eta1 + anglePerSegment
            sinEta2 = math.sin(eta2)
            cosEta2 = math.cos(eta2)
            e2x = cx + (a * cosTheta * cosEta2) - (b * sinTheta * sinEta2)
            e2y = cy + (a * sinTheta * cosEta2) + (b * cosTheta * cosEta2)
            ep2x = -a * cosTheta * sinEta2 - b * sinTheta * cosEta2
            ep2y = -a * sinTheta * sinEta2 + b * cosTheta * cosEta2
            tanDiff2 = math.tan((eta2 - eta1) / 2)
            alpha = math.sin(eta2 - eta1) * (math.sqrt(4 + (3 * tanDiff2 * tanDiff2)) - 1) / 3
            q1x = e1x + alpha * ep1x
            q1y = e1y + alpha * ep1y
            q2x = e2x - alpha * ep2x
            q2y = e2y - alpha * ep2y
            p.curveTo(q1x, q1y, q2x, q2y, e2x, e2y)
            eta1 = eta2
            e1x = e2x
            e1y = e2y
            ep1x = ep2x
            ep1y = ep2y