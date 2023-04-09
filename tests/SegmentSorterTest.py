'''
Created on 06.04.2023

@author: michael
'''
import os

from PIL import Image, ImageShow

from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService
from Asb.ScanConvert2.PageSegmentationModule.Operations import BinarizationService, \
    RunLengthAlgorithmService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.SimpleSegmentation import SimpleSegmentationService
from Base import BaseTest
from Asb.ScanConvert2.PageSegmentationModule.SegmentSorter import SegmentSorterService
from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox

ImageShow.register(ImageShow.EogViewer(), 0)


class SegmentSortingTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", "picture_detection.tif"))
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service,
                                                         self.ndarray_service)
        self.sorting_service = SegmentSorterService()
        self.simple_segmentation_service = SimpleSegmentationService(
            self.sorting_service,
            self.line_removing_service,
                                                                     self.run_length_algorithm_service,
                                                                     self.binarization_service,
                                                                     self.ndarray_service)
        
    def testSegmentSorting(self):

        segmented_page = self.simple_segmentation_service.get_segmented_page(self.img)
        segmented_page.show_segments()

    def notest_intersecting(self):
        
        bb1 = BoundingBox(10, 10, 40, 40)
        bb2 = BoundingBox(5, 5, 60, 60)
        self.assertTrue(bb1.intersects_with(bb2))
        self.assertTrue(bb2.intersects_with(bb1))
