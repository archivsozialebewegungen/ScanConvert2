'''
Created on 02.11.2022

@author: michael
'''
import os
import unittest

from injector import Injector

from Asb.ScanConvert2.PageGenerators import PageGeneratorsModule
from Asb.ScanConvert2.ScanConvertDomain import Scan, Projecttype, \
    Scantype, Algorithm
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Base import BaseTest


class PdfServiceTest(BaseTest):


    def testPdfServiceSingle(self):
        
        scans = []
        for i in range(1, 8):
            scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite%s.jpg" % i)))
        scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite8schraeg.jpg")))
        
        injector = Injector(PageGeneratorsModule())
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 Scantype.SINGLE,
                                                 Projecttype.PDF,
                                                 "/tmp/singletest")
        project_service.pdf_service.run_ocr = False
        project_service.run_project(project)

    def testPdfServiceDouble1(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite1.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite2_3.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite6_7.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite8schraeg.jpg")))
        
        injector = Injector(PageGeneratorsModule())
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 Scantype.DOUBLE,
                                                 Projecttype.PDF,
                                                 "/tmp/double1test")
        project_service.pdf_service.run_ocr = False
        project_service.run_project(project)

    def testPdfServiceDouble2(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite8_1.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite2_3.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite6_7.jpg")))
        
        injector = Injector(PageGeneratorsModule())
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 Scantype.DOUBLE,
                                                 Projecttype.PDF,
                                                 "/tmp/double2test")
        project_service.pdf_service.run_ocr = False
        project_service.run_project(project)

    def testPdfServiceDouble90(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite8_1.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite2_3.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite4_5.jpg")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite6_7.jpg")))
        
        injector = Injector(PageGeneratorsModule())
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 Scantype.DOUBLE_90,
                                                 Projecttype.PDF,
                                                 "/tmp/double90test",
                                                 Algorithm.SAUVOLA)
        project_service.pdf_service.run_ocr = False
        project_service.run_project(project)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPdfService']
    unittest.main()