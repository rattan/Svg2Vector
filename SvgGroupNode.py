from StreamWriter import StreamWriter
from AffineTransform import AffineTransform

from SvgNode import SvgNode
from xml.dom import minidom

# Represent a SVG file's group element
class SvgGroupNode(SvgNode):
    def __init__(self, svgTree: 'SvgTree', docNode: minidom.Element, name: str):
        super().__init__(svgTree, docNode, name)
        self.mChildren = []
        self.mUseReferenceNode = None

    def deepCopy(self):
        nreInstance = SvgGroupNode(self.getTree(), self.mDocumentElement, self.getName())
        newInstance.copyFrom(self)
        return newInstance

    def copyFrom(self, frm):
        super().copyFrom(frm)
        for child in frm.mChildren:
            self.addChild(child.deepCopy())

    # Revolve the 'href' reference to a difference group element in this 'use' group node.
    def resolveHref(self, svgTree: 'SvgTree'):
        _id = self.getHrefId()
        self.mUseReferenceNode = svgTree.getSvgNodeFromId(_id) if _id else None
        if self.mUseReferenceNode is None:
            if not _id or not svgTree.isIdIgnored(_id):
                svgTree.logError(f'Reference id not found{self.mDocumentElement}')
        else:
            # noinspection SuspiciousMethodCalls
            if self.mUseReferenceNode in svgTree.getPendingUseSet():
                # Cannot process this node, because referenceNode it depends upon
                # hasn't been processed yet.
                return False
        return True

    # Duplicate the node referenced in the 'use' group and propagate any attributes to its
    # children.
    def handleUse(self):
        if self.mUseReferenceNode is None:
            return
        copiedNode = self.mUseReferenceNode.deepCopy()
        self.addChild(copiedNode)
        for key, value in self.mVdAttributesMap.items():
            copiedNode.fillPresentationAttributes(key, value)
        self.fillEmptyAttributes(self.mVdAttributesMap)

        x = self.parseFloatOrDefault(self.mDocumentElement.getAttribute('x'), 0)
        y = self.parseFloatOrDefault(self.mDocumentElement.getAttribute('y'), 0)
        self.transformIfNeeded(AffineTransform(1, 0, 0, 1, x, y))
        

    def addChild(self, child: SvgNode):
        # Pass the presentation map down to the children, who can override the attributes.
        self.mChildren.append(child)
        # The child has its own attributes map. But the parents can still fill some attributes
        # if they don't exist
        child.fillEmptyAttributes(self.mVdAttributesMap)

    # Replace an existing child node with a new one.
    # @param oldChild the child node to replace
    # @param newChild the node to replace the existing child node with
    def replaceChild(self, oldChild: SvgNode, newChild: SvgNode):
        index = self.mChildren.index(oldChild)
        self.mChildren[index] = newChild

    def dumpNode(self, indent):
        # Print the current group.
        #print(f'{indent}current group: {self.getName()}')

        # Then print all the children
        for node in self.mChildren:
            node.dumpNode(indent + self.INDENT_UNIT)

    # Finds the parent node of the input node.
    # @return the parent node, or null if node is not in the tree.
    def findParent(self, node: SvgNode):
        for n in self.mChildren:
            if n == node:
                return self
            if n.isGroupNode():
                parent = n.findParent(node)
                if parent:
                    return parent
        return None

    def isGroupNode(self):
        return True

    def transformIfNeeded(self, rootTransform: AffineTransform):
        for p in self.mChildren:
            p.transformIfNeeded(rootTransform)

    def flatten(self, transform: AffineTransform):
        for node in self.mChildren:
            self.mStackedTransform.setTransform(transform)
            self.mStackedTransform.concatenate(self.mLocalTransform)
            node.flatten(self.mStackedTransform)

    def validate(self):
        for node in self.mChildren:
            node.validate()

    def writeXml(self, streamWriter: StreamWriter, indent: str):
        for node in self.mChildren:
            node.writeXml(streamWriter, indent)
    
    def accpet(self, visitor: SvgNode.Visitor):
        result = visitor.visit(self)
        if result == Visiresult.CONTINUE:
            for node in self.mChildren:
                if node.accpet(visitor) == self.VisitResult.ABORT:
                    return self.VisitResult.ABORT
        return self.VisitResult.CONTINUE if result == self.VisitResult.SKIP_CHILDREN else result

    def fillPresentationAttributes(self, name: str, value: str):
        super().fillPresentationAttributes(name, value)
        for n in self.mChildren:
            # Group presentation attribute should not override child.
            if name not in n.mVdAttributesMap:
                n.fillPresentationAttributes(name, value)