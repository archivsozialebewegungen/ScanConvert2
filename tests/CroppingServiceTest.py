'''
Created on 03.08.2023

@author: michael
'''
from Base import BaseTest
import os
from Asb.ScanConvert2.CroppingService import CroppingService
from PIL import Image, ImageDraw


class Test(BaseTest):


    def setUp(self):
        super().setUp()
        self.service = CroppingService()
        self.test_filename = os.path.join(self.test_file_dir, "CroppingService", "cropping_test.tiff")

    def tearDown(self):
        pass


    def testContour(self):
        
        cropping_information = self.service.get_cropping_information(self.test_filename)
        self.assertEqual(int(cropping_information.rotation_angle * 100), -51)
        
        img = Image.open(self.test_filename)
        img = img.rotate(cropping_information.rotation_angle, Image.BICUBIC)
        #img1 = ImageDraw.Draw(img)  
        #img1.rectangle(cropping_information.bounding_box, fill ="#ffff33", outline ="red")
        img = img.crop(cropping_information.bounding_box)
        img.save("/tmp/test.tif")
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()