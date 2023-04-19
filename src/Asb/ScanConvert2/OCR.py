'''
Created on 03.11.2022

@author: michael
'''
from injector import singleton
import re
from PIL import Image
import pytesseract
from xml.dom.minidom import parseString, Element, Node

class OCRPage(object):
    
    def __init__(self, dpi=300):
        
        self.dpi = dpi
        self.width = None
        self.height = None
        self.lines = []
        
    def __str__(self):
        string = "DPI: %s" % self.dpi
        string += "\nDimensions: %s x %s" % (self.width, self.height)
        for line in self.lines:
            string += "\n%s" % line
        return string
        
class OCRLine(object):
    
    def __init__(self):
        
        self.bbox = None
        self.baseline_coefficients = (1.0, 0.0)
        self.textangle = 0
        self.font_size = None
        self.words = []
        
    def __str__(self):
        
        string = "  Bounding box: %s %s %s %s" % self.bbox
        string += "\n  Baseline coefficients: %s %s" % self.baseline_coefficients
        string += "\n  Textangle: %d" % self.textangle
        string += "\n  Font size: %s" % self.font_size
        for word in self.words:
            string += "\n%s" % word
        return string
        
class OCRWord(object):
    
    def __init__(self):
        
        self.text = ""
        self.bbox = None
        
    def __str__(self):
        string = "    Bounding box: %s %s %s %s" % self.bbox
        string += "\n    Text: %s" % self.text
        return string

@singleton
class OcrRunner(object):
    '''
    This wraps the whole execution of tesseract and parsing the HOCR output
    '''

    def __init__(self):
        
        self.re_boundingbox = re.compile(r'bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+);.*')
        self.re_x_size = re.compile(r'.*x_size\s+([0-9.]+);.*')
        self.re_baseline = re.compile(r'.*baseline\s+([0-9-.]+)\s+([0-9-.]+);.*')
        self.re_textangle = re.compile(r'.*textangle\s+([0-9-.]+)\s*;.*')
    

    def run_tesseract(self, img: Image, lang: str, psm: str=3) -> OCRPage:
        '''
        This is the only public method. It executes OCR on the given image and
        returns the information in a page object.
        '''

        hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr', lang=lang, config="--psm %d" % psm)
        dom = parseString(hocr)
        page = OCRPage(img.info['dpi'][0])
        page.width = img.size[0]
        page.height = img.size[1]
        return self._parse_dom(dom, page)
    
    def _parse_dom(self, dom: Element, page: OCRPage):

        for paragraph in dom.getElementsByTagName("p"):
            page = self._add_lines_to_page(paragraph, page)
        return page
    
    def _add_lines_to_page(self, paragraph: Element, page_data: OCRPage) -> OCRPage:
        
        for line in self._get_lines(paragraph):
            line_data = OCRLine()
            line_data.font_size = round(self._get_x_size(line) * 72 / page_data.dpi)
            line_data.bbox = self._get_bounding_box(line, page_data)
            line_data.baseline_coefficients = self._get_baseline_coefficients(line)
            line_data.textangle = self._get_textangle(line)
            assert(line_data.textangle == 90 or line_data.textangle == 0) # No other angles implemented
            line_data = self._add_words_to_line(line, line_data, page_data)
            page_data.lines.append(line_data)

        return page_data
    
    def _add_words_to_line(self, line: Element, line_data: OCRLine, page_data: OCRPage) -> OCRLine:

        for word in self._get_words(line):
            word_data = OCRWord()
            word_data.bbox = self._get_bounding_box(word, page_data)
            word_data.text = word.firstChild.nodeValue
            line_data.words.append(word_data)
        
        return line_data

    def _get_lines(self, paragraph: Element):
        
        lines = []
        for child in paragraph.childNodes:
            if child.nodeType == Node.ELEMENT_NODE \
                    and child.tagName == "span" \
                    and child.getAttribute("class") == "ocr_line":
                lines.append(child)
        return lines

    def _get_words(self, page: Element):
        
        words = []
        for child in page.childNodes:
            if child.nodeType == Node.ELEMENT_NODE \
                    and child.tagName == "span" \
                    and child.getAttribute("class") == "ocrx_word":
                words.append(child)
        return words
    
    def _get_bounding_box(self, element: Element, page_data: OCRPage):
        '''
        We recalculate the bounding box to match the differing coordinate
        system of reportlab
        '''
        matcher = re.match(self.re_boundingbox, element.getAttribute("title"))
        if matcher:
            return (float(matcher.group(1)), page_data.height - float(matcher.group(2)),
                    float(matcher.group(3)), page_data.height - float(matcher.group(4)))
        raise Exception("Malformed hocr")
    
    def _get_baseline_coefficients(self, element: Element):
        
        matcher = re.match(self.re_baseline, element.getAttribute("title"))
        if matcher:
            return (float(matcher.group(1)), float(matcher.group(2)))
        return (1.0, 0.0)

    def _get_textangle(self, element: Element):
        
        matcher = re.match(self.re_textangle, element.getAttribute("title"))
        if matcher:
            return int(matcher.group(1))
        return 0

    def _get_x_size(self, element: Element):
        
        matcher = re.match(self.re_x_size, element.getAttribute("title"))
        if matcher:
            return (float(matcher.group(1)))
        raise Exception("Malformed hocr")
