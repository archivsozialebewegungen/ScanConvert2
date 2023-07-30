'''
Created on 30.07.2023

@author: michael
'''
import unittest
from Base import BaseTest
import tempfile
import os
from shutil import copyfile
from time import sleep
from Asb.ScanConvert2.ScanConvertServices import IPTCService


class Test(BaseTest):

    def setUp(self):
        super().setUp()
        self.tif_test_file_source = os.path.join(self.test_file_dir, "AlgorithmTest", "algorithm-test.tif")
        self.jpg_test_file_source = os.path.join(self.test_file_dir, "BgColorChange", "friedensforum_004.jpg")
        self.iptc_service = IPTCService()

    def testIPTCwriting(self):
        
        iptc_tags = {"1IPTC:Source": "Feministisches Archiv Freiburg",
                     "1IPTC:City": "Freiburg im Breisgau",
                     "1IPTC:SpecialInstructions": "Erstellt mit Mitteln des Bundesministeriums fuer Familie, Senioren, Frauen und Jugend",
                     "1IPTC:CatalogSets": "12.0.1: Anti-AKW- und Oekologiebewegung"}
        
        with tempfile.TemporaryDirectory(prefix="iptc") as temp_dir:

            test_file_tif = os.path.join(temp_dir, "test.tif") 
            test_file_jpg = os.path.join(temp_dir, "test.jpg") 
            copyfile(self.tif_test_file_source, test_file_tif)
            copyfile(self.jpg_test_file_source, test_file_jpg)
            self.iptc_service.write_iptc_tags(test_file_tif, iptc_tags)
            self.iptc_service.write_iptc_tags(test_file_jpg, iptc_tags)
            sleep(5000) 


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
