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
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService,\
    BinarizationService, NdArrayService, ImageStatisticsService
from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox,\
    SegmentType
from Asb.ScanConvert2.PageSegmentationModule.SimpleSegmentation import SimpleSegmentationService
import PIL
from PIL.ImageShow import EogViewer
from Asb.ScanConvert2.PageSegmentationModule.PavlidisZhouSegmentation import PavlidisZhouSegmentationService
from Asb.ScanConvert2.PageSegmentation import SegmentationService
from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService


PIL.ImageShow.register(EogViewer(), 0
                       )

test_images = [
        ["1982_original.tif", 2, BoundingBox(1071,175,1825,665)],
        ["1982_original_tilted.tif", 2, BoundingBox(1089,179,1854,689)],
        ["1982_original_strongly_tilted.tif", 2, BoundingBox(1071,175,1825,665)],
        ["Margaretha_I_025.jpg", 1, BoundingBox(267,624,1260,1903)],
        ["Margaretha_I_192.jpg", 1, BoundingBox(295,494,1497,941)],
        ["picture_detection_simple.tif", 1, BoundingBox(816,800,1537,1880)],
        ["picture_detection.tif", 1, BoundingBox(816,800,1537,1880)],
        ["mini.tif", 0, None],
        ["mini2.tif", 0, None],
        ["one_line.tif", 0, None],
        ["BlackBlock.tif", 0, None],
        ["single_c.tif", 0, None],
        ]

class PageSegmentationTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.binarization_service = BinarizationService()
        self.ndarray_service = NdArrayService()
        self.image_statistics_service = ImageStatisticsService()
        self.wws_segmentation_service = WahlWongCaseySegmentationService(
            self.run_length_algorithm_service,
            self.binarization_service,
            self.ndarray_service,
            self.image_statistics_service)
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service,
                                                         self.ndarray_service)
        self.simple_segmentation_service = SimpleSegmentationService(
            self.line_removing_service,
            self.run_length_algorithm_service,
            self.binarization_service,
            self.ndarray_service)
        self.pz_segmentation_service = PavlidisZhouSegmentationService(self.run_length_algorithm_service, self.binarization_service)

    @parameterized.expand(test_images[6:7])
    def no_test_wahl_wong_casey_segmentation(self, filename, no_of_pictures, bounding_box):
        """
        Images with index 2 and 6 do not work well with this algorithm
        """
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", filename)


        img = Image.open(self.test_file)
        segmented_page = self.wws_segmentation_service.get_segmented_page(img)
        segmented_page.show_segments(SegmentType.BORDER)
        photo_segments = segmented_page.photo_segments
        self.assertEqual(no_of_pictures, len(photo_segments))
        print(photo_segments[0].bounding_box)
        self.assertBoundingBoxesEqualApproximately(photo_segments[0].bounding_box, bounding_box)
    
    @parameterized.expand(test_images[2:3])
    def no_test_pavlidis_zhou_segmentation(self, filename, no_of_pictures, bounding_box):
        """
        Images with index 2 and 6 do not work well with this algorithm
        """
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", filename)


        img = Image.open(self.test_file)
        segmented_page = self.pz_segmentation_service.get_segmented_page(img)
        segmented_page.show_segments()
        photo_segments = segmented_page.photo_segments
        self.assertEqual(no_of_pictures, len(photo_segments))
        print(photo_segments[0].bounding_box)
        self.assertBoundingBoxesEqualApproximately(photo_segments[0].bounding_box, bounding_box)
    
    @parameterized.expand(test_images[6:7])
    def test_simple_segmentation(self, filename, no_of_pictures, bounding_box):
        
        self.test_file = os.path.join(self.test_file_dir, "PictureDetection", filename)

        img = Image.open(self.test_file)
        segmented_page = self.simple_segmentation_service.get_segmented_page(img)
        segmented_page.show_segments()
        #segmented_page.show_columns()
        photo_segments = segmented_page.photo_segments
        self.assertEqual(no_of_pictures, len(segmented_page.photo_segments))
        if no_of_pictures > 0:
            self.assertBoundingBoxesEqualApproximately(photo_segments[0].bounding_box, bounding_box)

    def assertValuesEqualApproximately(self, v1, v2):
        
        self.assertTrue(abs(v1/v2 - 1) < 0.01)
        
    def assertBoundingBoxesEqualApproximately(self, bb1, bb2):
        
        self.assertValuesEqualApproximately(bb1.width, bb2.width)
        self.assertValuesEqualApproximately(bb1.height, bb2.height)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()