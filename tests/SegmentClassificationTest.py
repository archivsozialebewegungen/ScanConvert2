'''
Created on 06.04.2023

@author: michael
'''
import os

from PIL import Image, ImageShow
from parameterized import parameterized
import numpy as np

from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox, Segment, \
    SegmentType, BINARY_WHITE
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
    ["Text 5", "Margaretha_I_025.jpg", BoundingBox(312, 177, 1202, 208), SegmentType.TEXT],
    ["Text 6", "Margaretha_I_025.jpg", BoundingBox(390,1929,1130,1960), SegmentType.TEXT],
    ["Text 7", "Margaretha_I_025.jpg", BoundingBox(450,1967,1069,2005), SegmentType.TEXT],
    ["Text 8", "Margaretha_I_025.jpg", BoundingBox(1340,2091,1373,2117), SegmentType.TEXT],
    ["Photo 1", "Margaretha_I_025.jpg", BoundingBox(270, 633, 1243, 1881), SegmentType.PHOTO],
    ["Photo 2", "1982_original.tif", BoundingBox(1074,174,1818,663), SegmentType.PHOTO],
    ["Photo 3", "1982_original.tif", BoundingBox(1068,1215,1830,1740), SegmentType.PHOTO],
    ["Photo 4", "Margaretha_I_192.jpg", BoundingBox(294,474,1494,940), SegmentType.PHOTO],
    ["Photo 5", "Margaretha_I_025.jpg", BoundingBox(263,677,1258,1903), SegmentType.PHOTO],
    ["Photo 6", "haitzinger.jpg", BoundingBox(188,4561,990,4942), SegmentType.PHOTO],
    ["Drawing 1", "1982_original.tif", BoundingBox(204, 69, 963, 606), SegmentType.DRAWING],
    ["Drawing 2", "1982_original.tif", BoundingBox(204, 1029, 966, 1803), SegmentType.DRAWING],
    ["Drawing 3", "haitzinger.jpg", BoundingBox(239,968,1853,1985), SegmentType.DRAWING],
    # This will be classified wrongly, but it is better to leave it like that - no great
    # harm is done if an illustration like this gets dithered instead of thesholded than
    # the other way round
    ["Drawing 4", "haitzinger.jpg", BoundingBox(1905,944,3534,2054), SegmentType.DRAWING],
    ]

files = [
    ["Margaretha_I_025.jpg"],
    ["Margaretha_I_192.jpg"],
    ["1982_original.tif"],
    ["picture_detection.tif"],
    ["haitzinger.jpg"],
    ]

class SegmentClassificationTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service, self.ndarray_service)
        self.sorting_service = SegmentSorterService()
        self.classification_service = SegmentClassificationService(
            self.run_length_algorithm_service,
            self.binarization_service)
        self.segmentation_service = SimpleSegmentationService(
            self.sorting_service,
            self.line_removing_service,
            self.classification_service,
            self.run_length_algorithm_service,
            self.binarization_service,
            self.ndarray_service)

    @parameterized.expand(test_classifications)
    def testTextClassification1(self, description, filename, bounding_box, expected_type):

        print(description)
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))

        segment = Segment(bounding_box)
        segment_type = self.classification_service._classify_segment(segment, img)
        self.assertEqual(segment_type, expected_type)

    @parameterized.expand(files[3:4])
    def notestFullPage(self, filename):
        
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))
        segmented_page = self.segmentation_service.get_segmented_page(img)
        segmented_page.show_segments()
        #segmented_page.show_segments(SegmentType.UNKNOWN)
        #segmented_page.show_segments(SegmentType.TEXT)
        #segmented_page.show_segments(SegmentType.DRAWING)
        #segmented_page.show_segments(SegmentType.PHOTO)
        #segmented_page.show_segments(SegmentType.BORDER)
        
    def notest_signal_cross_correlation(self):
        
        segment = np.zeros((2,10), dtype=np.bool)
        self.assertEqual(self.run_length_algorithm_service.signal_cross_correlation(segment, 0, 1), 1)
        segment[1][:1] = BINARY_WHITE
        self.assertEqual(self.run_length_algorithm_service.signal_cross_correlation(segment, 0, 1), 0.8)
        segment[1][:9] = BINARY_WHITE
        self.assertEqual(self.run_length_algorithm_service.signal_cross_correlation(segment, 0, 1), -0.8)
        segment[1] = BINARY_WHITE
        self.assertEqual(self.run_length_algorithm_service.signal_cross_correlation(segment, 0, 1), -1)
        
