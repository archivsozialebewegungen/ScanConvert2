'''
Created on 01.11.2022

@author: michael
'''
import unittest
import os
from Asb.ScanConvert2.ScanConvertDomain import Scan, Mode
from Base import BaseTest

class ScanTest(BaseTest):


    def testSimpleBWFile(self):
        # Actually png files do not support native black and white but
        # use a palette format, so for testing purposes we use
        # a tif file here
        scan = Scan(os.path.join(self.test_file_dir, "simple_bw.tif"))
        self.assertEqual(scan.width, 80)
        self.assertEqual(scan.height, 40)
        self.assertEqual(scan.resolution, 300)
        self.assertEqual(scan.mode, Mode.BW)

    def testSimpleGrayFile(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_gray.png"))
        self.assertEqual(scan.width, 80)
        self.assertEqual(scan.height, 40)
        self.assertEqual(scan.resolution, 300)
        self.assertEqual(scan.mode, Mode.GRAY)

    def testSimpleColorFile(self):
        
        scan = Scan(os.path.join(self.test_file_dir, "simple_color.png"))
        self.assertEqual(scan.width, 80)
        self.assertEqual(scan.height, 40)
        self.assertEqual(scan.resolution, 300)
        self.assertEqual(scan.mode, Mode.COLOR)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()