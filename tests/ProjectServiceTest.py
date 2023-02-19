'''
Created on 02.11.2022

@author: michael
'''
import os
import tempfile
import unittest

from fitz.fitz import Document
from injector import Injector

from Asb.ScanConvert2.Algorithms import AlgorithmModule
from Asb.ScanConvert2.ScanConvertDomain import Scan
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Base import BaseTest
from Asb.ScanConvert2.ProjectGenerator import SortType


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
class ProjectServiceTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        injector = Injector(AlgorithmModule)
        self.project_service = injector.get(ProjectService)

    def assert_project(self, project_service, project):

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_file = os.path.join(tmp_dir, "test.pdf")
            project_service.export_pdf(project, pdf_file)
            #project_service.export_pdf(project, "/tmp/tmp.pdf")
            document = Document(pdf_file)
            for i in range(0,8):
                self.assertIn(numbers_as_text[i+1], document.get_page_text(i))

    def testProjectServiceSingle(self):
        
        scans = []
        for i in range(1, 9):
            scans.append(Scan(os.path.join(self.test_file_dir, "Single000", "Seite%s.png" % i)))
        
        project = self.project_service.create_project(scans,
                                                 1,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 False)

        self.assert_project(self.project_service, project)
        
    def testProjectServiceSingle90(self):
        
        scans = []
        for i in range(1, 9):
            scans.append(Scan(os.path.join(self.test_file_dir, "Single090", "Seite%s.png" % i)))
        
        project = self.project_service.create_project(scans,
                                                 1,
                                                 SortType.STRAIGHT,
                                                 90,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSingle180(self):
        
        scans = []
        for i in range(1, 9):
            scans.append(Scan(os.path.join(self.test_file_dir, "Single180", "Seite%s.png" % i)))
        
        project = self.project_service.create_project(scans,
                                                 1,
                                                 SortType.STRAIGHT,
                                                 180,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSingle270(self):
        
        scans = []
        for i in range(1, 9):
            scans.append(Scan(os.path.join(self.test_file_dir, "Single270", "Seite%s.png" % i)))
        
        project = self.project_service.create_project(scans,
                                                 1,
                                                 SortType.STRAIGHT,
                                                 270,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceMixed(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Single000", "Seite1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite6_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Single000", "Seite8.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT,
                                                 0,
                                                 False)

        self.assert_project(self.project_service, project)
        
    def testProjectServiceDouble(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 0,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble270(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 270,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble180(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 180,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble090(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 90,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceDoublealternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 0,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble090alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 90,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble180alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 0,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceDouble270alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite2_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite6_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.STRAIGHT_WITH_TITLE,
                                                 270,
                                                 True)

        self.assert_project(self.project_service, project)


    def testProjectServiceSheets000(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 0,
                                                 False)

        self.assert_project(self.project_service, project)
        
    def testProjectServiceSheets090(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 90,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheets180(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 180,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheets270(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 270,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheets000alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 0,
                                                 True)

        self.assert_project(self.project_service, project)
        
    def testProjectServiceSheets090alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 90,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheets180alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 180,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheets270alternating(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite2_7.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite4_5.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET,
                                                 270,
                                                 True)

        self.assert_project(self.project_service, project)

    def testProjectServiceRectoFirstSheets000(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double000", "Seite2_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET_ALL_FRONT_ALL_BACK,
                                                 0,
                                                 False)

        self.assert_project(self.project_service, project)
        
    def testProjectServiceSheetsRectoFirst090(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double090", "Seite2_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET_ALL_FRONT_ALL_BACK,
                                                 90,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheetsRectoFirst180(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double180", "Seite2_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET_ALL_FRONT_ALL_BACK,
                                                 180,
                                                 False)

        self.assert_project(self.project_service, project)

    def testProjectServiceSheetsRectoFirst270(self):
        
        scans = []
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite8_1.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite6_3.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite4_5.png")))
        scans.append(Scan(os.path.join(self.test_file_dir, "Double270", "Seite2_7.png")))
        
        project = self.project_service.create_project(scans,
                                                 2,
                                                 SortType.SHEET_ALL_FRONT_ALL_BACK,
                                                 270,
                                                 False)

        self.assert_project(self.project_service, project)

if __name__ == "__main__":
    unittest.main()