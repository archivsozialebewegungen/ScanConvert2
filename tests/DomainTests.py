'''
Created on 11.02.2023

@author: michael
'''
import unittest
from Base import BaseTest
from Asb.ScanConvert2.ScanConvertDomain import Scan, Page, Region, Project
import os


class TestProject(BaseTest):


    def setUp(self):
        
        super().setUp()
        scan = Scan(os.path.join(self.test_file_dir, "Single000", "Seite1.png"))
        page = Page(scan, Region(0, 0, scan.width, scan.height))
        self.project = Project((page,))

    def testNameI(self):
        self.assertEqual(
            self.project.proposed_pdf_file,
            os.path.join(self.test_file_dir, "Single000", "Seite.pdf")
            )

    def testNameII(self):
        
        self.project.pages[0].scan.filename = "/tmp/test-00004.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/test.pdf"
            )

    def testNameIII(self):
        
        self.project.pages[0].scan.filename = "/tmp/test.test.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/test.test.pdf"
            )

    def testNameIV(self):
        
        self.project.pages[0].scan.filename = "/tmp/test.0004test.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/test.0004test.pdf"
            )

    def testNameV(self):
        
        self.project.pages[0].scan.filename = "/tmp/test._0004.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/test..pdf"
            )

    def testNameVI(self):
        
        self.project.pages[0].scan.filename = "/tmp/0004.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/.pdf"
            )

    def testNameVII(self):
        
        self.project.pages[0].scan.filename = "/tmp/test-0004.gif"
        self.assertEqual(
            self.project.proposed_pdf_file,
            "/tmp/test.pdf"
            )

    def testNameVIII(self):
        
        self.project.pages[0].scan.filename = "/tmp/test-0004.gif"
        self.assertEqual(
            self.project.proposed_zip_file,
            "/tmp/test.zip"
            )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()