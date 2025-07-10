import unittest
import xml.etree.ElementTree as ET

import sys
sys.path.append('../src')
from Svg2Vector import Svg2Vector
from StreamWriter import StreamWriter

class SvgXmlCompare:
    @classmethod
    def testSvgXml(cls, name: str):
        with open(f'{name}.xml', 'r') as file:
            w = StreamWriter()
            Svg2Vector.parseSvgToXml(f'{name}.svg', w)
            # print(w.toString())
            # self.assertEqual(file.read(), w.toString())

class Svg2VectorTest(unittest.TestCase):
    def testCircle(self):
        SvgXmlCompare.testSvgXml('circle')

    def testCircle(self):
        SvgXmlCompare.testSvgXml('clipPath')

    def testDefs(self):
        SvgXmlCompare.testSvgXml('defs')

    def testEllipse(self):
        SvgXmlCompare.testSvgXml('ellipse')

    def testGroup(self):
        SvgXmlCompare.testSvgXml('group')

    def testLine(self):
        SvgXmlCompare.testSvgXml('line')

    def testLinearGradient(self):
        SvgXmlCompare.testSvgXml('linearGradient')

    def testPath(self):
        SvgXmlCompare.testSvgXml('path')

    def testPolygon(self):
        SvgXmlCompare.testSvgXml('polygon')

    def testPolyLine(self):
        SvgXmlCompare.testSvgXml('polyline')

    def testRadialGradient(self):
        SvgXmlCompare.testSvgXml('radialGradient')

    def testRect(self):
        SvgXmlCompare.testSvgXml('rect')

    def testTransform(self):
        SvgXmlCompare.testSvgXml('transform')

    def testUse(self):
        SvgXmlCompare.testSvgXml('use')

    def teatAndroid(self):
        SvgXmlCompare.testSvgXml('android')

    def testStudio(self):
        SvgXmlCompare.testSvgXml('studio')

if __name__ == '__main__':
    unittest.main()