'''
Created on 19.02.2023

@author: michael
'''
import os
import unittest

from PIL import Image

from Base import BaseTest
from parameterized import parameterized
from Asb.ScanConvert2.PageSegmentationModule.WahlWongCaseySegmentation import WahlWongCaseySegmentationService
from Asb.ScanConvert2.PageSegmentationModule.Operations import SmearingService,\
    BinarizationService, NdArrayService, ImageStatisticsService
from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox

class PageSegmentationTest(BaseTest):

    @parameterized.expand([
        ["1982_original.tif", 2, BoundingBox(1071,175,1825,665)],
        ["Margaretha_I_025.jpg", 1, BoundingBox(267,624,1260,1903)],
        ["Margaretha_I_192.jpg", 1, BoundingBox(295,494,1497,941)],
        ["picture_detection_simple.tif", 1, BoundingBox(816,800,1537,1880)],
        #["picture_detection.tif", 1, BoundingBox(0,0,0,0)],
    ])
    def test_segmentation(self, filename, no_of_pictures, bounding_box):
        
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", filename)


        segmentation_service = WahlWongCaseySegmentationService(SmearingService(), BinarizationService(), NdArrayService(), ImageStatisticsService())
        img = Image.open(self.test_file)
        segmented_page = segmentation_service.get_segmented_page(img)
        photo_segments = segmented_page.photo_segments
        self.assertEqual(no_of_pictures, len(segmented_page.photo_segments))
        self.assertBoundingBoxesEqualApproximately(photo_segments[0].bounding_box, bounding_box)
    
    def assertValuesEqualApproximately(self, v1, v2):
        
        self.assertTrue(abs(v1/v2 - 1) < 0.01)
        
    def assertBoundingBoxesEqualApproximately(self, bb1, bb2):
        
        self.assertValuesEqualApproximately(bb1.width, bb2.width)
        self.assertValuesEqualApproximately(bb1.height, bb2.height)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()