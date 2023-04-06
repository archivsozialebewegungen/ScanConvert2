'''
Created on 02.11.2022

@author: michael
'''
import os
import tempfile

from fitz.fitz import Document
from injector import Injector

from Asb.ScanConvert2.Algorithms import AlgorithmModule, Algorithm,\
    BlackTextOnColor
from Asb.ScanConvert2.ScanConvertDomain import Scan
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Base import BaseTest
from Asb.ScanConvert2.ProjectGenerator import SortType
from PIL import Image

class ProjectServiceTest(BaseTest):
    
    def setUp(self):
        BaseTest.setUp(self)
        injector = Injector(AlgorithmModule)
        self.project_service = injector.get(ProjectService)

    def testProjectServiceDouble(self):

        project = self.project_service.load_project("/home/michael/scans/Ravensburg/test.scp")      
        #project.pages[0].main_region.mode_algorithm = Algorithm.OTSU
        #project.pages[1].main_region.mode_algorithm = Algorithm.COLOR_PAPER_QUANTIZATION
        #project.pages[2].main_region.mode_algorithm = Algorithm.COLOR_PAPER_QUANTIZATION
        #project.pages[3].main_region.mode_algorithm = Algorithm.OTSU
        project.project_properties.run_ocr = False
        project.project_properties.create_pdfa = False

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_file = os.path.join(tmp_dir, "test.pdf")
            self.project_service.export_pdf(project, pdf_file)
            document = Document(pdf_file)
            for page_no in range(0,9):
                page = document.load_page(page_no)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                #img.show("test")
                colors = img.getcolors()
                print(colors)

