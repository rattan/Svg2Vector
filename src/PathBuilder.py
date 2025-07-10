
from XmlUtils import XmlUtils
from typing import Self

# Build a string for Svg file's path data.
class PathBuilder:
    def __init__(self):
        self.mPathData = ''

    def encodeBoolean(self, flag) -> str:
        return '1' if flag else '0'

    def absoluteMoveTo(self, x: float, y: float) -> Self:
        self.mPathData += f'M{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeMoveTo(self, x: float, y: float) -> Self:
        self.mPathData += f'm{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteLineTo(self, x: float, y: float) -> Self:
        self.mPathData += f'L{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeLineTo(self, x: float, y: float) -> Self:
        self.mPathData += f'l{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteVerticalTo(self, v: float) -> Self:
        self.mPathData += f'V{XmlUtils.formatFloatValue(v)}'
        return self

    def relativeVerticalTo(self, v: float) -> Self:
        self.mPathData += f'v{XmlUtils.formatFloatValue(v)}'
        return self

    def absoluteHorizontalTo(self, h: float) -> Self:
        self.mPathData += f'H{XmlUtils.formatFloatValue(h)}'
        return self

    def relativeHorizontalTo(self, h: float) -> Self:
        self.mPathData += f'h{XmlUtils.formatFloatValue(h)}'
        return self

    def absoluteCurveTo(self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float) -> Self:
        self.mPathData += f'C{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeCurveTo(self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float) -> Self:
        self.mPathData += f'c{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteSmoothCurveTo(self, cp2x: float, cp2y: float, x: float, y: float) -> Self:
        self.mPathData += f'S{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeSmoothCurveTo(self, cp2x: float, cp2y: float, x: float, y: float) -> Self:
        self.mPathData += f's{XmlUtils.formatFloatValue(cp2x)},{XmlUtils.formatFloatValue(cp2y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteQuadraticCurveTo(self, cp1x: float, cp1y: float, x: float, y: float) -> Self:
        self.mPathData += f'Q{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeQuadraticCurveTo(self, cp1x: float, cp1y: float, x: float, y: float) -> Self:
        self.mPathData += f'q{XmlUtils.formatFloatValue(cp1x)},{XmlUtils.formatFloatValue(cp1y)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteSmoothQuadraticCurveTo(x: float, y: float) -> Self:
        self.mPathData += f'T{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeSmoothQuadraticCurveTo(x: float, y: float) -> Self:
        self.mPathData += f't{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteArcTo(self, rx, ry, rotation, largeArc, sweep, x, y) -> Self:
        self.mPathData += f'A{XmlUtils.formatFloatValue(rx)},{XmlUtils.formatFloatValue(ry)},{self.encodeBoolean(rotation)},{self.encodeBoolean(largeArc)},{self.encodeBoolean(sweep)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def relativeArcTo(self, rx, ry, rotation, largeArc, sweep, x, y) -> Self:
        self.mPathData += f'a{XmlUtils.formatFloatValue(rx)},{XmlUtils.formatFloatValue(ry)},{self.encodeBoolean(rotation)},{self.encodeBoolean(largeArc)},{self.encodeBoolean(sweep)},{XmlUtils.formatFloatValue(x)},{XmlUtils.formatFloatValue(y)}'
        return self

    def absoluteClose(self) -> Self:
        self.mPathData += 'Z'
        return self

    def relativeClose(self) -> Self:
        self.mPathData += 'z'
        return self

    def toString(self) -> Self:
        return self.mPathData