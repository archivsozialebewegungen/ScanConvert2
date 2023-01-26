'''
Created on 02.11.2022

@author: michael
'''
import io
import os
import unittest

from PIL import Image
from fitz.fitz import Document
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

import Asb
from Asb.ScanConvert2.OCR import OcrRunner
from Asb.ScanConvert2.ScanConvertServices import OCRService
from Base import BaseTest


class OCRServiceTest(BaseTest):


    def testOcr(self):
        
        ocr_service = OCRService(OcrRunner())
        pdf_file = "/tmp/ocrtest1.pdf"
        img = Image.open(os.path.join(self.test_file_dir, "OCR", "OCRSample.png"))
        pdf = Canvas(pdf_file, pageCompression=1)
        width_in_dots, height_in_dots = img.size
        pdf.setPageSize((width_in_dots * inch / 300, height_in_dots * inch / 300))
        
        img_stream = io.BytesIO()
        img.save(img_stream, format='png')
        img_stream.seek(0)
        img_reader = ImageReader(img_stream)
        pdf.drawImage(img_reader, 0, 0, width_in_dots * inch / 300, height_in_dots * inch / 300)

        Asb.ScanConvert2.ScanConvertServices.INVISIBLE = 0
        pdf = ocr_service.add_ocrresult_to_pdf(img, pdf, "deu")
        
        pdf.showPage()
        pdf.save()
        document = Document(pdf_file)
        self.assertIn("Einfacher Text", document.get_page_text(0))
        self.assertIn("Text um 90° gedreht", document.get_page_text(0))
        # The next two assertions won't work due to tesseract not recognizing
        # the rotation angles
        #self.assertIn("Text auf dem Kopf", document.get_page_text(0))
        #self.assertIn("Text um 270° gedreht", document.get_page_text(0))
        self.assertIn("Text leicht schräg", document.get_page_text(0))
        self.assertIn("Text leicht negativ schräg", document.get_page_text(0))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()