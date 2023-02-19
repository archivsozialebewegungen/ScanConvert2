'''
Created on 16.01.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.Algorithms import AlgorithmModule, Algorithm,\
    ModeTransformationAlgorithm, WHITE, AlgorithmHelper
import os
from PIL import Image
from _ast import Or

RUST_BACKGROUND = (155, 112, 96)
ORIGINAL_BACKGROUND = (114, 130, 149)
ORIGINAL_FOREGROUND = (29, 37, 50)

class AlgorithmTests(unittest.TestCase):
    
    def setUp(self):
        
        file_name = os.path.join(os.path.dirname(__file__), "SampleFiles", "AlgorithmTest", "algorithm-test.png")            
        self.img = Image.open(file_name)
        injector_module = AlgorithmModule()
        self.algorithms = injector_module.algorithm_provider()
        self.helper = AlgorithmHelper()
        self.result = None
        
    def tearDown(self):
        
        if self.result is not None:
            self.assertEqual(round(self.result[0].info['dpi'][0]), 300)
            self.assertEqual(round(self.result[0].info['dpi'][1]), 300)
        
    def get_colors(self, img: Image) -> []:
        
        return self.helper.get_colors(img)
    
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
        self.result[0].save(os.path.join("/", "tmp", "none.png"))

    def testGray(self):
        
        self.result = self.algorithms[Algorithm.GRAY].transform(self.img)
        self.result[0].save(os.path.join("/", "tmp", "gray.png"))
    
    def testGrayOnWhite(self):
        
        self.result = self.algorithms[Algorithm.GRAY_WHITE].transform(self.img)
        self.result[0].save(os.path.join("/", "tmp", "gray_on_white.png"))
        
    def testGrayOnColor(self):
        
        self.result = self.algorithms[Algorithm.GRAY_WHITE].transform(self.img, RUST_BACKGROUND)
        self.result[0].save(os.path.join("/", "tmp", "gray_on_color.png"))

    def testMissingResolution(self):

        file_name = os.path.join(os.path.dirname(__file__), "SampleFiles", "AlgorithmTest", "algorithm-test.pnm")            
        img = Image.open(file_name)

        self.result = self.algorithms[Algorithm.OTSU].transform(img)
        self.result[0].save(os.path.join("/", "tmp", "otsu.png"))

    def testOtsu(self):
        
        result = self.algorithms[Algorithm.OTSU].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "otsu.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn((0,0,0), colors)
        self.assertIn(WHITE, colors)
        
    def testOtsuWithBackground(self):
        
        result = self.algorithms[Algorithm.OTSU].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "otsu_backgound.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(RUST_BACKGROUND, colors)
        self.assertIn((0,0,0), colors)

    def testSauvola(self):
        
        result = self.algorithms[Algorithm.SAUVOLA].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "sauvola.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn((0,0,0), colors)

    def testSauvolaWithBackground(self):
        
        result = self.algorithms[Algorithm.SAUVOLA].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "sauvola_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(RUST_BACKGROUND, colors)
        self.assertIn((0,0,0), colors)

    def testFloydSteinberg(self):
        
        result = self.algorithms[Algorithm.FLOYD_STEINBERG].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "floyd_steinberg.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn((0,0,0), colors)
        self.assertIn(WHITE, colors)

    def testFloydSteinbergWithBackground(self):
        
        result = self.algorithms[Algorithm.FLOYD_STEINBERG].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "floyd_steinberg_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(RUST_BACKGROUND, colors)
        self.assertIn((0,0,0), colors)

    def testBlackTextOnColor(self):
        
        result = self.algorithms[Algorithm.COLOR_PAPER_QUANTIZATION].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "color_paper.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(ORIGINAL_BACKGROUND, colors)
        self.assertIn((0,0,0), colors)

    def testBlackTextOnColorWithBackground(self):
        
        result = self.algorithms[Algorithm.COLOR_PAPER_QUANTIZATION].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "color_paper_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(RUST_BACKGROUND, colors)
        self.assertIn((0,0,0), colors)

    def testColorTextOnWhite(self):
        
        result = self.algorithms[Algorithm.COLOR_TEXT_QUANTIZATION].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "color_text.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(ORIGINAL_FOREGROUND, colors)
        self.assertIn(WHITE, colors)

    def testColorTextOnWhiteWithBackground(self):
        
        result = self.algorithms[Algorithm.COLOR_TEXT_QUANTIZATION].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "color_text_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(ORIGINAL_FOREGROUND, colors)
        self.assertIn(RUST_BACKGROUND, colors)

    def testTwoColors(self):
        
        result = self.algorithms[Algorithm.TWO_COLOR_QUANTIZATION].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "two_colors.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertIn(ORIGINAL_FOREGROUND, colors)
        self.assertIn(ORIGINAL_BACKGROUND, colors)

    def testTwoColorsWithBackground(self):
        
        result = self.algorithms[Algorithm.TWO_COLOR_QUANTIZATION].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "two_colors_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 2)
        self.assertTrue(self.helper.colors_are_similar(ORIGINAL_FOREGROUND, colors[0]) or 
                        self.helper.colors_are_similar(ORIGINAL_FOREGROUND, colors[1]))
        self.assertTrue(self.helper.colors_are_similar(RUST_BACKGROUND, colors[0]) or 
                        self.helper.colors_are_similar(RUST_BACKGROUND, colors[1]))

    def testErase(self):
        
        result = self.algorithms[Algorithm.ERASE].transform(self.img)
        result[0].save(os.path.join("/", "tmp", "white.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 1)
        self.assertIn(WHITE, colors)
        
    def testEraseWithBackground(self):
        
        result = self.algorithms[Algorithm.ERASE].transform(self.img, RUST_BACKGROUND)
        result[0].save(os.path.join("/", "tmp", "white_background.png"))
        colors = self.get_colors(result[0])
        self.assertEqual(len(colors), 1)
        self.assertIn(RUST_BACKGROUND, colors)
        
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