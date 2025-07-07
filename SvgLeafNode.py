from SvgNode import SvgNode
from VdPath import VdPath
from StreamWriter import StreamWriter
from AffineTransform import AffineTransform
from PathParser import PathParser
from XmlUtils import XmlUtils

from typing import Self

import os
import math

# Represent a SVG file's leave element
class SvgLeafNode(SvgNode):
    def __init__(self, svgTree, node, nodeName):
        super().__init__(svgTree, node, nodeName)
        self.mPathData = None
        self.mFillGradientNode = None
        self.mStrokeGradientNode = None

        # Key is the attributes for vector drawable, and the value is the converted from SVG.
    
    def deepCopy(self) -> Self:
        newNode = SvgLeafNode(self.getTree(), self.mDocumentElement, self.getName())
        newNode.copyFrom(self)
        return newNode

    def copyFrom(self, frm: Self):
        super().copyFrom(frm)
        self.mPathData = frm.mPathData
        
    # Writes attributes of this node
    def writeAttributeValues(self, writer: StreamWriter, indent: str):
        # There could be some redundent opacity information in the attribute's map,
        # like opacity vs fill-opacity / stroke-opacity.
        self.parsePathOpacity()

        for name, svgValue in self.mVdAttributesMap.items():
            attribute = self.presentationMap.get(name)
            if not attribute:
                continue
            svgValue = svgValue.strip()
            vdValue = self.colorSvg2Vd(svgValue, '#000000')

            if vdValue is None:
                if name == ['fill', 'stroke']:
                    gradientNode = self.getGradientNode(svgValue)
                    if gradientNode:
                        gradientNode = gradientNode.deepCopy()
                        gradientNode.setSvgLeafNode(self)
                        if name == 'fill':
                            gradientNode.setGradientUsage(SvgGradientNode.GradientUsage.FILL)
                            self.mFillGradientNode = gradientNode
                        else:
                            gradientNode.setGradientUsage(SvgGradientNode.GradientUsage.STROKE)
                            self.mStrokeGradientNode = gradientNode
                        continue
                if svgValue.endswith('px'):
                    vdValue = svgValue[-2].strip()
                else:
                    vdValue = svgValue
            writer.write(os.linesep)
            writer.write(indent)
            writer.write(self.CONTINUATION_INDENT)
            writer.write(attribute)
            writer.write('="')
            writer.write(vdValue)
            writer.write('"')

    def getGradientNode(self, svgValue: str) -> 'SvgGradientNode':
        if svgValue.startswith('url(#') and svgVlaue.endswith(')'):
            _id = svgValue[5: -1]
            node = self.getTree().getSvgNodeFromId(_id)
            if node is SvgGradientNode:
                return node
        return None

    # Parse the SVG path's opacity attribute into fill and stroke.
    def parsePathOpacity(self):
        opacity = self.getOpacityValueFromMap('opacity')
        fillOpacity = self.getOpacityValueFromMap('fill-opacity')
        strokeOpacity = self.getOpacityValueFromMap('stroke-opacity')
        self.putOpacityValueToMap('fill-opacity', fillOpacity * opacity)
        self.putOpacityValueToMap('stroke-opacity', strokeOpacity * opacity)
        self.mVdAttributesMap.pop('opacity', None)

    # A utility funtion to get the opacity value as a floating point number.
    # @param attributeName the name of the opacity attribute
    # @return the clamped opacity value, or 1 if not found
    def getOpacityValueFromMap(self, attributeName: str) -> float:
        # Default opacity is 1.
        result = 1
        opacity = self.mVdAttributesMap.get(attributeName)
        if opacity:
            try:
                if opacity.endswith('%'):
                    result = float(opacity[:-1]) / 100
                else:
                    result = float(opacity)
            except Exception as e:
                # Ignore here, an invalid value is replaced by the default value 1.
                pass
        return min(max(result, 0), 1)
    
    def putOpacityValueToMap(self, attributeName: str, opacity: float):
        attributeValue = XmlUtils.formatFloatValue(opacity)
        if attributeValue == '1':
            self.mVdAttributesMap.pop(attributeName, None)
        else:
            self.mVdAttributesMap[attributeName] = attributeValue
    
    def dumpNode(self, indent: str):
        #print(f'indent{' null pathData' if self.mPathData is None else self.mPathData}{' null name' if self.mName is None else self.mName}')
        pass

    def setPathData(self, pathData: str):
        self.mPathData = pathData

    def isGroupNode(self) -> bool:
        return False

    def hasGradient(self) -> bool:
        return self.mFillGradientNode or self.mStrokeGradientNode

    def transformIfNeeded(self, rootTransform: AffineTransform):
        if not self.mPathData:
            # Nothing to draw and transform, early return.
            return
        nodes = PathParser.parsePath(self.mPathData, PathParser.ParseMode.SVG)
        self.mStackedTransform.preConcatenate(rootTransform)
        needsConvertRelativeModeAfterClose = VdPath.Node.hasRelMoveAfterClose(nodes)
        if not self.mStackedTransform.isIdentity() or needsConvertRelativeModeAfterClose:
            VdPath.Node.transform(self.mStackedTransform, nodes)
        self.mPathData = VdPath.Node.NodeListToString(nodes, self.mSvgTree)

    def flatten(self, transform: AffineTransform):
        self.mStackedTransform.setTransform(transform)
        self.mStackedTransform.concatenate(self.mLocalTransform)

        if 'non-scaling-stroke' != self.mVdAttributesMap.get('vector-effect') and (self.mStackedTransform.getType() & AffineTransform.TYPE_MASK_SCALE) != 0:
            strokeWidth = self.mVdAttributesMap.get('stroke-width')
            if strokeWidth:
                try:
                    # Unlike SVG, vector drawable is not capable of applying transformations
                    # to stroke outline. To compensate for that we apply scaling transformation
                    # to the stroke width, which produces accurate results for uniform and
                    # approximate results for nonuniform scaling transformation.
                    width = float(strokeWidth)
                    determinant = self.mStackedTransform.getDeterminant()
                    if determinant != 0:
                        width *= math.sqrt(math.abs(determinant))
                        self.mVdAttributesMap['stroke-width'] = self.mSvgTree.formatCoordinate(width)
                    if (self.mStackedTransform.getType() & AffineTransform.TYPE_GENERAL_SCALE) != 0:
                        # print('Scaling of the stroke width is approximate')
                        pass
                except Exception as e:
                    pass

    def writeXml(self, writer: StreamWriter, indent: str):
        if not self.mPathData:
            return  # No path to draw
        
        if self.mStrokeBeforeFill:
            # To render fill on top of stroke output the <path> element twice,
            # first without fill, and then without stroke.
            self.writePathElementWithSuppressedFillOrStroke(writer, 'fill', indent)
            self.writePathElementWithSuppressedFillOrStroke(writer, 'stroke', indent)
        else:
            self.writePathElement(writer, indent);
        
    def writePathElementWithSuppressedFillOrStroke(self, writer: StreamWriter, attribute: str, indent: str):
        savedValue = self.mVdAttributesMap.get(attribute)
        self.mVdAttributesMap[attribute] = '#00000000'
        self.writePathElement(writer, indent)
        if not savedValue:
            self.mVdAttributesMap.pop(attribute, None)
        else:
            self.mVdAttributesMap[attribute] = savedValue


    def writePathElement(self, writer: StreamWriter, indent: str):
        fillColor = self.mVdAttributesMap.get('fill')
        strokeColor = self.mVdAttributesMap.get('stroke')
        emptyFill = 'none' == fillColor or '#00000000' == fillColor
        emptyStroke = not strokeColor or 'none' == strokeColor
        if emptyFill and emptyStroke:
            return  # Nothing to draw.
        writer.write(indent)
        writer.write('<path')
        writer.write(os.linesep)
        if not fillColor and not mFillGradientNode:
            # print('Adding default fill color')
            writer.write(indent)
            writer.write(self.CONTINUATION_INDENT)
            writer.write('android:fillColor="#FF000000"')
            writer.write(os.linesep)
        if not emptyStroke and 'stroke-width' not in self.mVdAttributesMap and not self.mStrokeGradientNode:
            # print('Adding default stroke width')
            writer.write(indent)
            writer.write(self.CONTINUATION_INDENT)
            writer.write('android:strokeWidth="1"')
            writer.write(os.linesep)
        # Last, write the path data and all associated attributes.
        writer.write(indent)
        writer.write(self.CONTINUATION_INDENT)
        writer.write(f'android:pathData="{self.mPathData}"')
        self.writeAttributeValues(writer, indent)
        if not self.hasGradient():
            writer.write('/')
        writer.write('>')
        writer.write(os.linesep)
        if self.mFillGradientNode:
            self.mFillGradientNode.writeXml(writer, indent + self.INDENT_UNIT)

        if self.mStrokeGradientNode:
            self.mStrokeGradientNode.writeXml(writer, indent + self.INDENT_UNIT)
        if self.hasGradient():
            writer.write(indent)
            writer.write('</path>')
            writer.write(os.linesep)