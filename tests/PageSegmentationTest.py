'''
Created on 19.02.2023

@author: michael
'''
import os
import unittest
import numpy as np

from PIL import Image

from Asb.ScanConvert2.PageSegmentation import PageSegmentor, show_bin_img
from Base import BaseTest
from skimage.filters.thresholding import threshold_otsu


class PageSegmentationTest(BaseTest):


    def setUp(self):
        
        super().setUp()
        
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", "picture_detection_simple.tif")


    def testSegmentation(self):
        
        segmentor = PageSegmentor()
        img = Image.open(self.test_file)
        segments = segmentor.find_segments(img)
        for segment in segments:
            if segment.bounding_box.size > 100000:
                new_img = segment.overlay_on_image(img)
                new_img.show("Composite")
                new_img.save("/tmp/test.tif")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()