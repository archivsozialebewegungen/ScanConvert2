'''
Created on 19.02.2023

@author: michael
'''
import os
import unittest

from PIL import Image

from Asb.ScanConvert2.PageSegmentation import WahlWongCaseySegmentationService
from Base import BaseTest


class PageSegmentationTest(BaseTest):


    def setUp(self):
        
        super().setUp()
        
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", "Margaretha_I_025.jpg")


    def testSegmentation(self):
        
        segmentor = WahlWongCaseySegmentationService()
        img = Image.open(self.test_file)
        segments = segmentor.find_photo_segments(img)
        self.assertEqual(1, len(segments))
        bw_img = Image.fromarray(segmentor.binarize(img.convert("L")))
        for segment in segments:
            seg_img = img.crop((segment.bounding_box.x, segment.bounding_box.y, segment.bounding_box.x2, segment.bounding_box.y2))
            seg_img = seg_img.convert("L")
            bw_img.paste(seg_img, (segment.bounding_box.x, segment.bounding_box.y))
            
        bw_img.show("Composite")
        bw_img.save("/tmp/test.tif")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()