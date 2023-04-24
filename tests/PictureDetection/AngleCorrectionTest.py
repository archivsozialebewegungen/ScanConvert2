'''
Created on 06.04.2023

@author: michael
'''
from Base import BaseTest
import os
from PIL import Image
from Asb.ScanConvert2.PictureDetector.HelperServices import AngleCorrectionService,\
    BinarizationService, SmearingService, NdArrayService

class RotationAngleCorrectionTest(BaseTest):
    
    def setUp(self):
        super().setUp()

    def test_angle_correction(self):
        
        filename = os.path.join(self.test_file_dir, "PictureDetection", "1982_original_strongly_tilted.tif")
        img = Image.open(filename)
        service = AngleCorrectionService(BinarizationService(), SmearingService(), NdArrayService())
        img = service.correct_angle(img)
        img.show()
                                