import sys
sys.path.append('../src')
import unittest
import xml.etree.ElementTree as ET

from OutputStreamWriter import OutputStreamWriter
from Svg2Vector import Svg2Vector

class SvgXmlCompare:
    @classmethod
    def testSvgXml(cls, name: str, testCase: unittest.TestCase):
        with open(f'{name}.xml', 'r') as file:
            w = OutputStreamWriter()
            Svg2Vector.parseSvgToXml(f'{name}.svg', w)

class Svg2VectorTest(unittest.TestCase):
    def testCircle(self):
        SvgXmlCompare.testSvgXml('circle', self)

    def testCircle(self):
        SvgXmlCompare.testSvgXml('clipPath', self)

    def testDefs(self):
        SvgXmlCompare.testSvgXml('defs', self)

    def testEllipse(self):
        SvgXmlCompare.testSvgXml('ellipse', self)

    def testGroup(self):
        SvgXmlCompare.testSvgXml('group', self)

    def testLine(self):
        SvgXmlCompare.testSvgXml('line', self)

    def testLinearGradient(self):
        SvgXmlCompare.testSvgXml('linearGradient', self)

    def testPath(self):
        SvgXmlCompare.testSvgXml('path', self)

    def testPolygon(self):
        SvgXmlCompare.testSvgXml('polygon', self)

    def testPolyLine(self):
        SvgXmlCompare.testSvgXml('polyline', self)

    def testRadialGradient(self):
        SvgXmlCompare.testSvgXml('radialGradient', self)

    def testRect(self):
        SvgXmlCompare.testSvgXml('rect', self)

    def testTransform(self):
        SvgXmlCompare.testSvgXml('transform', self)

    def testUse(self):
        SvgXmlCompare.testSvgXml('use', self)

    def teatAndroid(self):
        SvgXmlCompare.testSvgXml('android', self)

    def testStudio(self):
        SvgXmlCompare.testSvgXml('studio', self)

if __name__ == '__main__':
    unittest.main()