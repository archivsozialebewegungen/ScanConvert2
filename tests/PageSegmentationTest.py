'''
Created on 19.02.2023

@author: michael
'''
import os
import unittest

from PIL import Image

from Asb.ScanConvert2.PageSegmentation import PageSegmentor
from Base import BaseTest


class PageSegmentationTest(BaseTest):


    def setUp(self):
        
        super().setUp()
        
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", "picture_detection_simple.tif")


    def testSegmentation(self):
        
        segmentor = PageSegmentor()
        segments = segmentor.find_segments(Image.open(self.test_file))
        self.assertEqual(0, len(segments))
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()