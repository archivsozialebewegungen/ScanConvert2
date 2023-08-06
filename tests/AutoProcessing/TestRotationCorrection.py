'''
Created on 20.05.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.AutoProcessing.CommonOperations import NdArrayService,\
    BinarizationService, ConstrainedRunLengthAlgorithmsService
from Asb.ScanConvert2.AutoProcessing.Services import RotationService
from AutoProcessing.TestMixin import TestMixin


class Test(unittest.TestCase, TestMixin):


    def setUp(self):
        
        self.service = RotationService(NdArrayService(), BinarizationService(), ConstrainedRunLengthAlgorithmsService())
        self.img = self.open_sample_file("Zeitungsausschnitte_001.jpg")


    def testAngleDetection(self):
        
        rotation_angle = self.service.determine_rotation(self.img)
        self.assertEqual(0.9, round(rotation_angle, 1))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()