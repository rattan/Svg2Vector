from SvgGroupNode import SvgGroupNode
from AffineTransform import AffineTransform
from SvgNode import SvgNode
from StreamWriter import StreamWriter
from SvgLeafNode import SvgLeafNode

from xml.dom import minidom
from typing import Self

import os

# Represents a SVG group element that contains a clip-path. SvgClipPathNode's mChildren will
# contain the actual path data of the clip-path. The path of the clip will be constructed in
# {@link #writeXml} by concatenating mChildren's paths. mAffectedNodes contains any group or leaf
# nodes that are clipped by the path.

class SvgClipPathNode(SvgGroupNode):
    def __init__(self, svgTree: 'SvgTree', element: minidom.Element, name: str):
        super().__init__(svgTree, element, name)
        self.mAffectedNodes = []

    def deepCopy(self) -> Self:
        newInstance = SvgClipPathNode(self.getTree(), self.mDocumentElement, self.mName)
        newInstance.copyFrom(self)
        return newInstance

    def copyFrom(self, frm: Self):
        super().copyFrom(frm)
        for node in frm.mAffectedNodes:
            self.addAffectedNode(node)

    def addChild(self, child: SvgNode):
        # Pass the presentation map down to the children, who can override the attributes.
        self.mChildren.append(child)
        # The child has its own attributes map. But the parents can still fill some attributes
        # if they don't exists
        child.fillEmptyAttributes(self.mVdAttributesMap)

    def addAffectedNode(self, child: SvgNode):
        self.mAffectedNodes.append(child)
        child.fillEmptyAttributes(self.mVdAttributesMap)

    def flatten(self, transform: AffineTransform):
        for n in self.mChildren:
            self.mStackedTransform.setTransform(transform)
            self.mStackedTransform.concatenate(self.mLocalTransform)
            n.flatten(self.mStackedTransform)

        self.mStackedTransform.setTransform(transform)
        for n in self.mAffectedNodes:
            n.flatten(self.mStackedTransform);   # mLocalTransform does not apply to mAffectedNodes.
        self.mStackedTransform.concatenate(self.mLocalTransform)
        if 'stroke-width' in self.mVdAttributesMap and ((self.mStackedTransform.getType() & AffineTransform.TYPE_MASK_SCALE) != 0):
            self.logWarning('Scaling of the stroke width is ignored')

    def validate(self):
        super().validate()
        for n in self.mChildren:
            n.validate()
        for n in self.mAffectedNodes:
            n.validate()
        if self.mDocumentElement.tagName == 'mask' and not self.isWhiteFill():
            # A mask that is not solid white creates a transparency effect that cannot be
            # reproduced by a clip-path.
            self.logError('Semitransparent mask cannot be represented by a vector drawable')

    def isWhiteFill(self) -> bool:
        fillColor = self.mVdAttributesMap.get('fill')
        if fillColor is None:
            return False

        fillColor = self.colorSvg2Vd(fillColor, '#000')
        if fillColor is None:
            return False
        return VdUtil.parseColorValue(fillColor) == 0xFFFFFFFF

    def transformIfNeeded(self, rootTransform: AffineTransform):
        for p in self.mChildren:
            p.transformIfNeeded(rootTransform)
        for p in self.mAffectedNodes:
            p.transformIfNeeded(rootTransform)
   
    def writeXml(self, writer: StreamWriter, indent: str):
        writer.write(indent)
        writer.write('<group>')
        writer.write(os.linesep)
        incrementedIndent = indent + self.INDENT_UNIT
        clipPaths = {}
        class ClipPathCollector(self.Visitor):
            def visit(self, node: SvgNode):
                if node is SvgLeafNode:
                    pathData = node.getPathData()
                    if pathData:
                        clipRule = ClipRule.EVEN_ODD if "evenOdd" == 'clip-rule' in node.mVdAttributesMap else ClipRule.NON_ZERO
                        paths = self.clipPaths.setDefault(clipRule, []);
                        paths.append(pathData)
                return SvgNode.VisitResult.CONTINUE
        clipPathCollector = ClipPathCollector()

        for node in self.mChildren:
            node.accept(clipPathCollector)
        for clipRule, pathData in clipPaths.items():
            writer.write(incrementedIndent)
            writer.write('<')
            writer.write('path')
            writer.write(os.linesep)
            writer.write(incrementedIndent)
            writer.write(self.INDENT_UNIT)
            writer.write(self.INDENT_UNIT)
            writer.write('android:pathData="')
            for i, path in enumerate(pathData):
                print(path)
                if 0 < i and not path.startsWith('M'):
                    # Reset the current position to the origin of the coordinate system.
                    writer.write('M 0,0')
                writer.write(path)
            writer.write('"')
            if clipRule == ClipRule.EVEN_ODD:
                writer.write(os.linesep)
                writer.write(incrementedIndent)
                writer.write(self.INDENT_UNIT)
                writer.write(self.INDENT_UNIT)
                writer.write('android:fillType="evenOdd"')
            writer.write('/>')
            writer.write(os.linesep)
        for node in self.mAffectedNodes:
            node.writeXml(writer, incrementedIndent)
        writer.write(indent)
        writer.write('</group>')
        writer.write(os.linesep)

    # Concatenates the affected nodes transformations to the clipPathNode's so it is properly
    # transformed.
    def setClipPathNodeAttributes(self):
        for n in self.mAffectedNodes:
            self.mLocalTransform.concatenate(n.mLocalTransform)