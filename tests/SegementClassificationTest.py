'''
Created on 06.04.2023

@author: michael
'''
from Base import BaseTest
from PIL import Image
import os
from Asb.ScanConvert2.PageSegmentationModule.Operations import BinarizationService,\
    RunLengthAlgorithmService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.Domain import BINARY_BLACK
from Asb.ScanConvert2.PageSegmentationModule.SimpleSegmentation import SimpleSegment,\
    ContourClassificationService
import cv2

class SegmentClassificationServiceTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", "picture_detection.tif"))
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.classification_service = ContourClassificationService(self.run_length_algorithm_service)

    def testProjectServiceDouble(self):
        
        bin_ndarray = self.binarization_service.binarize_otsu(self.img)
        #smeared_ndarray = self.run_length_algorithm_service.smear_horizontal(bin_ndarray, 30, BINARY_BLACK)
        smeared_ndarray_gray = self.ndarray_service.convert_binary_to_inverted_gray(bin_ndarray)
        contours, hierarchy = cv2.findContours(smeared_ndarray_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        segments = []
        for idx in range(0, len(contours)):
            segments.append(SimpleSegment(idx, contours[idx], hierarchy[0][idx], contours))
        for segment in segments:
            segment.all_segments = segments
        segments.sort(key=lambda x: x.size, reverse=True)
        assert(segments[0].size > segments[1].size)
        
        self.classification_service.classify_segment(self.img, segments[0])
 
