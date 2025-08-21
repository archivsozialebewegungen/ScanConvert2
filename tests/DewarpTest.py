'''
Created on 21.08.2025

@author: michael
'''
import unittest
import os
from Asb.ScanConvert2.ScanConvertDomain import Scan, Page, ScanPart, Region
import pytesseract
from Asb.ScanConvert2.Algorithms import Algorithm


class DewarpTest(unittest.TestCase):


    def testDewarp(self):
        
        scan = Scan(os.path.join(os.path.dirname(__file__), "SampleFiles", "Dewarp", "warped.jpeg"))
        page = Page(scan, ScanPart.WHOLE, Region(0, 0, scan.width, scan.height, mode_algorithm=Algorithm.SAUVOLA))
        
        img = page.get_raw_image()
        page_text = pytesseract.image_to_string(img, lang="deu")
        self.assertFalse("Paritätisches Bildungswerk Bundesverband e.V." in page_text)
        
        page.dewarp = True
        img = page.get_raw_image()
        page_text = pytesseract.image_to_string(img, lang="deu")
        self.assertTrue("Paritätisches Bildungswerk Bundesverband e.V." in page_text)

        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()