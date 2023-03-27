'''
Created on 22.03.2023

@author: michael
'''
import unittest
import numpy as np


class NumpyTest(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_adressing(self):
        
        a = np.array([[1, 2, 2, 4],
                      [5, 6, 7, 8],
                      [9, 10, 11, 12],
                      [13,14, 15, 16]])
        
        a[1:3,1:3] = 17
        
    def test_reate_array(self):
        
        a = np.ones((2,3))
        print(a)
        
        print(a)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()