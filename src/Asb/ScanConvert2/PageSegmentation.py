'''
Created on 19.02.2023

@author: michael
'''
from enum import Enum

from PIL import Image, ImageShow
from numpy.core._multiarray_umath import ndarray
from skimage.filters.thresholding import threshold_otsu

import numpy as np
import cv2

ImageShow.register(ImageShow.EogViewer, -1)

BLACK = False
WHITE = True

class SegmentType(Enum):
    
    TEXT = 1
    PHOTO = 2
    DRAWING = 3

class Segment(object):
    
    def __init__(self, x:int, y:int, width:int, height:int, segment_type: SegmentType):
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.segment_type = segment_type


class PageSegmentor(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    def find_segments(self, img: Image) -> []:
        
        segments = []
        bin_img = self.binarize(img)
        self.show_bin_img(bin_img)
        hor_smeared = self.smear_horizontal(bin_img, 250)
        self.show_bin_img(hor_smeared)
        ver_smeared = self.smear_vertical(bin_img, 150)
        self.show_bin_img(ver_smeared)
        combined = np.logical_or(hor_smeared, ver_smeared)
        final = self.smear_horizontal(combined, 25)
        self.show_bin_img(final)
        return segments
        
    def binarize(self, img: Image) -> ndarray:
        
        in_array = np.asarray(img.convert("L"))
        mask = threshold_otsu(in_array)
        return in_array > mask
    
    def smear_vertical(self, bin_img: ndarray, constraint: int):
        
        smeared_img = self.smear_horizontal(np.rot90(bin_img, -1), constraint)
        return np.rot90(smeared_img)

    def smear_horizontal(self, bin_img: ndarray, constraint: int):
        
        height = bin_img.shape[0]
        width = bin_img.shape[1]
        smeared_img = bin_img.copy()
        for row_idx in range(0, height):
            if row_idx % 10 == 0:
                print(row_idx)
            line = bin_img[row_idx]
            col_idx = 0
            last_black = -1
            while col_idx < width:
                if line[col_idx] == BLACK:
                    whites = col_idx - last_black
                    if whites > 0 and whites < constraint:
                        smeared_img[row_idx, last_black +1:col_idx] = BLACK
                    last_black = col_idx
                col_idx += 1
                
        return smeared_img
    
    def show_bin_img(self, bin_img: ndarray, title: str = "Binarized image"):
        
        img = Image.fromarray(bin_img)
        img.save("/tmp/test.png")
        img.show(title)