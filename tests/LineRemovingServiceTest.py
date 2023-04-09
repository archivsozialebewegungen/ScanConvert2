'''
Created on 06.04.2023

@author: michael
'''
import os

from PIL import Image, ImageShow
from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService
from Asb.ScanConvert2.PageSegmentationModule.Operations import BinarizationService, \
    RunLengthAlgorithmService, NdArrayService
from Base import BaseTest

ImageShow.register(ImageShow.EogViewer(), 0)

class LineRemovingServiceTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        
        self.img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", "picture_detection.tif"))
        self.binarization_service = BinarizationService()
        self.run_length_algorithm_service = RunLengthAlgorithmService()
        self.ndarray_service = NdArrayService()
        self.line_removing_service = LineRemovingService(self.run_length_algorithm_service,
                                                         self.ndarray_service)
        
    def testLineRemoving(self):
        
        bin_ndarray = self.binarization_service.binarize_otsu(self.img)
        bin_ndarray = self.line_removing_service.remove_lines(bin_ndarray)
        #Image.fromarray(bin_ndarray).show()
