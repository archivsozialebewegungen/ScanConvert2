'''
Created on 01.11.2022

@author: michael
'''
import os
import unittest

from Asb.ScanConvert2.ScanConvertDomain import Scan, Page, Region
from Base import BaseTest


class PageTest(BaseTest):


    def testSimpleScanLoading(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_gray.png"))
        page = Page(scan, Region(0, 0, 80, 40))
        img = page.get_base_image()
        #img.show()

    def testHalfScanLoading(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_gray.png"))
        page = Page(scan, Region(0, 0, 40, 40))
        img = page.get_base_image()
        #img.show()

    def testRotation90ScanLoading(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_gray.png"))
        page = Page(scan, Region(0, 0, 80, 40), 90)
        img = page.get_base_image()
        #img.show()

    def testResolutionChange(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_gray.png"))
        page = Page(scan, Region(0, 0, 80, 40))
        img = page.get_base_image(150)
        #img.show()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()