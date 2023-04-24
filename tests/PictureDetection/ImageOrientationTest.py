'''
Created on 06.04.2023

@author: michael
'''
import os

from PIL import Image, ImageShow
from parameterized import parameterized

from Base import BaseTest
from Asb.ScanConvert2.PictureDetector.HelperServices import OrientationCorrectionService

ImageShow.register(ImageShow.EogViewer(), 0)

corrections = {0: 0,
               90: 270,
               180: 180,
               270: 90}

rotations = {90: Image.ROTATE_90,
             180: Image.ROTATE_180,
             270: Image.ROTATE_270}

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
        
        self.orientation_service = OrientationCorrectionService()

    @parameterized.expand(files)
    def testCorrectionAngles(self, filename, angle):
        
        img = Image.open(os.path.join(self.test_file_dir, "PictureDetection", filename))
        if angle != 0:
            transposed = img.transpose(rotations[angle])
        else:
            transposed = img
        self.assertEqual(self.orientation_service._determine_correction(transposed), corrections[angle])

