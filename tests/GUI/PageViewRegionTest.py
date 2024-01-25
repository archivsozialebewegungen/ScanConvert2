'''
Created on 24.01.2024

@author: michael
'''
import unittest
from PySide6.QtWidgets import QApplication
from injector import Injector
from Asb.ScanConvert2.Algorithms import AlgorithmModule
from Asb.ScanConvert2.GUI.Gui import Window
import sys
from PIL import Image
from Asb.ScanConvert2.ScanConvertDomain import Region
from PySide6.QtCore import QRect, QSize


class Test(unittest.TestCase):


    def setUp(self):
        
        self.app = QApplication(sys.argv)

        injector = Injector(AlgorithmModule)
        self.win = injector.get(Window)
        self.region = Region(50.0, 50.0, 200.0, 400.0)
        
        self.img_portait = Image.new('RGB',(2480,3508))
        self.img_landscape = Image.new('RGB',(3580,2480))


    def tearDown(self):
        
        del self.win
        del self.app


    def testRegionSelection(self):

        self.win.graphics_view.set_page(self.img_landscape)
        self.win.graphics_view.rubberBand.setGeometry(QRect(50, 50, 40, 30))
        self.win.graphics_view.region_cache = self.win.graphics_view._calculate_img_region()
        region = self.win.graphics_view.get_selected_region()
        
        self.win.graphics_view.show_region(region)
        geometry = self.win.graphics_view.rubberBand.geometry()
        self.assertEqual(QRect(50, 50, 40, 30), geometry)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()