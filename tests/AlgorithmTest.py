'''
Created on 16.01.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.Algorithms import AlgorithmModule, Algorithm,\
    ModeTransformationAlgorithm
import os
from PIL import Image

class AlgorithmTests(unittest.TestCase):
    
    def setUp(self):
        
        file_name = os.path.join(os.path.dirname(__file__), "Files", "AlgorithmTest", "algorithm-test.tif")            
        self.img = Image.open(file_name)
        injector_module = AlgorithmModule()
        self.algorithms = injector_module.algorithm_provider()
        
    def testCompleteness(self):
        """
        Checks that all algorithms have an implementation
        """
        for algo in Algorithm:
            self.assertIn(algo, self.algorithms)
            self.assertIsInstance(self.algorithms[algo], ModeTransformationAlgorithm)
            
    def testAllInModule(self):
        """
        Check that all algorithms are existing (ok, this is a stupid test)
        """

        for algo in self.algorithms.keys():
            self.assertIn(algo, Algorithm)

    def testNone(self):
        
        self.algorithms[Algorithm.NONE].transform(self.img).save(os.path.join("/", "tmp", "none.png"))

    def testGray(self):
        
        self.algorithms[Algorithm.GRAY].transform(self.img).save(os.path.join("/", "tmp", "gray.png"))
    
    def testGrayOnWhite(self):
        
        self.algorithms[Algorithm.GRAY_WHITE].transform(self.img).save(os.path.join("/", "tmp", "gray_on_white.png"))

    def testOtsu(self):
        
        self.algorithms[Algorithm.OTSU].transform(self.img).save(os.path.join("/", "tmp", "otsu.png"))
        
    def testSauvola(self):
        
        self.algorithms[Algorithm.SAUVOLA].transform(self.img).save(os.path.join("/", "tmp", "sauvola.png"))

    def testNiblack(self):
        
        self.algorithms[Algorithm.NIBLACK].transform(self.img).save(os.path.join("/", "tmp", "niblack.png"))

    def testFloydSteinberg(self):
        
        self.algorithms[Algorithm.FLOYD_STEINBERG].transform(self.img).save(os.path.join("/", "tmp", "floyd_steinberg.png"))

    def testBlackTextOnColor(self):
        
        self.algorithms[Algorithm.COLOR_PAPER_QUANTIZATION].transform(self.img).save(os.path.join("/", "tmp", "color_paper.png"))

    def testColorTextOnWhite(self):
        
        self.algorithms[Algorithm.COLOR_TEXT_QUANTIZATION].transform(self.img).save(os.path.join("/", "tmp", "color_text.png"))

    def testTwoColors(self):
        
        self.algorithms[Algorithm.TWO_COLOR_QUANTIZATION].transform(self.img).save(os.path.join("/", "tmp", "two_colors.png"))

    def testWhite(self):
        
        self.algorithms[Algorithm.WEISS].transform(self.img).save(os.path.join("/", "tmp", "white.png"))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()