'''
Created on 01.11.2022

@author: michael
'''
import unittest
import os


class BaseTest(unittest.TestCase):


    def setUp(self):
        
        self.test_file_dir = os.path.join(os.path.dirname(__file__), "Files")

