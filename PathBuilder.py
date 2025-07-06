
from XmlUtils import XmlUtils

# Build a string for Svg file's path data.
class PathBuilder:
    def __init__(self):
        self.mPathData = ''

    def encodeBoolean(self, flag):
        return '1' if flag else '0'

    def absoluteMoveTo(self, x, y):
        self.mPathData += f'M{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeMoveTo(self, x, y):
        self.mPathData += f'm{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteLineTo(self, x, y):
        self.mPathData += f'L{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeLineTo(self, x, y):
        self.mPathData += f'l{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteVerticalTo(self, v):
        self.mPathData += f'V{XmlUtils.formatFloatValue(v)}'
        return self

    def relativeVerticalTo(self, v):
        self.mPathData += f'v{XmlUtils.formatFloatValue(v)}'
        return self

    def absoluteHorizontalTo(self, h):
        self.mPathData += f'H{XmlUtils.formatFloatValue(h)}'
        return self

    def relativeHorizontalTo(self, h):
        self.mPathData += f'h{XmlUtils.formatFloatValue(h)}'
        return self

    def absoluteCurveTo(self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float):
        self.mPathData += f'C{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeCurveTo(self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float):
        self.mPathData += f'c{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteSmoothCurveTo(self, cp2x: float, cp2y: float, x: float, y: float):
        self.mPathData += f'S{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeSmoothCurveTo(self, cp2x: float, cp2y: float, x: float, y: float):
        self.mPathData += f's{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteQuadraticCurveTo(self, cp1x: float, cp1y: float, x: float, y: float):
        self.mPathData += f'Q{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeQuadraticCurveTo(self, cp1x: float, cp1y: float, x: float, y: float):
        self.mPathData += f'q{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteSmoothQuadraticCurveTo(x: float, y: float):
        self.mPathData += f'T{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeSmoothQuadraticCurveTo(x: float, y: float):
        self.mPathData += f't{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteArcTo(self, rx, ry, rotation, largeArc, sweep, x, y):
        self.mPathData += f'A{XmlUtils.formatFloatValue(rx)},{XmlUtils.formatFloatValue(ry)},{self.encodeBoolean(rotation)},{self.encodeBoolean(largeArc)},{self.encodeBoolean(sweep)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeArcTo(self, rx, ry, rotation, largeArc, sweep, x, y):
        self.mPathData += f'a{XmlUtils.formatFloatValue(rx)},{XmlUtils.formatFloatValue(ry)},{self.encodeBoolean(rotation)},{self.bencodeBooleanooleanToString(largeArc)},{self.encodeBoolean(sweep)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteClose(self):
        self.mPathData += 'Z'
        return self

    def relativeClose(self):
        self.mPathData += 'z'
        return self

    def toString(self):
        return self.mPathData