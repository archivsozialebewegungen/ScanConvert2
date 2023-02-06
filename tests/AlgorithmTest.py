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
        
        file_name = os.path.join(os.path.dirname(__file__), "SampleFiles", "AlgorithmTest", "algorithm-test.png")            
        self.img = Image.open(file_name)
        injector_module = AlgorithmModule()
        self.algorithms = injector_module.algorithm_provider()
        self.result = None
        
    def tearDown(self):
        
        if self.result is not None:
            self.assertEqual(round(self.result.info['dpi'][0]), 300)
            self.assertEqual(round(self.result.info['dpi'][1]), 300)
        
    def testCompleteness(self):
        """
        Checks that all algorithms have an implementation
        """
        for algo in Algorithm:
            self.assertIn(algo, self.algorithms)
            self.assertIsInstance(self.algorithms[algo], ModeTransformationAlgorithm)
            
    def testTexts(self):
        """
        Checks that wie have a string description for every
        algorithm
        """
        
        for algo in Algorithm:
            string_value = "%s" % algo
            self.assertTrue(len(string_value) > 0)
            
    def testAllInModule(self):
        """
        Check that all algorithms are existing (ok, this is a stupid test)
        """

        for algo in self.algorithms.keys():
            self.assertIn(algo, Algorithm)

    def testNone(self):
        
        self.result = self.algorithms[Algorithm.NONE].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "none.png"))

    def testGray(self):
        
        self.result = self.algorithms[Algorithm.GRAY].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "gray.png"))
    
    def testGrayOnWhite(self):
        
        self.result = self.algorithms[Algorithm.GRAY_WHITE].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "gray_on_white.png"))
        
    def testMissingResolution(self):

        file_name = os.path.join(os.path.dirname(__file__), "SampleFiles", "AlgorithmTest", "algorithm-test.pnm")            
        img = Image.open(file_name)

        self.result = self.algorithms[Algorithm.OTSU].transform(img)
        self.result.save(os.path.join("/", "tmp", "otsu.png"))

    def testOtsu(self):
        
        self.result = self.algorithms[Algorithm.OTSU].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "otsu.png"))
        
    def testSauvola(self):
        
        self.result = self.algorithms[Algorithm.SAUVOLA].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "sauvola.png"))

    def notestNiblack(self):
        
        self.result = self.algorithms[Algorithm.NIBLACK].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "niblack.png"))

    def testFloydSteinberg(self):
        
        self.result = self.algorithms[Algorithm.FLOYD_STEINBERG].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "floyd_steinberg.png"))

    def testBlackTextOnColor(self):
        
        self.result = self.algorithms[Algorithm.COLOR_PAPER_QUANTIZATION].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "color_paper.png"))

    def testColorTextOnWhite(self):
        
        self.result = self.algorithms[Algorithm.COLOR_TEXT_QUANTIZATION].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "color_text.png"))

    def testTwoColors(self):
        
        self.result = self.algorithms[Algorithm.TWO_COLOR_QUANTIZATION].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "two_colors.png"))

    def testWhite(self):
        
        self.result = self.algorithms[Algorithm.WEISS].transform(self.img)
        self.result.save(os.path.join("/", "tmp", "white.png"))
        
    def testParentClass(self):
        
        exception_raised = False
        try:
            ModeTransformationAlgorithm().transform(self.img)
        except Exception:
            exception_raised = True
        self.assertTrue(exception_raised)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()