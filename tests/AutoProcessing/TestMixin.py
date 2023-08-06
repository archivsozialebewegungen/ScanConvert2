'''
Created on 20.05.2023

@author: michael
'''
from PIL import Image
import os

class TestMixin(object):
    
    def open_sample_file(self, filename: str) -> Image:
        
        sample_dir = os.path.join(os.path.dirname(__file__), "SampleFiles")
        img_file_name = os.path.join(sample_dir, filename)
        return Image.open(img_file_name)