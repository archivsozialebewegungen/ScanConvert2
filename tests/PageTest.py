'''
Created on 01.11.2022

@author: michael
'''
import os
import unittest

from Asb.ScanConvert2.ScanConvertDomain import Scan, Page, Region, Algorithm
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

    def testAlgorithmGray(self):

        scan = Scan(os.path.join(self.test_file_dir, "Testtext", "Seite8.jpg"))
        page = Page(scan, Region(0, 0, scan.width, scan.height, Algorithm.GRAY))
        img = page.get_final_image()
        img.save("/tmp/gray.tif", compression="tiff_lzw")
        #img.show()

    def testAlgorithmOtsu(self):

        scan = Scan(os.path.join(self.test_file_dir, "Testtext", "Seite8.jpg"))
        page = Page(scan, Region(0, 0, scan.width, scan.height, Algorithm.OTSU))
        img = page.get_final_image()
        img.save("/tmp/otsu.tif", compression="tiff_lzw")

    def testAlgorithmSauvola(self):

        scan = Scan(os.path.join(self.test_file_dir, "Testtext", "Seite8.jpg"))
        page = Page(scan, Region(0, 0, scan.width, scan.height, Algorithm.SAUVOLA))
        img = page.get_final_image()
        img.save("/tmp/sauvola.tif", compression="tiff_lzw")

    def testAlgorithmFloydSteinberg(self):

        scan = Scan(os.path.join(self.test_file_dir, "Testtext", "Seite8.jpg"))
        page = Page(scan, Region(0, 0, scan.width, scan.height, Algorithm.FLOYD_STEINBERG))
        img = page.get_final_image()
        img.save("/tmp/floydsteinberg.tif", compression="tiff_lzw")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()