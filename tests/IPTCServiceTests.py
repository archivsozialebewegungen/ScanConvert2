'''
Created on 30.07.2023

@author: michael
'''
import unittest
from Base import BaseTest
import tempfile
import os
from shutil import copyfile
from Asb.ScanConvert2.ScanConvertServices import IPTCService
from iptcinfo3 import IPTCInfo

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
            tiff_info = IPTCInfo(test_file_tif)
            jpg_info = IPTCInfo(test_file_jpg)
            self.assertEqual(b'Feministisches Archiv Freiburg', tiff_info["source"])
            self.assertEqual(b'Freiburg im Breisgau', tiff_info["city"])
            self.assertEqual(b'Erstellt mit Mitteln des Bundesministeriums fuer Familie, Senioren, Frauen und Jugend', tiff_info["special instructions"])
            self.assertEqual(b'12.0.1: Anti-AKW- und Oekologiebewegung', tiff_info[255])
            self.assertEqual(b'Feministisches Archiv Freiburg', jpg_info["source"])
            self.assertEqual(b'Freiburg im Breisgau', jpg_info["city"])
            self.assertEqual(b'Erstellt mit Mitteln des Bundesministeriums fuer Familie, Senioren, Frauen und Jugend', jpg_info["special instructions"])
            self.assertEqual(b'12.0.1: Anti-AKW- und Oekologiebewegung', jpg_info[255])

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
