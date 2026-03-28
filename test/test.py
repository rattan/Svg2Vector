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
            testCase.assertMultiLineEqual(file.read(), w.toString())

class Svg2VectorTest(unittest.TestCase):
    def testCircle(self):
        SvgXmlCompare.testSvgXml('circle', self)

    def testClipPath(self):
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

    # New test cases for bug fixes (2026-03-28)

    def testStyleClass(self):
        """
        Test: Style block with CSS class parsing (Svg2Vector.py bugs 7, 8, 9)
        Bugs fixed:
        - Bug 7: wrong arg count in addAffectedNodeToStyleClass
        - Bug 8: minidom.Type → minidom.Node for CDATA detection
        - Bug 9: aClassData → sClassData, \\{ → {
        Expected: Group element with class="myclass" gets fill from <style> block
        """
        SvgXmlCompare.testSvgXml('styleClass', self)

    def testDisplayNone(self):
        """
        Test: Element with display="none" attribute is excluded (Svg2Vector.py bug 10)
        Bug fixed: displayAttr.ndoeValue → direct string comparison
        Expected: Circle in display="none" group is excluded, rect is included
        """
        SvgXmlCompare.testSvgXml('displayNone', self)

    def testInvalidColorGradient(self):
        """
        Test: Gradient with invalid color value falls back gracefully (SvgGradientNode.py bug 5)
        Bug fixed: Wrapped parseColorValue in try/except, fallback to #FF000000
        Expected: Invalid stop color becomes black (#FF000000), valid color is preserved
        """
        SvgXmlCompare.testSvgXml('invalidColorGradient', self)

    def testVisitorPattern(self):
        """
        Test: Nested groups are traversed correctly by Visitor (SvgGroupNode.py bug 1)
        Bug fixed: accpet → accept, Visiresult → self.VisitResult
        Expected: All children in nested groups are converted (4 paths total, 2 red + 2 green)
        """
        SvgXmlCompare.testSvgXml('visitorPattern', self)

    def testGradientMultiStop(self):
        """
        Test: Gradient with multiple color stops is correctly rendered
        Related bugs fixed:
        - Svg2Vector.py bug 6: resoveHref → resolveHref
        - SvgGradientNode.py bug 4: .contains() → in operator
        Expected: Circle filled with linear gradient with 3 stops (red, green, blue)
        """
        SvgXmlCompare.testSvgXml('gradientHref', self)

    # Additional coverage tests for uncovered code paths

    def testStrokeAttributes(self):
        """
        Test: stroke-linecap and stroke-linejoin attributes
        Coverage: SvgNode.presentationMap mapping, SvgLeafNode.writeAttributeValues
        Expected: VectorDrawable output includes android:strokeLineCap="round"
                  and android:strokeLineJoin="bevel"
        """
        SvgXmlCompare.testSvgXml('strokeAttributes', self)

    def testFillRule(self):
        """
        Test: fill-rule: evenodd attribute mapping
        Coverage: SvgNode.fillPresentationAttributesInternal fill-rule conversion
        Expected: android:fillType="evenOdd" appears in output
        """
        SvgXmlCompare.testSvgXml('fillRule', self)

    def testOpacity(self):
        """
        Test: opacity, fill-opacity, and stroke-opacity combination
        Coverage: SvgLeafNode.parsePathOpacity, getOpacityValueFromMap, putOpacityValueToMap
        Expected: opacity * fill-opacity combined into android:fillAlpha
                  opacity * stroke-opacity combined into android:strokeAlpha
        """
        SvgXmlCompare.testSvgXml('opacity', self)

    def testMatrixTransform(self):
        """
        Test: matrix(a b c d e f) transform
        Coverage: SvgNode.parseOneTransform matrix branch
        Expected: Rect coordinates transformed correctly (equiv to translate(50,75))
        """
        SvgXmlCompare.testSvgXml('matrixTransform', self)

    def testRoundedRect(self):
        """
        Test: Rounded rect with rx attribute (rx only, ry fallback to rx)
        Coverage: Svg2Vector.extractRectItem rx/ry branch with arc generation
        Expected: Path data contains A (arc) commands for rounded corners
        """
        SvgXmlCompare.testSvgXml('roundedRect', self)

    def testGradientUserSpace(self):
        """
        Test: linearGradient with gradientUnits="userSpaceOnUse"
        Coverage: SvgGradientNode.writeXml userSpaceOnUse branch
        Expected: Gradient coordinates use viewport dimensions (200,200)
                  not bounding box dimensions (160,160)
        """
        SvgXmlCompare.testSvgXml('gradientUserSpace', self)

    def testStrokeGradient(self):
        """
        Test: Gradient applied to stroke (not fill)
        Coverage: SvgGradientNode.writeXml STROKE branch
        Expected: <aapt:attr name="android:strokeColor"> (not fillColor)
        """
        SvgXmlCompare.testSvgXml('strokeGradient', self)

    def testRelativePath(self):
        """
        Test: Path with relative commands (c, s) directly in d attribute
        Coverage: VdPath.Node.transformImpl relative bezier branches
        Expected: c and s commands correctly handled in path data output
        """
        SvgXmlCompare.testSvgXml('relativePath', self)

if __name__ == '__main__':
    unittest.main()