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
from Asb.ScanConvert2.PageSegmentationModule.OrientationDetector import OrientationDetectionService,\
    rotations


ImageShow.register(ImageShow.EogViewer(), 0)
corrections = {0: 0,
               90: 270,
               180: 180,
               270: 90}


files = [
    ["Margaretha_I_025.jpg", 0],
    ["Margaretha_I_192.jpg", 0],
    ["1982_original_strongly_tilted.tif", 0],
    ["picture_detection.tif", 0],
    ["haitzinger.jpg", 0],
    ["Margaretha_I_025.jpg", 90],
    ["Margaretha_I_192.jpg", 90],
    ["1982_original_strongly_tilted.tif", 90],
    ["picture_detection.tif", 90],
    ["haitzinger.jpg", 90],
    ["Margaretha_I_025.jpg", 180],
    ["Margaretha_I_192.jpg", 180],
    ["1982_original_strongly_tilted.tif", 180],
    ["picture_detection.tif", 180],
    ["haitzinger.jpg", 180],
    ["Margaretha_I_025.jpg", 270],
    ["Margaretha_I_192.jpg", 270],
    ["1982_original_strongly_tilted.tif", 270],
    ["picture_detection.tif", 270],
    ["haitzinger.jpg", 270],
    ]

class SegmentClassificationTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service, self.ndarray_service)
        self.sorting_service = SegmentSorterService()
        self.orientation_service = OrientationDetectionService()

    @parameterized.expand(files)
    def notestCorrectionAngles(self, filename, angle):
        
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))
        if angle != 0:
            transposed = img.transpose(rotations[angle])
        else:
            transposed = img
        self.assertEqual(self.orientation_service._determine_correction(transposed), corrections[angle])

    @parameterized.expand(files)
    def testCorrections(self, filename, angle):
        
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))
        if angle != 0:
            transposed = img.transpose(rotations[angle])
        else:
            transposed = img
        self.orientation_service.correct_orientation(transposed).show()
