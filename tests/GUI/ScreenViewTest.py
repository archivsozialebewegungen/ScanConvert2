'''
Created on 28.01.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.GUI.PageView import PageViewBase
from Asb.ScanConvert2.ScanConvertDomain import Region

class ScreenViewStub(PageViewBase):
    
    def __init__(self,
                 img_width: int, 
                 img_height: int,
                 ratio: int,
                 x_offset: int,
                 y_offset: int):
        
        self.img_width = img_width
        self.img_height = img_height
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.ratio = ratio
        
    def set_screen_img_selection(self, x, y, width, height):
        
        self.screen_selection = (x + self.x_offset, y + self.y_offset, width, height)
        
    def _get_screen_selection(self):
    
        return self.screen_selection
    
    def _get_page_img_size(self):

        return (self.img_width, self.img_height)

    def _get_screen_img_size(self):

        return(round(self.img_width / self.ratio), round(self.img_height / self.ratio))    

    def _get_offsets(self):
        return (self.x_offset, self.y_offset)

class Test(unittest.TestCase):


    def testSimpleRegion(self):
        
        stub = ScreenViewStub(400, 400, 2.0, 40, 0)
        stub.set_screen_img_selection(10, 10, 40, 40)
        
        region = stub._calculate_img_region()
        self.assertEqual(round(region.x), 20)
        self.assertEqual(round(region.y), 20)
        self.assertEqual(round(region.width), 80)
        self.assertEqual(round(region.height), 80)

    def testComplicatedRegion(self):
        
        stub = ScreenViewStub(3458, 2266, 1.732, 60, 0)
        stub.set_screen_img_selection(78, 22, 148, 64)
        
        region = stub._calculate_img_region()
        screen_selection = stub._calculate_screen_selection(region)
        self.assertEqual(
            (round(screen_selection[0]),
             round(screen_selection[1]),
             round(screen_selection[2]),
             round(screen_selection[3])),
            (78 + stub.x_offset, 22 + stub.y_offset, 148, 64))

    def testRoundTripRegion(self):
        
        stub = ScreenViewStub(3467, 2244, 1.732, 0, 80)

        x = 55
        y = 87
        width = 455
        height = 1235
        
        screen_selection = stub._calculate_screen_selection(Region(x, y, width, height))
        stub.set_screen_img_selection(screen_selection[0] - stub.x_offset,
                                      screen_selection[1] - stub.y_offset,
                                      screen_selection[2],
                                      screen_selection[3])
        region = stub._calculate_img_region()
        
        self.assertEqual(round(region.x), x)
        self.assertEqual(round(region.y), y)
        self.assertEqual(round(region.width), width)
        self.assertEqual(round(region.height), height)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()