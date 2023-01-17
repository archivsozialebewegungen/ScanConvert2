'''
Created on 16.01.2023

@author: michael
'''
import unittest
from Asb.ScanConvert2.ScanConvertDomain import Algorithm


class AlgorithmClassTest(unittest.TestCase):


    def testAlgorithmClass(self):
        
        self.assertEqual("SW Otsu (Text gleichmäßig)", "%s" % Algorithm.OTSU)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()