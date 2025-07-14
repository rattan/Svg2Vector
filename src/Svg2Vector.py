"""
Copyright 2025 Svg2Vector. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from collections import deque
import logging
import re
from xml.dom import minidom

from OutputStreamWriter import OutputStreamWriter
from PathBuilder import PathBuilder
from SvgClipPathNode import SvgClipPathNode
from SvgGradientNode import SvgGradientNode
from SvgGroupNode import SvgGroupNode
from SvgLeafNode import SvgLeafNode
from SvgNode import SvgNode
from SvgTree import SvgTree

# Converts SVG to VectorDrawable's XML
class Svg2Vector:
    SVG_DEFS = 'defs'
    SVG_USE = 'use'
    SVG_HREF = 'href'
    SVG_XLINK_HREF = 'xlink:href'
    SVG_POLYGON = 'polygon'
    SVG_POLYLINE = 'polyline'
    SVG_RECT = 'rect'
    SVG_CIRCLE = 'circle'
    SVG_LINE = 'line'
    SVG_PATH = 'path'
    SVG_ELLIPSE = 'ellipse'
    SVG_GROUP = 'g'
    SVG_STYLE = 'style'
    SVG_DISPLAY = 'display'
    SVG_CLIP_PATH_ELEMENT = 'clipPath'
    SVG_D = 'd'
    SVG_CLIP = 'clip'
    SVG_CLIP_PATH = 'clip-path'
    SVG_CLIP_RULE = 'clip-rule'
    SVG_FILL = 'fill'
    SVG_FILL_OPACITY = 'fill-opacity'
    SVG_FILL_RULE = 'fill-rule'
    SVG_OPACITY = 'opacity'
    SVG_PAINT_ORDER = 'paint-order'
    SVG_STROKE = 'stroke'
    SVG_STROKE_LINECAP = 'stroke-linecap'
    SVG_STROKE_LINEJOIN = 'stroke-linejoin'
    SVG_STROKE_OPACITY = 'stroke-opacity'
    SVG_STROKE_WIDTH = 'stroke-width'
    SVG_MASK = 'mask'
    SVG_POINTS = 'points'
    presentationMap = {
        SVG_CLIP: 'android:clip',
        SVG_CLIP_RULE: '',     # Treated individually.
        SVG_FILL: 'android:fillColor',
        SVG_FILL_OPACITY: 'android:fillAlpha',
        SVG_FILL_RULE: 'android:fillType',
        SVG_OPACITY: '',       # Treated individually.
        SVG_PAINT_ORDER: '',   # Treated individually.
        SVG_STROKE: 'android:strokeColor',
        SVG_STROKE_LINECAP: 'android:strokeLineCap',
        SVG_STROKE_LINEJOIN: 'android:strokeLineJoin',
        SVG_STROKE_OPACITY: 'android:strokeAlpha',
        SVG_STROKE_WIDTH: 'android:strokeWidth'
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
    unsupportedSvgNodes = [
        # Animation elements.
        'animate',
        'animateColor',
        'animateMotion',
        'animateTransform',
        'mpath',
        'set',
        # Container elements.
        'a',
        'marker',
        'missing-glyph',
        'pattern',
        'switch',
        # Filter primitive elements.
        'feBlend',
        'feColorMatrix',
        'feComponentTransfer',
        'feComposite',
        'feConvolveMatrix',
        'feDiffuseLighting',
        'feDisplacementMap',
        'feFlood',
        'feFuncA',
        'feFuncB',
        'feFuncG',
        'feFuncR',
        'feGaussianBlur',
        'feImage',
        'feMerge',
        'feMergeNode',
        'feMorphology',
        'feOffset',
        'feSpecularLighting',
        'feTile',
        'feTurbulence',
        # Font elements.
        'font',
        'font-face',
        'font-face-format',
        'font-face-name',
        'font-face-src',
        'font-face-uri',
        'hkern',
        'vkern',
        # Gradient elements.
        'stop',
        # Graphics elements.
        'ellipse',
        'image',
        # Light source elements.
        'feDistantLight',
        'fePointLight',
        'feSpotLight',
        # Structural elements.
        'symbol',
        # Text content elements.
        'altGlyphDef',
        'altGlyphItem',
        'glyph',
        'glyphRef',
        'text',
        # Text content child elements.
        'altGlyph',
        'textPath',
        'tref',
        'tspan',
        # Uncategorized elements.
        'color-profile',
        'cursor',
        'filter',
        'foreignObject',
        'script',
        'view'
        ]
    SPACE_OR_COMMA = r'[\s,]+'

    @classmethod
    def parse(cls, path: str) -> SvgTree:
        svgTree = SvgTree()
        parseErrors = []
        doc = svgTree.parse(path, parseErrors)
        for error in parseErrors:
            svgTree.logError(error, None)

        # Get <svg> elements.
        nSvgNode = doc.getElementsByTagName('svg')
        if len(nSvgNode) != 1:
            message = 'No <svg> tags found' if len(svgNode) == 0 else 'Multiple <svg> tags are not supported.'
            raise ValueError(message)
        rootElement = nSvgNode.item(0)
        svgTree.parseDimension(rootElement)

        if svgTree.viewBox == None:
            svgTree.logError('Missing "viewBox" in <svg> element', rootElement)
            return svgTree
        
        root = SvgGroupNode(svgTree, rootElement, 'root')
        svgTree.setRoot(root)

        # Parse all the group and path node recursively.
        cls.traverseSvgAndExtract(svgTree, root, rootElement)
        cls.resolveUseNodes(svgTree)
        cls.resolveGradientReference(svgTree)

        # TODO: Handle clipPath elements that reference another clipPath
        # Add attributes for all the style elements.
        for key, value in svgTree.getStyleAffectedNodes().items():
            for n in value:
                cls.addStyleToPath(n, svgTree.getStyleClassAttr(key))

        # Replaces elements that reference clipPaths and replaces them with clipPathNodes
        # Note that clip path can be embedded within style, so it has to be called after
        # addStyleToPath.
        for key, value in svgTree.getClipPathAffectedNodesSet().items():
            cls.handleClipPath(svgTree, key, value[0], value[1])

        svgTree.flatten()
        svgTree.validate()
        svgTree.dump()

        return svgTree

    # Fills in all <use> nodes in the svgTree.
    @classmethod
    def resolveUseNodes(cls, svgTree: SvgTree):
        nodes = svgTree.getPendingUseSet()
        pendingUseSet = set(nodes)
        while nodes:
            nl = len(nodes)
            nodes = {n for n in nodes if not n.resolveHref(svgTree)}
            if nl == len(nodes):
                cls.reportCycles(svgTree, nodes)
                return
        ordering = cls.getUseNodeTopologicalOrdering(svgTree, pendingUseSet)
        [o.handleUse() for o in ordering]

    # This orders the 'use' nodes in pendingUseSet in a topological order, in the sense that an
    # earlier node does not reference a part of the svgTree that contains a later node.
    @classmethod
    def getUseNodeTopologicalOrdering(cls, svgTree: SvgTree, pendingUseSet: set[SvgGroupNode]) -> list[SvgGroupNode]:
        queue = deque([])
        # Directed graph where nodes of the svgTree point to their parent and 'use' nodes that
        # reference them.
        reverseGraph = dict()
        inDegrees = dict()
        root = svgTree.getRoot()
        queue.append(root)
        reverseGraph[root] = set()
        inDegrees[root] = 0
        while queue:
            current = queue.popleft()
            if current is SvgGroupNode:
                for child in current.mChildren:
                    reverseGraph.setdefault(child, {})
                    reverseGraph[child].append(current)
                    if child not in inDegrees:
                        queue.append(child)
                        inDegrees[child] = 0
                useRefNode = groupNode.mUseReferenceNode
                if useRefNode:
                    reverseGraph.setdefault(useRefNode, {})
                    reverseGraph[useRefNode].append(current)
                    if useRefNode not in inDegrees:
                        queue.append(useRefNode)
                        inDegrees[useRefNode] = 0
        for node, value in reverseGraph.items():
            for child in value:
                inDegrees[child] = inDegrees[child] + 1
        for node, value in inDegrees.items():
            if value == 0:
                queue.append(node)
        
        topologicalOrdering = []
        while queue:
            current = queue.popleft()
            if current is SvgGroupNode:
                if current.mUseReferenceNode:
                    topologicalOrdering.append(current)
                    pendingUseSet.remove(current)
            for child in reverseGraph[current]:
                inDegrees[child] = inDegrees[child] - 1
                if inDegrees[child] == 0:
                    queue.append(child)

        # Add remaining nodes for which the order is irrelevant
        topologicalOrdering.extend(pendingUseSet)
        return topologicalOrdering

    # Resolve all href reference in gradient nodes.
    @classmethod
    def resolveGradientReference(cls, svgTree: SvgTree):
        nodes = svgTree.getPendingGradientRefSet()
        while nodes:
            nl = len(nodes)
            nodes = {n for n in nodes if n.resoveHref(svgTree)}
            if nl == len(nodes):
                # Not avle to make progress because of cyclic references.
                cls.reportCycles(svgTree, nodes)
                break

    @classmethod
    def reportCycles(cls, svgTree: SvgTree, svgNodes: set) -> SvgNode:
        edges = dict()
        nodesById = dict()
        for svgNode in svgNodes:
            element = svgNode.getDocumentElement()
            _id = element.getAttribute('id')
            if _id:
                targetId = svgNode.getHrefId()
                if targetId:
                    edges[_id] = targetId
                    nodesById[_id] = element

        while edges:
            visited = set()
            _id = next(iter(edges))
            targetId = edges[_id]
            while targetId and _id not in visited:
                visited.append(_id)
                _id = targetId
                targetId = edges[_id]
            
            if targetId:    # Broken links are reported separately. Ignore them here.
                node = nodesById[_id]
                cycle = cls.getCycleStartingAt(_id, edges, nodesById)
                svgTree.logError(f'Circular dependency of <use> nodes: {cycle}', node)
            for v in visited:
                del edges[v]

    @classmethod
    def getCycleStartingAt(cls, startId: str, edges: dict, nodesById: dict) -> str:
        buf = ''
        _id = startId
        while True:
            _id = edges[_id]
            buf += f' -> {_id}'
            if _id == startId:
                break
            buf += f' (line {cls.getStartLine(nodesById[_id])})'
        return buf

    @classmethod
    def traverseSvgAndExtract(cls, svgTree: SvgTree, currentGroup: SvgGroupNode, item:minidom.Element):
        childNodes = item.childNodes

        for idx, childNode in enumerate(childNodes):
            if childNode.nodeType != minidom.Node.ELEMENT_NODE or not childNode.hasChildNodes() and not childNode.hasAttributes():
                continue

            tagName = childNode.tagName
            if tagName in [cls.SVG_PATH, cls.SVG_RECT, cls.SVG_CIRCLE, cls.SVG_ELLIPSE, cls.SVG_POLYGON, cls.SVG_POLYLINE, cls.SVG_LINE]:
                child = SvgLeafNode(svgTree, childNode, f'{tagName}{idx}')
                cls.processIdName(svgTree, child)
                currentGroup.addChild(child)
                cls.extractAllItemsAs(svgTree, child, childNode, currentGroup)
                svgTree.setHasLeafNode(True)
            elif cls.SVG_GROUP == tagName:
                childGroup = SvgGroupNode(svgTree, childNode, f'child{idx}')
                currentGroup.addChild(childGroup)
                cls.processIdName(svgTree, childGroup)
                cls.extractGroupNode(svgTree, childGroup, currentGroup)
                cls.traverseSvgAndExtract(svgTree, childGroup, childNode)
            elif cls.SVG_USE == tagName:
                childGroup = SvgGroupNode(svgTree, childNode, f'child{idx}')
                cls.processIdName(svgTree, childGroup)
                currentGroup.addChild(childGroup)
                svgTree.addToPendingUseSet(childGroup)
            elif cls.SVG_DEFS == tagName:
                childGroup = SvgGroupNode(svgTree, childNode, f'child{idx}')
                cls.traverseSvgAndExtract(svgTree, childGroup, childNode)
            elif tagName in [cls.SVG_CLIP_PATH_ELEMENT, cls.SVG_MASK]:
                clipPath = SvgClipPathNode(svgTree, childNode, f'{tagName}{idx}')
                cls.processIdName(svgTree, clipPath)
                cls.traverseSvgAndExtract(svgTree, clipPath, childNode)
            elif cls.SVG_STYLE == tagName:
                cls.extractStyleNode(svgTree, childNode)
            elif 'linearGradient' == tagName:
                gradientNode = SvgGradientNode(svgTree, childNode, f'{tagName}{idx}')
                cls.processIdName(svgTree, gradientNode)
                cls.extractGradientNode(svgTree, gradientNode)
                gradientNode.fillPresentationAttributes('gradientType', 'linear')
                svgTree.setHasGradient(True)
            elif 'radialGradient' == tagName:
                gradientNode = SvgGradientNode(svgTree, childNode, f'{tagName}{idx}')
                cls.processIdName(svgTree, gradientNode)
                cls.extractGradientNode(svgTree, gradientNode)
                gradientNode.fillPresentationAttributes('gradientType', 'radial')
                svgTree.setHasGradient(True)
            else:
                _id = childNode.getAttribute('id')
                if _id:
                    svgTree.addIgnoredId(_id)
                # For other fancy tags, like <switch>, they can contain children too.
                # Report the unsupported nodes.
                if tagName in cls.unsupportedSvgNodes:
                    svgTree.logError(f'<{tagName}> is not supported', childNode)
                # This is a workaround for the cases using defs to define a full icon size clip
                # path, which is redundent information anyway.
                cls.traverseSvgAndExtract(svgTree, currentGroup, childNode)

    # Reads content from a gradient element's decumentNode and fills in attributes for the given
    # Svg gradient node.
    @classmethod
    def extractGradientNode(cls, svg: SvgTree, gradientNode: SvgGradientNode):
        element = gradientNode.getDocumentElement()
        attrs = element.attributes
        if element.getAttribute(cls.SVG_HREF) or element.getAttribute(cls.SVG_XLINK_HREF):
            svg.addToPendingGradientRefSet(gradientNode)
        
        for i in range(attrs.length):
            n = attrs.item(i)
            name = n.nodeName
            value = n.nodeValue
            if name in cls.gradientMap:
                gradientNode.fillPresentationAttributes(name, value)
        gradientChildren = element.childNodes

        # Default SVG gradient offset is the previous largets offset.
        greatestOffset = 0.0
        for i in range(gradientChildren.length):
            node = gradientChildren.item(i)
            nodeName = node.nodeName
            if nodeName == 'stop':
                stopAttr = node.attributes
                # Default SVG gradient stop color is black.
                color = 'rgb(0,0,0)'
                # Default SVG gradient stop opacity is 1.
                opacity = '1'
                for k in range(stopAttr.length):
                    stopItem = stopAttr.item(k)
                    name = stopItem.nodeName
                    value = stopItem.nodeValue
                    try:
                        if name == 'offset':
                            # If a gradient's value is not greater than all previous offset
                            # values, then the offset value is adjusted to be equal to
                            # the largets of all previous offset values.
                            greatestOffset = cls.extractOffset(value, greatestOffset)
                        elif name == 'stop-color':
                            color = value
                        elif name == 'stop-opacity':
                            opacity = value
                        elif name == 'style':
                            for attr in value.split(';'):
                                splitAttribute = attr.split(':')
                                if len(splitAttribute) == 2:
                                    if attr.startswith('stop-color'):
                                        color = splitAttribute[1]
                                    elif attr.startswith('stop-opacity'):
                                        opacity = splitAttribute[1]
                    except Exception as e:
                        svg.logError(f'Invalid attribute value: {name}="{value}"', node)
                offset = svg.formatCoordinate(greatestOffset)
                vdColor = gradientNode.colorSvg2Vd(color, '#000000')
                if vdColor:
                    color = vdColor
                gradientNode.addGradientStop(color, offset, opacity)
                            
    # Finds the gradient offset value given a String containing the value and greatest previous
    # offset value.
    # @param offset an absolute floating point value or a percentage
    # @param greatestOffset is the greatest offset value seen in the gradient so far
    # @return the new greatest offset value
    @classmethod
    def extractOffset(cls, offset: str, greatestOffset: float) -> float:
        x = 0.0
        if offset.endswith('%'):
            x = float(offset[:-1]) / 100
        else:
            x = float(offset)
        # Gradient offset value must be between 0 and 1 or 0% and 100%.
        x = min(1, max(x, 0))
        return max(x, greatestOffset)

    # Checks to see if the childGroup reference an clipPath or style elements. Saves the
    # reference in the svgTree to add the information to an SvgNode later.
    @classmethod
    def extractGroupNode(cls, svgTree: SvgTree, childGroup:SvgGroupNode, currentGroup: SvgGroupNode):
        a = childGroup.getDocumentElement().attributes
        for j in range(a.length):
            n = a.item(j)
            name = n.nodeName
            value = n.nodeValue
            if name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                if value:
                    svgTree.addClipPathAffectedNode(childGroup, currentGroup, value)
            elif name == 'class':
                if value:
                    svgTree.addAffectedNodeToStyleClass('.', value, childGroup)                    

    # Extracts the attribute information from a style element and adds to the
    # styleClassAttributeMap of the SvgTree. SvgNodes reference style elements using a 'class'
    # attribute. The style attribute will be filled into the tree after the svgTree calls
    # traverseSVGAndExtract().
    @classmethod
    def extractStyleNode(cls, svgTree: SvgTree, currentNode: minidom.Node):
        a = currentNode.childNodes
        styleData = ''
        for j in range(a.length):
            n = a.item(j)
            if n.nodeType == minidom.Type.CDATA_SECTION_NODE or a.length == 1:
                styleData = n.nodeValue
        if styleData:
            # Separate each of the classes.
            classData = styleData.split('}')
            for sClassData in classData:
                splitClassData = aClassData.split('\\{')
                if len(splitClassData) < 2:
                    # When the class info is empty, then skip.
                    continue
                className = splitClassData[0].strip()
                styleAttr = splitClassData[1].strip()
                # Separate multiple classes if necessary.
                splitClassNames = className.split(',')
                for splitClassName in splitClassNames:
                    styleAttrTemp = styleAttr
                    className = splitClassName.strip()
                    # Concatenate the attributes to existing attributes.
                    existing = svgTree.getStyleClassAttr(className)
                    if existing:
                        styleAttrTemp += f';{existing}'
                    svgTree.addStyleClassToTree(className, styleAttrTemp)
    
    # Checks if the id of a node exists and adds the id and svgNode to the svgTree's idMap if it
    # exists.
    @classmethod
    def processIdName(cls, svgTree: SvgTree, node: SvgNode):
        _id = node.getAttributeValue('id')
        if _id:
            svgTree.addIdToMap(_id, node)

    # Replaces an SvgNode in the SvgTree that references a clipPath element with the
    # SvgClipPathNode that corresponds to the referenced clip-path id. Adds the SvgNode as an
    # affected node of the SvgClipPathNode.
    @classmethod
    def handleClipPath(cls, svg: SvgTree, child: SvgNode, currentGroup: SvgGroupNode, value: str):
        if not currentGroup or not value:
            return
        clipName = cls.getClipPathName(value)
        if not clipName:
            return
        clipNode = svg.getSvgNodeFromId(clipName)
        if not clipNode:
            return
        clipCopy = clipNode.deepCopy()

        currentGroup.replaceChild(child, clipCopy)

        clipCopy.addAffectedNode(child)
        clipCopy.setClipPathNodeAttributes()

    # Normally, clip path is referred as "url(#clip-path)", this function can help to extract the
    # name, which is "clip-path" here.
    # @return the name of the clip path or null if the given string does not contain a proper clip
    #     path name.
    @classmethod
    def getClipPathName(cls, s: str) -> str:
        if not s:
            return None
        startPos = s.find('#')
        endPos = s.find(')', startPos + 1)
        if endPos < 0:
            endPos = len(s)
        return s[startPos + 1: endPos].strip()
    
    # Read the content from currentItem, and fill into the SvgLeafNode "child".
    @classmethod
    def extractAllItemsAs(cls, svg: SvgTree, child: SvgLeafNode, currentItem: minidom.Node, currentGroup: SvgGroupNode):
        parentNode = currentItem.parentNode
        hasNodeAttr = False
        styleContent = ''
        styleContentBuilder = ''
        nothingToDisplay = False

        while parentNode and parentNode.nodeName == 'g':
            # Parse the group's attributes.
            logging.info('Printing current patent')
            cls.printlnCommon(parentNode)

            nodeAttr = parentNode.getAttribute(cls.SVG_STYLE)
            # Search for the "display:none", if existed, then skip this item
            if nodeAttr:
                styleContent += f'{nodeAttr.value};'
                logging.info(f'styleContent is :{styleContent} at number group')
                if 'display:none' in styleContent:
                    logging.info('Found none style, skip the whole group')
                    nothingToDisplay = True
                    break
                else:
                    hasNodeAttr = True
            
            displayAttr = parentNode.getAttribute(cls.SVG_DISPLAY)
            if displayAttr and 'none' == displayAttr.ndoeValue:
                logging.info('Found display:none style, skip the whole group')
                nothingToDisplay = True
                break
            parentNode = parentNode.parentNode
        
        if nothingToDisplay:
            # Skip this current whole item.
            return
        
        logging.info('Print current item')
        cls.printlnCommon(currentItem)

        if hasNodeAttr and styleContent:
            cls.addStyleToPath(child, styleContent)

        if cls.SVG_PATH == currentItem.nodeName:
            cls.extractPathItem(svg, child, currentItem, currentGroup)
        
        if cls.SVG_RECT == currentItem.nodeName:
            cls.extractRectItem(svg, child, currentItem, currentGroup)

        if cls.SVG_CIRCLE == currentItem.nodeName:
            cls.extractCircleItem(svg, child, currentItem, currentGroup)

        if currentItem.nodeName in {
            cls.SVG_POLYGON, cls.SVG_POLYLINE
        }:
            cls.extractPolyItem(svg, child, currentItem, currentGroup)

        if cls.SVG_LINE == currentItem.nodeName:
            cls.extractLineItem(svg, child, currentItem, currentGroup)

        if cls.SVG_ELLIPSE == currentItem.nodeName:
            cls.extractEllipseItem(svg, child, currentItem, currentGroup)

        # Add the type of node as a style class name for child.
        svg.addAffectedNodeToStyleClass(currentItem.nodeName, child)

    @classmethod
    def printlnCommon(cls, n: minidom.Node):
        logging.info(f'nodeName="{n.nodeName}"')

        val = n.namespaceURI
        if val:
            logging.info(f'uri="{val}"')
            pass

        val = n.prefix

        if val:
            logging.info(f'pre="{val}"')
            pass

        val = n.localName
        if val:
            logging.info(f'local="{val}"')
            pass

        val = n.nodeValue
        if val:
            logging.info('nodeValue=')
            if val.strip() == '':
                # Whitespace
                logging.info('[WS]')
                pass
            else:
                logging.info(f'"{n.ndoeVlaue}"')
                pass


    # Convert polygon element into a path.
    @classmethod
    def extractPolyItem(cls, svgTree: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'Polyline or Polygon found{currentGroupNode}')
        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            attributes = currentGroupNode.attributes
            for itemIndex in range(attributes.length):
                n = attributes.item(itemIndex)
                name = n.nodeName
                value = n.nodeValue
                try:
                    if cls.SVG_STYLE == name:
                        cls.addStyleToPath(child, value)
                    elif name in cls.presentationMap:
                        child.fillPresentationAttributes(name, value)
                    elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                        svgTree.addClipPathAffectedNode(child, currentGroup, value)
                    elif name == cls.SVG_POINTS:
                        builder = PathBuilder()
                        splt = re.split(cls.SPACE_OR_COMMA, value)
                        baseX = float(splt[0])
                        baseY = float(splt[1])
                        builder.absoluteMoveTo(baseX, baseY)
                        for i in range(2, len(splt), 2):
                            x = float(splt[i])
                            y = float(splt[i + 1])
                            builder.relativeLineTo(x - baseX, y - baseY)
                            baseX = x
                            baseY = y
                        if currentGroupNode.nodeName == cls.SVG_POLYGON:
                            builder.relativeClose()
                        child.setPathData(builder.toString())
                    elif name == 'class':
                        svgTree.addAffectedNodeToStyleClass(f'.{value}', child)
                        svgTree.addAffectedNodeToStyleClass(f'{currentGroupNode.nodeName}.{value}', child)
                except Exception as e:
                    svgTree.logError(f'Invalid value of "{name}" attribute', n)
                
    
    # Convert rectangle element into a path
    @classmethod
    def extractRectItem(cls, svg: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'Rect found{currentGroupNode}')

        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            x = 0.0
            y = 0.0
            width = float('nan')
            height = float('nan')
            rx = 0.0
            ry = 0.0

            a = currentGroupNode.attributes
            pureTransparent = False
            for j in range(a.length):
                n = a.item(j)
                name = n.nodeName
                value = n.nodeValue
                try:
                    if cls.SVG_STYLE == name:
                        cls.addStyleToPath(child, value)
                        if 'opacity:0;' in value:
                            pureTransparent = True
                    elif name in cls.presentationMap:
                        child.fillPresentationAttributes(name, value)
                    elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                        svg.addClipPathAffectedNode(child, currentGroup, value)
                    elif 'x' == name:
                        x = svg.parseXValue(value)
                    elif 'y' == name:
                        y = svg.parseYValue(value)
                    elif 'rx' == name:
                        rx = svg.parseXValue(value)
                    elif 'ry' == name:
                        ry = svg.parseYValue(value)
                    elif 'width' == name:
                        width = svg.parseXValue(value)
                    elif 'height' == name:
                        height = svg.parseYValue(value)
                    elif 'class' == name:
                        svgTree.addAffectedNodeToStyleClass(f'rect.{value}', child)
                        svgTree.addAffectedNodeToStyleClass(f'.{value}', child)
                except Exception as e:
                    svg.logError(f'Invalid attribute value: {name}="{value}"', currentGroupNode)
            
            if not pureTransparent and x != float('nan') and y != float('nan') and width != float('nan') and height != float('nan'):
                builder = PathBuilder()
                if rx <= 0 and ry <= 0:
                    # "M x, y h width v height h -width z"
                    builder.absoluteMoveTo(x, y)
                    builder.relativeHorizontalTo(width)
                    builder.relativeVerticalTo(height)
                    builder.relativeHorizontalTo(-width)
                else:
                    # Refer to http://www.w3.org/TR/SVG/shapes.html#RectElement
                    assert rx > 0 or ry > 0
                    if ry == 0:
                        ry = rx
                    elif rx == 0:
                        rx = ry
                    if width / 2 < rx:
                        rx = width / 2
                    if height / 2 < ry:
                        ry = height / 2
                    
                    builder.absoluteMoveTo(x + rx, y)
                    builder.absoluteLineTo(x + width - rx, y)
                    builder.absoluteArcTo(rx, ry, False, False, True, x + width, y + ry)
                    builder.absoluteLineTo(x + width, y + height - ry)
                    builder.absoluteArcTo(rx, ry, False, False, True, x + width - rx, y + height)
                    builder.absoluteLineTo(x + rx,  y + height)
                    builder.absoluteArcTo(rx, ry, False, False, True, x, y + height - ry)
                    builder.absoluteLineTo(x,  y + ry)
                    builder.absoluteArcTo(rx, ry, False, False, True, x + rx, y)

                builder.relativeClose()
                child.setPathData(builder.toString())

    # Convert circle element into a path.
    @classmethod
    def extractCircleItem(cls, svg: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'circle found{currentGroupNode}')
        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            cx = 0
            cy = 0
            radius = 0

            pureTransparent = False
            a = currentGroupNode.attributes
            for i in range(a.length):
                n = a.item(i)
                name = n.nodeName
                value = n.nodeValue
                if cls.SVG_STYLE == name:
                    cls.addStyleToPath(child, value)
                    if 'opacity:0;' in value:
                        pureTransparent = True
                elif name in cls.presentationMap:
                    child.fillPresentationAttributes(name, value)
                elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                    svg.addClipPathAffectedNode(child, currentGroup, value)
                elif 'cx' == name:
                    cx = float(value)
                elif 'cy' == name:
                    cy = float(value)
                elif 'r' == name:
                    radius = float(value)
                elif 'class' == name:
                    svgTree.addAffectedNodeToStyleClass(f'circle.{value}', child)
                    svgTree.addAffectedNodeToStyleClass(f'.{value}', child)

                if not pureTransparent and cx != float('nan') and cy != float('nan'):
                    # "M cx cy m -r, 0 a r,r 0 1,1 (r * 2)0 a r,r 0 1,1 -(r * 2),0"
                    builder = PathBuilder()
                    builder.absoluteMoveTo(cx, cy)
                    builder.relativeMoveTo(-radius, 0)
                    builder.relativeArcTo(radius, radius, False, True, True, 2 * radius, 0)
                    builder.relativeArcTo(radius, radius, False, True, True, -2 * radius, 0)
                    child.setPathData(builder.toString())
    
    # Convert ellipse element into a path
    @classmethod
    def extractEllipseItem(cls, svg: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'ellipse found{currentGroupNode}')

        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            cx = 0.0
            cy = 0.0
            rx = 0.0
            ry = 0.0

            a = currentGroupNode.attributes
            pureTransparent = False
            for j in range(a.length):
                n = a.item(j)
                name = n.nodeName
                value = n.nodeValue
                if cls.SVG_STYLE == name:
                    cls.addStyleToPath(child, value)
                    if 'opacity:0;' in value:
                        pureTransparent = True
                elif name in cls.presentationMap:
                    child.fillPresentationAttributes(name, value)
                elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                    svg.addClipPathAffectedNode(child, currentGroup, value)
                elif 'cx' == name:
                    cx = float(value)
                elif 'cy' == name:
                    cy = float(value)
                elif 'rx' == name:
                    rx = float(value)
                elif 'ry' == name:
                    ry = float(value)
                elif 'class' == name:
                    svgTree.addAffectedNodeToStyleClass(f'ellipse.{value}', child)
                    svgTree.addAffectedNodeToStyleClass(f'.{value}', child)

            if not pureTransparent and cx != float('nan') and cy != float('nan') and 0 < rx and 0 < ry:
                # "M cx -rx, cy a rx,ry 0 1,0 (rx * 2),0 a rx,ry 0 1,0 -(rx * 2),0"
                builder = PathBuilder()
                builder.absoluteMoveTo(cx - rx, cy)
                builder.relativeArcTo(rx, ry, False, True, False, 2 * rx, 0)
                builder.relativeArcTo(rx, ry, False, True, False, -2 * rx, 0)
                builder.relativeClose()
                child.setPathData(builder.toString())

    # Convert line element into a path
    @classmethod
    def extractLineItem(cls, svg: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'line found{currentGroupNode}')

        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            x1 = 0.0
            y1 = 0.0
            x2 = 0.0
            y2 = 0.0

            a = currentGroupNode.attributes
            pureTransparent = False
            for j in range(a.length):
                n = a.item(j)
                name = n.nodeName
                value = n.nodeValue
                if cls.SVG_STYLE == name:
                    cls.addStyleToPath(child, value)
                    if 'opacity:0;' in value:
                        pureTransparent = True
                elif name in cls.presentationMap:
                    child.fillPresentationAttributes(name, value)
                elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                    svg.addClipPathAffectedNode(child, currentGroup, value)
                elif 'x1' == name:
                    x1 = float(value)
                elif 'y1' == name:
                    y1 = float(value)
                elif 'x2' == name:
                    x2 = float(value)
                elif 'y2' == name:
                    y2 = float(value)
                elif 'class' == name:
                    svgTree.addAffectedNodeToStyleClass(f'line.{value}', child)
                    svgTree.addAffectedNodeToStyleClass(f'.{value}', child)

            if pureTransparent == False and svg and x1 != float('nan') and y1 != float('nan') and x2 != float('nan') and y2 != float('nan'):
                # "M x1, y1 L x2, y2"
                builder = PathBuilder()
                builder.absoluteMoveTo(x1, y1)
                builder.absoluteLineTo(x2, y2)
                child.setPathData(builder.toString())

    @classmethod
    def extractPathItem(cls, svg: SvgTree, child: SvgLeafNode, currentGroupNode: minidom.Node, currentGroup: SvgGroupNode):
        logging.info(f'Path found{currentGroupNode}')

        if currentGroupNode.nodeType == minidom.Node.ELEMENT_NODE:
            a = currentGroupNode.attributes
            for i in range(a.length):
                n = a.item(i)
                name = n.nodeName
                value = n.nodeValue
                if cls.SVG_STYLE == name:
                    cls.addStyleToPath(child, value)
                elif name in cls.presentationMap:
                    child.fillPresentationAttributes(name, value)
                elif name in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                    svg.addClipPathAffectedNode(child, currentGroup, value)
                elif cls.SVG_D == name:
                    pathData = re.sub(r'(\d)-', r'\1,-', value)
                    child.setPathData(pathData)
                elif 'class' == name:
                    svg.addAffectedNodeToStyleClass(f'path.{value}', child)
                    svg.addAffectedNodeToStyleClass(f'.{value}', child)

    @classmethod
    def addStyleToPath(cls, path: SvgNode, value: str):
        logging.info(f'Style found is{value}')
        if value:
            for subStyle in reversed(value.split(';')):
                nameValue = subStyle.split(':')
                if len(nameValue) == 2 and nameValue[0] and nameValue[1]:
                    attr = nameValue[0].strip()
                    val = nameValue[1].strip()
                    if attr in cls.presentationMap:
                        path.fillPresentationAttributes(attr, val)
                    elif attr == cls.SVG_OPACITY:
                        # TODO: This is hacky, since we don't have a group level
                        # android:opacity. This only works when the path didn't overlap.
                        path.fillPresentationAttributes(cls.SVG_FILL_OPACITY, nameValue[1])
                    
                    # We need to handle a clip-path or mask within the style in a different way
                    # then other styles. We treat it as an attribute clip-path = "#url(name)".
                    if attr in [cls.SVG_CLIP_PATH, cls.SVG_MASK]:
                        parentNode = path.getTree().findParent(path)
                        if parentNode:
                            path.getTree().addClipPathAffectedNode(path, parentNode, val)
    
    # def getSizeString(cls. w, h, scaleFactor):
    #     return f'        android:width="{int(w * scaleFactor)}dp"\n        android:height="{int(h * scaleFactor)}dp"\n'
    @classmethod
    def writeFile(cls, OutputStreamWriter: OutputStreamWriter, svgTree: SvgTree):
        svgTree.writeXml(OutputStreamWriter)

    # Converts an SVG file into VectorDrawable's XML content, if no error is found.
    # @param inputSvg the input SVG file
    # @param outStream the converted VectorDrawable's content. This can be empty if there is any
    #     error found during parsing
    # @return the error message that combines all logged errors and warnings, or an empty string if
    #     there were no errors
    @classmethod
    def parseSvgToXml(cls, inputSVG: str, OutputStreamWriter: OutputStreamWriter) -> str:
        svgTree = cls.parse(inputSVG)
        if svgTree.getHasLeafNode():
            cls.writeFile(OutputStreamWriter, svgTree)
        return svgTree.getErrorMessage()