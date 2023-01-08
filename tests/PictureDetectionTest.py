'''
Created on 06.01.2023

@author: michael
'''
from Base import BaseTest
from Asb.ScanConvert2.PictureDetector import PictureDetector
from PIL import Image
import os

class PictureDetectionTest(BaseTest):

    def testFile1(self):
        
        self.detector = PictureDetector()
        img = Image.open(os.path.join(self.test_file_dir, "picture_detection.tif"))
        for picture in self.detector.find_pictures(img):
            blank = Image.new("1", (picture[2]-picture[0], picture[3]-picture[1]), color=0)
            img.paste(blank, (picture[0], picture[1]))
        img.save("/tmp/test.png")