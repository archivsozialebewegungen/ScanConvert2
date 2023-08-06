'''
Created on 20.05.2023

@author: michael
'''
from PIL import Image
from numpy.core._multiarray_umath import ndarray
from skimage.filters.thresholding import threshold_otsu

import numpy as np


BINARY_BLACK = False
BINARY_WHITE = True
GRAY_BLACK = 0
GRAY_WHITE = 255

class BinarizationService(object):

    def binarize_otsu(self, img: Image) -> ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_otsu(in_array)
        return in_array > threshold
    
class NdArrayService(object):
    
    def convert_binary_to_inverted_gray(self, binary_ndarray: ndarray):
        
        gray_ndarray = np.array(binary_ndarray, dtype=np.uint8)
        gray_ndarray[gray_ndarray == BINARY_BLACK] = GRAY_WHITE
        gray_ndarray[gray_ndarray == BINARY_WHITE] = GRAY_BLACK
        
        return gray_ndarray

class ConstrainedRunLengthAlgorithmsService(object):
    """
    Implementation of a constrained run length algorithm (CRLA)
    """

    def smear_horizontal(self, bin_img: ndarray, constraint: int, boundary_color = BINARY_BLACK):

        height = bin_img.shape[0]
        width = bin_img.shape[1]
        smeared_img = bin_img.copy()
        for row_idx in range(0, height):
            line = bin_img[row_idx]
            col_idx = 0
            gap_size = None
            while col_idx < width:
                if line[col_idx] == boundary_color:
                    if gap_size is not None and gap_size > 0:
                        if gap_size < constraint:
                            gap_start = col_idx - gap_size
                            smeared_img[row_idx, gap_start:col_idx] = boundary_color
                    gap_size = 0
                else:
                    if gap_size is not None:
                        gap_size += 1
                    
                col_idx += 1
                
        return smeared_img
