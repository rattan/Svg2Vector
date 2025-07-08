from StreamWriter import StreamWriter
from AffineTransform import AffineTransform
from SvgColor import SvgColor

import copy
import re
import math

from abc import *
from typing import Self
from enum import Enum
from xml.dom import minidom

# Parent class for a SVG file's node, can be either group or leave element.
class SvgNode(metaclass=ABCMeta):
    INDENT_UNIT = '  '
    CONTINUATION_INDENT = INDENT_UNIT + INDENT_UNIT
    TRANSFORM_TAG = 'transform'
    MATRIX_ATTRIBUTE = 'matrix'
    TRANSLATE_ATTRIBUTE = 'translate'
    ROTATE_ATTRIBUTE = 'rotate'
    SCALE_ATTRIBUTE = 'scale'
    SKEWX_ATTRIBUTE = 'skewX'
    SKEWY_ATTRIBUTE = 'skewY'

    presentationMap = {
        'stroke': 'android:strokeColor',
        'stroke-opacity': 'android:strokeAlpha',
        'stroke-linejoin': 'android:strokeLineJoin',
        'stroke-linecap': 'android:strokeLineCap',
        'stroke-width': 'android:strokeWidth',
        'fill': 'android:fillColor',
        'fill-opacity': 'android:fillAlpha',
        'clip': 'android:clip',
        'opacity': 'android:fillAlpha'
    }

    # While parsing the translate() rotate() ..., update the {@code mLocalTransform}.
    def __init__(self, svgTree: 'SvgTree', element, name: str):
        self.mName = name
        # Keep a reference to the tree in order to dump the error log.
        self.mSvgTree = svgTree
        # Use document node to get the line number for error reporting.
        self.mDocumentElement = element

        # Key is the attributes for vector drawable, and the value is the converted from SVG.
        self.mVdAttributesMap = dict()
        # Stroke is applied before fill as a result of "paint-order:stroke fill" style. */
        self.mStrokeBeforeFill = False
        # If mLocalTransform is identity, it is the same as not having any transformation.
        self.mLocalTransform = AffineTransform()
        # During the flatten() operation, we need to merge the transformation from top down.
        # This is the stacked transformation. And this will be used for the path data transform().
        self.mStackedTransform = AffineTransform()

        attrs = element.attributes
        for itemIndex in range(attrs.length):
            n = attrs.item(itemIndex)
            nodeName = n.nodeName
            nodeValue = n.nodeValue
            # TODO: Handle style here. Refer to Svg2Vector::addStyleToPath()
            if nodeName in self.presentationMap:
                self.fillPresentationAttributesInternal(nodeName, nodeValue)
            
            if self.TRANSFORM_TAG == nodeName:
                print(f'{nodeName} {nodeValue}')
                self.parseLocalTransform(nodeValue)

    def parseLocalTransform(self, nodeValue: str):
        # We separate the string into multiple parts and look like this:
        # "translate" "30" "rotate" "4.5e1  5e1  50"
        nodeValue = nodeValue.replace(',', ' ')
        matrices = re.split(r'[()]', nodeValue)
        for i in range(0, len(matrices) - 1, 2):
            parsedTransform = self.parseOneTransform(matrices[i].strip(), matrices[i + 1].strip())
            if parsedTransform:
                self.mLocalTransform.concatenate(parsedTransform)

    @classmethod
    def parseOneTransform(cls, _type: str, data: str):
        numbers = cls.getNumbers(data)
        if not numbers:
            return None
        print(_type, data)
        numLength = len(numbers)
        parsedTransform = AffineTransform()
        if cls.MATRIX_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 6:
                return None
            parsedTransform.setTransform(numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5])
        elif cls.TRANSLATE_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 1 and numLength != 2:
                return None
            # Default translateY is 0
            parsedTransform.translate(numbers[0], numbers[1] if numLength == 2 else 0)
        elif cls.SCALE_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 1 and numLength != 2:
                return None
            # Default scaleY == scaleX
            parsedTransform.scale(numbers[0], numbers[1 if numLength == 2 else 0])
        elif cls.ROTATE_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 1 and numLength != 3:
                return None
            parsedTransform.rotate(math.radians(numbers[0]), numbers[1] if numLength == 3 else 0, numbers[2] if numLength == 3 else 0)
        elif cls.SKEWX_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 1:
                return None
            # Note that Swing is pass the shear value directly to the matrix as m01 or m10,
            # while SVG is using tan(a) in the matrix and a is in radians.
            parsedTransform.shear(math.tan(math.radians(numbers[0])), 0)
        elif cls.SKEWY_ATTRIBUTE.casefold() == _type.casefold():
            if numLength != 1:
                return None
            parsedTransform.shear(0, math.tan(math.radians(numbers[0])))
        return parsedTransform
    
    @classmethod
    def getNumbers(cls, data: str) -> list[float]:
        numbers = re.split(r'\s+', data)
        ln = len(numbers)
        if ln == 0:
            return None
        results = [0.0] * ln
        for i in range(ln):
            results[i] = float(numbers[i])
        return results
    
    def getTree(self) -> 'SvgTree':
        return self.mSvgTree
    
    def getName(self) -> str:
        return self.mName
    
    def getDocumentElement(self) -> minidom.Element:
        return self.mDocumentElement
    
    # Dumps the current node's debug info.
    @abstractmethod
    def dumpNode(self, indent: str):
        pass
        
    # Writes content of the node into the VectorDrawable's XML file.
    # @param writer the writer to write the group XML element to
    # @param indent whitespace used for indenting output XML
    @abstractmethod
    def writeXml(self, writer: StreamWriter, indent: str):
        raise Exception()

    class VisitResult(Enum):
        CONTINUE = 1
        SKIP_CHILDREN = 2
        ABOR = 3

    class Visitor(metaclass=ABCMeta):
        # Called by the {@link SvgNode#accept(Visitor)} method for every visited node.
        # @param node the node being visited
        # @return {@link VisitResult#CONTINUE} to continue visiting children,
        #         {@link VisitResult#SKIP_CHILDREN} to skip children and continue visit with
        #         the next sibling, {@link VisitResult#ABORT} to skip all remaining nodes
        @abstractmethod
        def visit(self, node: 'SvgNode') -> 'VisitResult':
            pass

    # Calls the {@linkplain Visitor#visit(SvgNode)} method for this node and its descendants.
    # @param visitor the visitor to accept
    def accept(self, visitor: Visitor) -> 'VisitResult':
        return visitor.visit(self)
    
    # Returns true the node is a group node.
    @abstractmethod
    def isGroupNode(self):
        pass

    # Transforms the current Node with the transformation matrix.
    @abstractmethod
    def transformIfNeeded(self, finalTransform: AffineTransform):
        pass

    def fillPresentationAttributesInternal(self, name: str, value: str):
        if name == 'paint-order':
            order = re.split(r'\s+', value)
            strokePos = self.indexOf(order, 'stroke')
            fillPos = self.indexOf(order, 'fill')
            self.mStrokeBeforeFill = 0 <= strokePos and strokePos < fillPos
            return
        elif name in ['fill-rule', 'clip-rule']:
            if value == 'nonzero':
                value = 'nonZero'
            elif value == 'evenodd':
                value = 'evenOdd'
        elif name == 'stroke-width':
            if value == '0':
                del self.mVdAttributesMap['stroke']
        # print(f'>>>> PROP {name} = {value}')
        if value.startswith('url('):
            if name != 'fill' and name != 'stroke':
                print('Unsupported URL value: {value}')
                return
        if value:
            self.mVdAttributesMap[name] = value

    def indexOf(self, array: list, element) -> int:
        for i in ragne(len(array)):
            if element == array[i]:
                return i
        return -1
    
    def fillPresentationAttributes(self, name: str, value: str):
        self.fillPresentationAttributesInternal(name, value)
    
    def fillEmptyAttributes(self, parentAttributesMap: dict):
        # Go through the parents' attributes, if the child misses any, then fill it.
        for name, value in parentAttributesMap.items():
            if name not in self.mVdAttributesMap:
                self.mVdAttributesMap[name] = value

    @abstractmethod
    def flatten(self, transform: AffineTransform):
        pass

    #  Checks validity of the node and logs any issues associated with it. Subclasses may override.
    def validate(self):
        pass


    # Returns a string containing the value of the given attribute. Returns an empty string if
    # the attribute does not exist.
    def getAttributeValue(self, attribute: str) -> str:
        return self.mDocumentElement.getAttribute(attribute)
    
    @abstractmethod
    def deepCopy(self) -> Self:
        pass
    
    def copyFrom(self, frm: Self):
        self.fillEmptyAttributes(frm.mVdAttributesMap)
        self.mLocalTransform = copy.deepcopy(frm.mLocalTransform)
    
     # Converts an SVG color value to "#RRGGBB" or "#RGB" format used by vector drawables. The input
     # color value can be "none" and RGB value, e.g. "rgb(255, 0, 0)", or a color name defined in
     # https:#www.w3.org/TR/SVG11/types.html#ColorKeywords.
     # @param svgColor the SVG color value to convert
     # @param errorFallbackColor the value returned if the supplied SVG color value has invalid or
     #     unsupported format
     # @return the converted value, or None if the given value cannot be interpreted as color
    def colorSvg2Vd(self, svgColor: str, errorFallbackColor: str) -> str:
        try:
            return SvgColor.colorSvg2Vd(svgColor)
        except Exception as e:
            print(f'Unsupported color format "{svgColor}"')
            return errorFallbackColor

    # Returns the id referenced by 'href' or 'xlink.href' attribute, or an empty string if neither
    # of the two attributes is present or doesn't contain a valid reference.
    def getHrefId(self) -> str:
        value = self.mDocumentElement.getAttribute('href')
        if not value:
            value = self.mDocumentElement.getAttribute('xlink:href')
        return value[1:] if value else ''
    
    def logError(self, s: str):
        self.mSvgTree.logError(s, self.mDocumentElement)
    
    def logWarning(self, s: str):
        self.mSvgTree.logWarning(s, self.mDocumentElement)
    
    class ClipRule(Enum):
        NON_ZERO = 1
        EVEN_ODD = 2