'''
Created on 06.04.2023

@author: michael
'''
import os

from PIL import Image, ImageShow
from parameterized import parameterized

from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox, Segment, \
    SegmentType
from Asb.ScanConvert2.PageSegmentationModule.Operations import BinarizationService, \
    RunLengthAlgorithmService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.SegmentClassification import SegmentClassificationService
from Base import BaseTest
from Asb.ScanConvert2.PageSegmentationModule.SimpleSegmentation import SimpleSegmentationService
from Asb.ScanConvert2.PageSegmentationModule.SegmentSorter import SegmentSorterService
from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService


ImageShow.register(ImageShow.EogViewer(), 0)

test_classifications = [
    ["Text 1", "Margaretha_I_025.jpg", BoundingBox(121, 253, 1375, 589), SegmentType.TEXT],
    ["Text 2", "1982_original.tif", BoundingBox(1125,69,1824,132), SegmentType.TEXT],
    ["Text 3", "1982_original.tif", BoundingBox(1185,893,1235,918), SegmentType.TEXT],
    ["Text 4", "picture_detection.tif", BoundingBox(230,68,2148,314), SegmentType.TEXT],
    ["Photo 1", "Margaretha_I_025.jpg", BoundingBox(270, 633, 1243, 1881), SegmentType.PHOTO],
    ["Photo 2", "1982_original.tif", BoundingBox(1074,174,1818,663), SegmentType.PHOTO],
    ["Photo 3", "1982_original.tif", BoundingBox(1068,1215,1830,1740), SegmentType.PHOTO],
    ["Photo 4", "Margaretha_I_192.jpg", BoundingBox(294,474,1494,940), SegmentType.PHOTO],
    ["Drawing 1", "1982_original.tif", BoundingBox(204, 69, 963, 606), SegmentType.DRAWING],
    ["Drawing 2", "1982_original.tif", BoundingBox(204, 1029, 966, 1803), SegmentType.DRAWING],
    ]

files = [
    ["Margaretha_I_025.jpg"],
    ["Margaretha_I_192.jpg"],
    ["1982_original.tif"],
    ["picture_detection.tif"],
    ]

class SegmentSortingTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service, self.ndarray_service)
        self.sorter_service = SegmentSorterService()
        self.segmentation_service = SimpleSegmentationService(
            self.sorter_service,
            self.line_removing_service,
            self.run_length_algorithm_service,
            self.binarization_service,
            self.ndarray_service
            )
        self.segment_classification_service = SegmentClassificationService(
            self.run_length_algorithm_service,
            self.binarization_service)

    @parameterized.expand(test_classifications)
    def testTextClassification1(self, description, filename, bounding_box, expected_type):

        print(description)
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))

        segment = Segment(bounding_box)
        segment_type = self.segment_classification_service._classify_segment(segment, img)
        self.assertEqual(segment_type, expected_type)

    @parameterized.expand(files)
    def notestFullPage(self, filename):
        
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))
        segmented_page = self.segmentation_service.get_segmented_page(img)
        segmented_page = self.segment_classification_service.classify_segmented_page(segmented_page)
        segmented_page.show_segments()
        #segmented_page.show_segments(SegmentType.UNKNOWN)
        segmented_page.show_segments(SegmentType.TEXT)
        #segmented_page.show_segments(SegmentType.DRAWING)
        #segmented_page.show_segments(SegmentType.PHOTO)
        #segmented_page.show_segments(SegmentType.BORDER)
        
