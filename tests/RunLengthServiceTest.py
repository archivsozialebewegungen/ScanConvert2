'''
Created on 02.04.2023

@author: michael
'''
import os
import unittest

from PIL import Image, ImageShow

from Asb.ScanConvert2.PageSegmentationModule.Domain import BINARY_BLACK,\
    BINARY_WHITE
from Asb.ScanConvert2.PageSegmentationModule.Operations import BinarizationService, \
    RunLengthAlgorithmService
from Base import BaseTest
import numpy as np
from PIL.ImageShow import EogViewer
import time

ImageShow.register(EogViewer(), 0
                       )

class RunLengthAlgorithmTest(BaseTest):


    def setUp(self):
        super().setUp()
        
        filename =  os.path.join(self.test_file_dir, "PictureDetection", "1982_original.tif")
        self.run_length_service = RunLengthAlgorithmService()
        self.binarization_service = BinarizationService()
        self.img = Image.open(filename)
        self.bin_img = self.binarization_service.binarize_otsu(self.img)


    def tearDown(self):
        pass


    def notest0degrees(self):
        
        bin_copy1 = self.bin_img.copy()
        bin_copy2 = self.bin_img.copy()
        
        indirect_start = time.perf_counter()
        matrix = self.run_length_service.calculate_0_degrees_run_lengths(bin_copy2, BINARY_WHITE)
        bin_copy2[matrix < 30] = BINARY_BLACK
        indirect_end = time.perf_counter()
        
        direct_start = time.perf_counter()
        bin_copy1 = self.run_length_service.smear_horizontal(bin_copy1, 30, BINARY_BLACK)
        direct_end = time.perf_counter()

        print(f"Direct: {direct_end - direct_start:0.4f} sec.")
        print(f"Indirect: {indirect_end - indirect_start:0.4f} sec.")
        Image.fromarray(bin_copy1).show()
        Image.fromarray(bin_copy2).show()
        
    def test_find_vertical_lines(self):
        
        filename =  os.path.join(self.test_file_dir, "PictureDetection", "picture_detection.tif")
        img = Image.open(filename)
        bin_img = self.binarization_service.binarize_otsu(img)
        h_matrix = self.run_length_service.calculate_0_degrees_run_lengths(bin_img, BINARY_BLACK)
        v_matrix = self.run_length_service.calculate_90_degrees_run_lengths(bin_img, BINARY_BLACK)
        mask_v = np.zeros_like(bin_img)
        mask_v[v_matrix > 300] = BINARY_WHITE
        mask_v[h_matrix > 40] = BINARY_BLACK
        mask_h = np.zeros_like(bin_img)
        mask_h[h_matrix > 300] = BINARY_WHITE
        mask_h[v_matrix > 30] = BINARY_BLACK
        result = np.bitwise_or(mask_v, bin_img)
        result = np.bitwise_or(mask_h, result)
        
        #Image.fromarray(mask_v).show()
        Image.fromarray(result).show()
        
        
    def notest45degrees(self):
        
        matrix = self.run_length_service.calculate_45_degrees_run_lengths(self.bin_img, BINARY_WHITE)
        self.bin_img[matrix < 30] = BINARY_BLACK
        Image.fromarray(self.bin_img).show()

    def notest90degrees(self):
        
        matrix = self.run_length_service.calculate_90_degrees_run_lengths(self.bin_img, BINARY_WHITE)
        self.bin_img[matrix < 30] = BINARY_BLACK
        Image.fromarray(self.bin_img).show()

    def notest135degrees(self):
        
        matrix = self.run_length_service.calculate_135_degrees_run_lenghts(self.bin_img, BINARY_WHITE)
        self.bin_img[matrix < 30] = BINARY_BLACK
        Image.fromarray(self.bin_img).show()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()