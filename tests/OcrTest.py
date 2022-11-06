'''
Created on 02.11.2022

@author: michael
'''
import unittest
from Base import BaseTest
import os
from reportlab.pdfgen.canvas import Canvas
from Asb.ScanConvert2.ScanConvertDomain import Scan
from PIL import Image
from Asb.ScanConvert2.ScanConvertServices import OCRService
from reportlab.lib.units import inch
from Asb.ScanConvert2.OCR import OcrRunner
import Asb


class OCRServiceTest(BaseTest):


    def testOcr(self):
        
        ocr_service = OCRService(OcrRunner())
        
        img = Image.open(os.path.join(self.test_file_dir, "Testtext", "Seite8schraeg.jpg"))
        pdf = Canvas("/tmp/ocrtest.pdf", pageCompression=1)
        width_in_dots, height_in_dots = img.size
        pdf.setPageSize((width_in_dots * inch / 300, height_in_dots * inch / 300))
        
        Asb.ScanConvert2.ScanConvertServices.INVISIBLE = 0
        pdf = ocr_service.add_ocrresult_to_pdf(img, pdf)
        
        pdf.showPage()
        pdf.save()

class OCRRunnerTest(BaseTest):

    def notestRun(self):
        
        ocr_runner = OcrRunner()
        img = Image.open(os.path.join(self.test_file_dir, "Testtext", "Seite8schraeg.jpg"))
        data = ocr_runner.run_tesseract(img)
        expected = '''DPI: 300
Dimensions: 2480 x 3507
  Bounding box: 265.0 232.0 1245.0 282.0
  Baseline coefficients: 0.017 -17.0
  Font size: 11
    Bounding box: 265.0 232.0 486.0 269.0
    Text: abschaffen.'''
        received = "%s" % data
        self.assertEqual(received[0:190], expected)
        #print(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()