import xml.dom.minidom as minidom
import xml.sax

class LineNumberDOMHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        super().__init__()
        self.dom = minidom.Document()
        self.current_node = self.dom
        self.locator = None

    def setDocumentLocator(self, locator):
        self.locator = locator
    
    def startElement(self, name, attrs):
        line_number = self.locator.getLineNumber()
        element = self.dom.createElement(name)
        for qname, value in attrs.items():
            element.setAttribute(qname, value)
        self.current_node.appendChild(element)
        self.current_node = element
        setattr(element, '__line_number__', line_number)
    
    def endElement(self, name):
        if self.current_node.parentNode:
            self.current_node = self.current_node.parentNode

    def characters(self, content):
        if content.strip():
            text_node = self.dom.createTextNode(content)
            self.current_node_appendChild(text_node)

    def get_dom(self):
        return self.dom

class PositionXmlParser:
    @classmethod
    def parse(cls, path):
        handler = LineNumberDOMHandler()
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        xml.sax.parse(path, handler)
        return handler.get_dom()