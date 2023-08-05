'''
Created on 05.08.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.ScanConvertDomain import Scan
from Base import BaseTest
import os
from Asb.ScanConvert2.ProjectGenerator import ProjectGenerator, SortType
from injector import Injector
from Asb.ScanConvert2.ScanConvertServices import DDFService, TiffService
from Asb.ScanConvert2.Algorithms import AlgorithmImplementations,\
    AlgorithmModule


class Test(BaseTest):


    def setUp(self):
        
        super().setUp()
        
        filedir = os.path.join(self.test_file_dir, "Double090")
        
        scans = [
            Scan(os.path.join(filedir, "Seite8_1.png")),
            Scan(os.path.join(filedir, "Seite2_7.png")),
            Scan(os.path.join(filedir, "Seite6_3.png")),
            Scan(os.path.join(filedir, "Seite4_5.png")),
        ]
        
        injector = Injector([AlgorithmModule])
        self.ddf_service = injector.get(DDFService)
        project_generator = injector.get(ProjectGenerator)
        self.project = project_generator.scans_to_project(
                    scans=scans,
                    pages_per_scan=2,
                    sort_type=SortType.SHEET,
                    scan_rotation=90,
                    rotation_alternating=False)
        self.project.metadata.ddf_prefix ="ddftest"


    def tearDown(self):
        pass


    def testDDFExportIntegration(self):
        
        self.ddf_service.create_ddf_file_archive(self.project, os.path.join("/", "tmp", "ddf_test"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()