from AffineTransform import AffineTransform
from SvgNode import SvgNode
from SvgGroupNode import SvgGroupNode
from SvgGradientNode import SvgGradientNode
from StreamWriter import StreamWriter
from VdUtil import VdUtil
from XmlUtils import XmlUtils


from xml.dom import minidom
from enum import Enum
from typing import Self

import os

#Represent the SVG file in an internal data structure as a tree
class SvgTree:
    HEAD = '<vector xmlns:android="http://schemas.android.com/apk/res/android"'
    AAPT_BOUND = 'xmlns:aapt="http://schemas.android.com/aapt"'

    SVG_WIDTH = 'width'
    SVG_HEIGHT = 'height'
    SVG_VIEW_BOX = 'viewBox'
    def __init__(self):
        self.w = -1.0
        self.h = -1.0
        self.mRootTransform = AffineTransform()
        self.viewBox = []

        self.mRoot = None
        self.mFileName = ''

        self.mLogMessages = []

        self.mHasLeafNode = False

        self.mHasGradient = False
        # Map of SvgNode's id to the SvgNode.
        self.mIdMap = dict()
        # IDs of ignored SVG nodes.
        self.mIgnoredIds = set()
        # Set of SvgGroupNodes that contain "use" elements.
        self.mPendingUseGroupSet = set()
        # Set of SvgGradientNodes that contain "href"" elements.
        self.mPendingGradientRefSet = set()

        # Key is SvgNode that references a clipPath. Value is SvgGroupNode that is the parent of that
        # SvgNode.
        self.mClipPathAffectedNodes = dict()

        # Key is String that is the id of a style class. Value is set of SvgNodes referencing that
        # class.
        self.mStyleAffectedNodes = dict()

        # Key is String that is the id of a style class. Value is a String that contains attribute
        # information of that style class.
        self.mStyleClassAttributeMap = dict()

        self.mCoordinateFormat = None

    class SvgLogLevel(Enum):
        ERROR = 1
        WARNING = 2

    class LogMessage:
        # Initializes a log message.
        # @param level the severity level
        # @param line the line number of the SVG file the message applies to,
        #     or zero if the message applies to the whole file
        # @param message the text of the message
        def __init__(self, level, line: int, message: str):
            self.level = level
            self.line = line
            self.message = message
        
        def getFormattedMessage(self) -> str:
            line = f'@ line{self.line}' if self.line else ''
            return f'{self.level.name()}{line}: {message}'

        def __lt__(self, other: Self) -> bool:
            if self.level < other.level:
                return True
            if self.level > other.level:
                return False
            if self.line < other.line:
                return True
            if self.line > other.line:
                return False
            return self.message < other.message

        def __eq__(self, other: Self) -> bool:
            return self.level == other.level and self.line == other.line and self.message == other.message

    def getWidth(self) -> float:
        return self.w

    def getHeight(self) -> float:
        return self.h

    def getScaleFactor(self) -> float:
        return 1.0

    def setHasLeafNode(self, hasLeafNode: bool):
        self.mHasLeafNode = hasLeafNode

    def setHasGradient(self, hasGradient: bool):
        self.mHasGradient = hasGradient

    def getViewBox(self) -> list[float]:
        return self.viewBox

    # From the root, top down, pass the transformation (TODO: attributes) down the children
    def flatten(self):
        self.mRoot.flatten(AffineTransform())

    # Validates all nodes and logs any encountered issue.
    def validate(self):
        self.mRoot.validate()
        if not self.mLogMessages and not self.getHasLeafNode():
            self.logError('No vector content found', None)

    def parse(self, path: str, parseErrors: list[str]) -> minidom.Document:
        self.mFileName = os.path.basename(path)
        try:
            return minidom.parse(self.mFileName)  
        except Exception as e:
            raise Exception(f'Internal error {e}')    

    def normalize(self):
        # mRootTransform is always setup, now just need to apply th viewbox info into.
        self.mRootTransform.preConcatenate(AffineTransform(1, 0, 0, 1, -self.viewBox[0], -self.viewBox[1]))
        self.transform(self.mRootTransform)
        # print(f'matrix={self.mRootTransform}')

    def transform(self, rootTransform: AffineTransform):
        self.mRoot.transformIfNeeded(rootTransform)

    def dump(self):
        # print(f'file {self.mFileName}')
        self.mRoot.dumpNode('')

    def setRoot(self, root: SvgGroupNode):
        self.mRoot = root

    def getRoot(self) -> SvgGroupNode:
        return self.mRoot

    def logError(self, s: str, node: minidom.Node):
        self.logErrorLine(s, node, self.SvgLogLevel.ERROR)

    def logWarning(self, s: str, node: minidom.Node):
        self.logErrorLine(s, node, self.SvgLogLevel.WARNING)

    def logErrorLine(self, s: str, node: minidom.Node, level: SvgLogLevel):
        # temporary print log before implments logging system.
        print(s)
        # line = self.getStartLine(node) if node else 0
        # self.mLogMessage(LogMessage(level, line, s))

    # Returns the error message that combines all logged errors and warnings. If there were no
    # errors, returns an empty string.
    def getErrorMessage(self) -> str:
        if not self.mLogMessages:
            return ''
        self.mLogMessage.sort() # Sort by severity and line number.
        result = ''
        for message in self.mLogMessages:
            if result:
                result += '\n'
            result += message.getFormattedMessage()
        return result

    # Returns true when there is at least one valid child.
    def getHasLeafNode(self) -> bool:
        return self.mHasLeafNode

    def getHasGradient(self) -> bool:
        return self.mHasGradient

    # Returns the 1-based start line number of the given node.
    @classmethod
    def getStartLine(cls, node):
        return cls.getPosition(node).getStartLine() + 1

    def getViewportWidth(self) -> float:
        return self.viewBox[2] if self.viewBox else -1.0

    def getViewportHeight(self) -> float:
        return self.viewBox[3] if self.viewBox else -1.0

    def parseDimension(self, nNode: minidom.Node):
        a = nNode.attributes
        widthType = self.SizeType.PIXEL
        heightType = self.SizeType.PIXEL
        for i in range(a.length):
            n = a.item(i)
            name = n.nodeName.strip()
            value = n.nodeValue.strip()
            subStringSize = len(value)
            currentType = self.SizeType.PIXEL
            unit = value[max(len(value) - 2, 0):]
            if unit in ['em', 'ex', 'px',' in', 'cm', 'mm', 'pt', 'pc']:
                subStringSize -= 2
            elif value.endswith('%'):
                subStringSize -= 1
                currentType = self.SizeType.PERCENTAGE

            if self.SVG_WIDTH == name:
                self.w = float(value[: subStringSize])
                widthType = currentType
            elif self.SVG_HEIGHT == name:
                self.h = float(value[0: subStringSize])
                heightType = currentType
            elif self.SVG_VIEW_BOX == name:
                self.viewBox = [0.0] * 4
                strbox = value.split(' ')
                for j in range(len(self.viewBox)):
                    self.viewBox[j] = float(strbox[j])
        # If there is no viewbox, then set it up according to w, h.
        # From now on, viewport should be read from viewBox, and size should be from w and h.
        # w and h can be set to percentage too, in this case, set it to the viewbox size.
        if not self.viewBox and 0 < self.w and 0 < self.h:
            self.viewBox = [0.0] * 4
            self.viewBox[2] = self.w
            self.viewBox[3] = self.h
        elif (self.w < 0 or self.h < 0) and self.viewBox:
            self.w = self.viewBox[2]
            self.h = self.viewBox[3]

        if widthType == self.SizeType.PERCENTAGE and self.w > 0:
            self.w = self.viewBox[2] * w / 100

        if heightType == self.SizeType.PERCENTAGE and self.h > 0:
            self.h = self.viewBox[3] * h / 100

    # Parses an X coordinate of a width value that can be an absolute number or percentage of
    # the viewport size.
    # @param value the value to parse
    # @return the parsed value
    # @throws IllegalArgumentException if the value is not a valid floating point number or
    #     percentage
    def parseXValue(self, value: str) -> float:
        return self.parseCoordinateOrLength(value, self.getViewportWidth())


    # Parses an Y coordinate of a height value that can be an absolute number or percentage of
    # the viewport size.
    # @param value the value to parse
    # @return the parsed value
    # @throws IllegalArgumentException if the value is not a valid floating point number or
    #     percentage
    def parseYValue(self, value: str) -> float:
        return self.parseCoordinateOrLength(value, self.getViewportHeight())

    @classmethod
    def parseCoordinateOrLength(cls, value: str, percentageBase: float) -> float:
        if value.endswith('%'):
            return float(value[: -1]) / 100 * percentageBase
        else:
            return float(value)

    def addIdToMap(self, _id: str, svgNode: SvgNode):
        self.mIdMap[_id] = svgNode

    def getSvgNodeFromId(self, _id: str) -> SvgNode:
        return self.mIdMap.get(_id)

    def addToPendingUseSet(self, useGroup: SvgGroupNode):
        self.mPendingUseGroupSet.add(useGroup)

    def getPendingUseSet(self) -> set[SvgGroupNode]:
        return self.mPendingUseGroupSet

    def addToPendingGradientRefSet(self, node: SvgGradientNode):
        self.mPendingGradientRefSet.add(node)

    def getPendingGradientRefSet(self) -> set[SvgGradientNode]:
        return self.mPendingGradientRefSet

    def addIgnoredId(self, _id: str):
        self.mIgnoredIds.add(_id)

    def isIdIgnored(self, _id: str):
        return _id in self.mIgnoredIds

    def addClipPathAffectedNode(self, child: SvgNode, currentGroup: SvgGroupNode, clipPathName: str):
        self.mClipPathAffectedNodes[child] = (currentGroup, clipPathName)

    def getClipPathAffectedNodesSet(self) -> dict:
        return self.mClipPathAffectedNodes

    # Adds child to set of SvgNodes that reference the style class with id className.
    def addAffectedNodeToStyleClass(self, className: str, child: SvgNode):
        if className in self.mStyleAffectedNodes:
            self.mStyleAffectedNodes[className].add(child)
        else:
            styleNodesSet = set()
            styleNodesSet.add(child)
            self.mStyleAffectedNodes[className] = styleNodesSet

    def addStyleClassToTree(self, className: str, attributes: str):
        self.mStyleClassAttributeMap[className] = attributes

    def getStyleClassAttr(self, classname: str) -> dict:
        return self.mStyleClassAttributeMap.get(classname)

    def getStyleAffectedNodes(self) -> dict:
        return self.mStyleAffectedNodes

    # Finds the parent node of the input node.
    # @return the parent node, or null if node is not in the tree.
    def findParent(sefl, node: SvgNode) -> SvgGroupNode:
        return self.mRoot.findParent(node)

    # Formats and returns the given coordinate with an appropriate precision. */
    def formatCoordinate(self, coordinate: float) -> str:
        return XmlUtils.trimInsignificantZeros(self.getCoordinateFormat().format(coordinate))

    # Returns a {@link NumberFormat] of sufficient precision to use for formatting coordinate
    # values within the viewport.
    def getCoordinateFormat(self) -> str:
        if not self.mCoordinateFormat:
            viewportWidth = self.getViewportWidth()
            viewportHeight = self.getViewportHeight()
            self.mCoordinateFormat = VdUtil.getCoordinateFormat(max(viewportHeight, viewportWidth))
        return self.mCoordinateFormat

    def writeXml(self, writer: StreamWriter):
        if not self.mRoot:
            raise ValueError('SvgTree is not fully initialized')
        writer.write(self.HEAD)
        writer.write(os.linesep)
        if self.getHasGradient():
            writer.write(SvgNode.CONTINUATION_INDENT)
            writer.write(self.AAPT_BOUND)
            writer.write(os.linesep)
        writer.write(SvgNode.CONTINUATION_INDENT)
        writer.write('android:width="')
        writer.write(self.formatCoordinate(self.getWidth() * self.getScaleFactor()))
        writer.write('dp"')
        writer.write(os.linesep)
        writer.write(SvgNode.CONTINUATION_INDENT)
        writer.write('android:height="')
        writer.write(self.formatCoordinate(self.getHeight() * self.getScaleFactor()))
        writer.write('dp"')
        writer.write(os.linesep)
        writer.write(SvgNode.CONTINUATION_INDENT)
        writer.write('android:viewportWidth="')
        writer.write(self.formatCoordinate(self.getViewportWidth()))
        writer.write('"')
        writer.write(os.linesep)
        writer.write(SvgNode.CONTINUATION_INDENT)
        writer.write('android:viewportHeight="')
        writer.write(self.formatCoordinate(self.getViewportHeight()))
        writer.write('">')
        writer.write(os.linesep)
        self.normalize()
        self.mRoot.writeXml(writer, SvgNode.INDENT_UNIT)
        writer.write('</vector>')
        writer.write(os.linesep)

    class SizeType(Enum):
        PIXEL = 1
        PERCENTAGE = 2