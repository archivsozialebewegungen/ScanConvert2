'''
Created on 02.11.2022

@author: michael
'''
import os
import unittest

from injector import Injector

from Asb.ScanConvert2.ScanConvertDomain import Scan, \
    Scantype, Algorithm, SortType
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Base import BaseTest
from fitz.fitz import Document
import tempfile

numbers_as_text = {
    1: "eins",
    2: "zwei",
    3: "drei",
    4: "vier",
    5: "fünf",
    6: "sechs",
    7: "sieben",
    8: "acht"
    }
class PdfServiceTest(BaseTest):

    def assert_project(self, project_service, project):

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_file = os.path.join(tmp_dir, "test.pdf")
            project_service.export_pdf(project, pdf_file)
            #project_service.export_pdf(project, "/tmp/tmp.pdf")
            document = Document(pdf_file)
            for i in range(0,8):
                self.assertIn(numbers_as_text[i+1], document.get_page_text(i))

    def notestPdfServiceSingle(self):
        
        scans = []
        for i in range(1, 9):
            scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite%s.png" % i)))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 1,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)
        
    def notestPdfServiceDouble1(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite6_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Singlefiles", "Seite8.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)
        
    def notestPdfServiceDouble2(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def notestPdfServiceDouble270(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 270,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def notestPdfServiceDouble180(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 180,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def notestPdfServiceDouble90(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 90,
                                                 False,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def testPdfServiceDoublealternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 True,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def notestPdfServiceDouble90alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 90,
                                                 True,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def testPdfServiceDouble180alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles180", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 True,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)

    def testPdfServiceDouble270alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles270", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Doublefiles90", "Seite6_7.png")))
        
        injector = Injector()
        project_service = injector.get(ProjectService)
        project = project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 270,
                                                 True,
                                                 Algorithm.OTSU)

        self.assert_project(project_service, project)
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPdfService']
    unittest.main()