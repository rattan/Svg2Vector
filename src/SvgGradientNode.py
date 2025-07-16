from enum import Enum
import logging
import os
from typing import Self
from xml.dom import minidom

from AffineTransform import AffineTransform
from GradientStop import GradientStop
from OutputStreamWriter import OutputStreamWriter
from Path2D import Path2DF
from PathParser import PathParser
from Point2D import Point2DF
from SvgNode import SvgNode
from XmlUtils import XmlUtils
from VdNodeRender import VdNodeRender
from VdPath import VdPath
from VdUtil import VdUtil


# Represents an SVG gradient that is referenced by a SvgLeafNode.
class SvgGradientNode(SvgNode):
    logger = logging.getLogger('Svg2Vector')
    # Maps the gradient vector's coordinate names to an int for easier array lookup.
    vectorCoordinateMap = {
        'x1': 0,
        'y1': 1,
        'x2': 2,
        'y2': 3,
    }
    gradientMap = {
        'x1': 'android:startX',
        'y1': 'android:startY',
        'x2': 'android:endX',
        'y2': 'android:endY',
        'cx': 'android:centerX',
        'cy': 'android:centerY',
        'r': 'android:gradientRadius',
        'spreadMethod': 'android:tileMode',
        'gradientUnits': '',
        'gradientTransform': '',
        'gradientType': 'android:type',
    }

    def __init__(self, svgTree: 'SvgTree', element: minidom.Element, nodeName: str):
        super().__init__(svgTree, element, nodeName)
        self.mGradientStops = []
        self.mSvgLeafNode = None
        # Bounding box of mSvgLeafNode.
        self.mBoundingBox = None
        self.mGradientUsage = None


    def deepCopy(self) -> Self:
        newInstance = SvgGradientNode(self.getTree(), self.mDocumentElement, self.getName())
        newInstance.copyFrom(self)
        return newInstance

    def isGroupNode(self) -> bool:
        return False

    # We do not copy mSvgLeafNode, boundingBox, or mGradientUsage because they will be set after
    # copying the SvgGradientNode. We always call deepCopy of SvgGradientNodes within a SvgLeafNode
    # and then call setSvgLeafNode for that leaf. We calculate the boundingBox and determine the
    # mGradientUsage based on the leaf node's attributes and reference to the gradient being
    # copied.
    def copyFrom(self, frm: Self):
        super().copyFrom(frm)
        if not self.mGradientStops:
            for g in frm.mGradientStops:
                self.addGradientStop(g.getColor(), g.getOffset(), g.getOpacity())

    # Resolves the 'href' reference to a template gradient element.
    # @return True if the reference has been resolved, or False if it cannot be resolved at this
    #     time due to a dependency on an unresolved node
    def resolveHref(self, svgTree: 'SvgTree') -> bool:
        _id = self.getHrefId()
        referencedNode = svgTree.getSvgNodeFromId(_id) if _id else None 
        if isinstance(referencedNode, SvgGradientNode):
            #noinspection SuspiciousMethodCalls
            if (svgTree.getPendingUseSet().contains(referencedNode)):
                # Cannot process this node, because referencedNode it depends upon
                # hasn't been processed yet.
                return False
            
            self.copyFrom(referencedNode)
        elif referencedNode is None:
            if not _id or not svgTree.isIdIgnored(_id):
                svgTree.logError('Referenced id not found', mDocumentElement)
        else:
            svgTree.logError('Referenced element is not a gradient', mDocumentElement)
        return True
    
    def dumpNode(self, indent: str):
        # Print the current node.
        self.logger.info(f'{indent} current gradient is :{self.getName()}')
        pass
    
    def transformIfNeeded(self, rootTransform: AffineTransform):
        # Transformation is done in the writeXml method.
        pass
    
    def flatten(self, transform: AffineTransform):
        self.mStackedTransform.setTransform(transform)
        self.mStackedTransform.concatenate(self.mLocalTransform)
    
    class GradientCoordResult:
        # When the gradientUnits is set to "userSpaceOnUse", we usually use the coordinate values
        # as it is. But if the coordinate value is a percentage, we still need to multiply this
        # percentage with the viewport's bounding box, in a similar way as gradientUnits is set
        # to "objectBoundingBox".
        def __init__(self, value: float, isPercentage: bool):
            self.mValue = value
            self.mIsPercentage = isPercentage
        
        def getValue(self) -> float:
            return self.mValue
        
        def isPercentage(self) -> float:
            return self.mIsPercentage

    #Parses the gradient coordinate value given as a percentage or a length. Returns a double.
    def getGradientCoordinate(self, x: str, defaultValue: float) -> GradientCoordResult:
        if x not in self.mVdAttributesMap:
            return self.GradientCoordResult(defaultValue, False)
        
        val = defaultValue
        vdValue = self.mVdAttributesMap[x].strip()
        if x == 'r' and vdValue.startswith('-'):
            return self.GradientCoordResult(defaultValue, False)
        isPercentage = False
        try:
            if vdValue.endswith('%'):
                val = float(vdValue[0: -1]) / 100
                isPercentage = True
            else:
                val = float(vdValue)

        except Exception as e:
            self.logError('Unsupported coordinate value')
            pass
        return self.GradientCoordResult(val, isPercentage)

    def writeXml(self, writer: OutputStreamWriter, indent: str):
        if not self.mGradientStops:
            self.logError("Gradient has no stop info")
            return

        # By default, the dimensions of the gradient is the bounding box of the path.
        self.setBoundingBox()
        height = self.mBoundingBox.getHeight()
        width = self.mBoundingBox.getWidth()
        startX = self.mBoundingBox.getX()
        startY = self.mBoundingBox.getY()
        gradientUnit = self.mVdAttributesMap.get('gradientUnits')
        isUserSpaceOnUse = 'userSpaceOnUse' == gradientUnit
        # If gradientUnits is specified to be "userSpaceOnUse", we use the image's dimensions.
        if isUserSpaceOnUse:
            startX = 0
            startY = 0
            height = self.getTree().getHeight()
            width = self.getTree().getWidth()
        
        if width == 0 or height == 0:
            return  # The gradient is not visible because it doesn't occupy any area.
        
        writer.write(indent)
        if self.mGradientUsage == self.GradientUsage.FILL:
            writer.write('<aapt:attr name="android:fillColor">')
        else:
            writer.write('<aapt:attr name="android:strokeColor">')
        
        writer.write(os.linesep)
        writer.write(indent)
        writer.write(self.INDENT_UNIT)
        writer.write('<gradient ')
        # TODO: Fix matrix transformations that include skew element and SVGs that define scale before rotate.
        # Additionally skew transformations have not been tested.
        # If there is a gradientTransform, parse and store in mLocalTransform.
        if 'gradientTransform' in self.mVdAttributesMap:
            transformValue = self.mVdAttributesMap['gradientTransform']
            self.parseLocalTransform(transformValue)
            if not isUserSpaceOnUse:
                tr = AffineTransform(width, 0, 0, height, 0, 0)
                self.mLocalTransform.preConcatenate(tr)
                try:
                    tr.invert()
                except Exception as e:
                    raise Exception(e); # Not going to happen because width * height != 0
                
                self.mLocalTransform.concatenate(tr)
        
        # According to the SVG spec, the gradient transformation (mLocalTransform) always needs
        # to be applied to the gradient. However, the geometry transformation (mStackedTransform)
        # will be affecting gradient only when it is using user space because we flatten
        # everything.
        # If we are not using user space, at this moment, the bounding box already contains
        # the geometry transformation, when we apply percentage to the bounding box, we don't
        # need to multiply the geometry transformation the second time.
        if isUserSpaceOnUse:
            self.mLocalTransform.preConcatenate(self.mSvgLeafNode.mStackedTransform)
        
        # Source and target arrays to which we apply the local transform.
        gradientBounds = []
        transformedBounds = []
        gradientType = 'linear'
        if 'gradientType' in self.mVdAttributesMap:
            gradientType = self.mVdAttributesMap['gradientType']
        if gradientType == 'linear':
            gradientBounds = [0.0] * 4
            transformedBounds = [0.0] * 4
            # Retrieves x1, y1, x2, y2 and calculates their coordinate in the viewport.
            # Stores the coordinates in the gradientBounds and transformedBounds arrays to apply
            # the proper transformation.
            for s, index in self.vectorCoordinateMap.items():
                # Get the index corresponding to x1, y1, x2 and y2.
                # x1 and x2 are indexed as 0 and 2
                # y1 and y2 are indexed as 1 and 3
                # According to SVG spec, the default coordinate value for x1, and y1 and y2 is 0.
                # The default for x2 is 1.
                defaultValue = 0.0
                if index == 2:
                    defaultValue = 1.0
                result = self.getGradientCoordinate(s, defaultValue)
                coordValue = result.getValue()
                if not isUserSpaceOnUse or result.isPercentage():
                    if index % 2 == 0:
                        coordValue = coordValue * width + startX
                    else:
                        coordValue = coordValue * height + startY
                # In case no transforms are applied, original coordinates are also stored in
                # transformedBounds.
                gradientBounds[index] = coordValue
                transformedBounds[index] = coordValue
                # We need mVdAttributesMap to contain all coordinates regardless if they are
                # specified in the SVG in order to write the default value to the VD XML.
                if s not in self.mVdAttributesMap:
                    self.mVdAttributesMap[s] = ''
            # transformedBounds will hold the new coordinates of the gradient.
            # This applies it to the linearGradient
            self.mLocalTransform.transform(gradientBounds, 0, transformedBounds, 0, 2)
        else:
            gradientBounds = [0.0] * 2
            transformedBounds = [0.0] * 2
            cxResult = self.getGradientCoordinate('cx', 0.5)
            cx = cxResult.getValue()
            if not isUserSpaceOnUse or cxResult.isPercentage():
                cx = width * cx + startX
            
            cyResult = self.getGradientCoordinate('cy', 0.5)
            cy = cyResult.getValue()
            if not isUserSpaceOnUse or cyResult.isPercentage():
                cy = height * cy + startY
            
            rResult = self.getGradientCoordinate('r', 0.5)
            r = rResult.getValue()
            if not isUserSpaceOnUse or rResult.isPercentage():
                r *= max(height, width)
            
            gradientBounds[0] = cx
            transformedBounds[0] = cx
            gradientBounds[1] = cy
            transformedBounds[1] = cy
            # Transform radius, center point here.
            self.mLocalTransform.transform(gradientBounds, 0, transformedBounds, 0, 1)
            radius = Point2DF(r, 0)
            transformedRadius = Point2DF(r, 0)
            self.mLocalTransform.deltaTransform(radius, transformedRadius)
            self.mVdAttributesMap['cx'] = self.mSvgTree.formatCoordinate(transformedBounds[0])
            self.mVdAttributesMap['cy'] = self.mSvgTree.formatCoordinate(transformedBounds[1])
            self.mVdAttributesMap['r'] = self.mSvgTree.formatCoordinate(transformedRadius.distance(0, 0))
        
        for svgAttribute, gradientAttr in self.gradientMap.items():
            svgValue = self.mVdAttributesMap.get(svgAttribute)
            if svgValue is None or not gradientAttr:
                continue
            svgValue = svgValue.strip()
            vdValue = self.colorSvg2Vd(svgValue, '#000000')
            if not vdValue:
                coordinateIndex = self.vectorCoordinateMap.get(svgAttribute)
                if coordinateIndex is not None:
                    x = transformedBounds[coordinateIndex]
                    vdValue = self.mSvgTree.formatCoordinate(self.mSvgTree.roundHalfUp(x))
                elif svgAttribute == 'spreadMethod':
                    if svgValue == 'pad':
                        vdValue = 'clamp'
                    elif svgValue == 'reflect':
                        vdValue = 'mirror'
                    elif svgValue == 'repeat':
                        vdValue = 'repeat'
                    else:
                        self.logError(f'Unsupported spreadMethod {svgValue}')
                        vdValue = 'clamp'
                    
                elif svgValue.endswith("%"):
                    coordinate = self.getGradientCoordinate(svgAttribute, 0).getValue()
                    vdValue = self.mSvgTree.formatCoordinate(coordinate)
                else:
                    vdValue = svgValue
            
            writer.write(os.linesep)
            writer.write(indent)
            writer.write(self.INDENT_UNIT)
            writer.write(self.CONTINUATION_INDENT)
            writer.write(gradientAttr)
            writer.write('="')
            writer.write(vdValue)
            writer.write('"')
        
        writer.write('>')
        writer.write(os.linesep)
        self.writeGradientStops(writer, indent + self.INDENT_UNIT + self.INDENT_UNIT)
        writer.write(indent)
        writer.write(self.INDENT_UNIT)
        writer.write('</gradient>')
        writer.write(os.linesep)
        writer.write(indent)
        writer.write('</aapt:attr>')
        writer.write(os.linesep)
    
    def writeGradientStops(self, writer: OutputStreamWriter, indent: str):
        for g in self.mGradientStops:
            color = g.getColor()
            opacity = 1.0
            try:
                opacity = float(g.getOpacity())
            except Exception as e:
                self.logWarning('Unsupported opacity value')
                opacity = 1.0
            
            color1 = VdPath.applyAlpha(VdUtil.parseColorValue(color), opacity)
            color = '#%08X' % color1
            writer.write(indent)
            writer.write('<item android:offset="')
            writer.write(XmlUtils.trimInsignificantZeros(g.getOffset()))
            writer.write('"')
            writer.write(' android:color="')
            writer.write(color)
            writer.write('"/>')
            writer.write(os.linesep)
            if len(self.mGradientStops) == 1:
                self.logWarning('Gradient has only one color stop')
                writer.write(indent)
                writer.write('<item android:offset="1"')
                writer.write(' android:color="')
                writer.write(color)
                writer.write('"/>')
                writer.write(os.linesep)
    
    def addGradientStop(self, color: str, offset: str, opacity: str):
        stop = GradientStop(color, offset)
        stop.setOpacity(opacity)
        self.mGradientStops.append(stop)
    
    class GradientUsage(Enum):
        FILL = 1
        STROKE = 2

    def setGradientUsage(self, gradientUsage: GradientUsage):
        self.mGradientUsage = gradientUsage
    
    def setSvgLeafNode(self, svgLeafNode: 'SvgLeafNode'):
        self.mSvgLeafNode = svgLeafNode
    
    def setBoundingBox(self):
        svgPath = Path2DF()
        nodes = PathParser.parsePath(self.mSvgLeafNode.getPathData(), PathParser.ParseMode.SVG)
        VdNodeRender.createPath(nodes, svgPath)
        self.mBoundingBox = svgPath.getBounds2D()