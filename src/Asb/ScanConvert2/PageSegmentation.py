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

def show_bin_img(bin_img: ndarray, title: str = "Binarized image"):
        
    img = Image.fromarray(bin_img)
    img.save("/tmp/test.png")
    img.show(title)
    
class SegmentType(Enum):
    
    TEXT = 1
    PHOTO = 2
    DRAWING = 3
    
class BoundingBox(object):
    
    def __init__(self, x, y, width, height):
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)

class Segment(object):
    
    def __init__(self, label, stats, label_matrix, binary_img):
        
        self.label_matrix = label_matrix
        self.binary_img = binary_img
        self.label = label
        self.stats = stats
        self.bounding_box = BoundingBox(self.stats[cv2.CC_STAT_LEFT],
                                        self.stats[cv2.CC_STAT_TOP],
                                        self.stats[cv2.CC_STAT_WIDTH],
                                        self.stats[cv2.CC_STAT_HEIGHT])
        self._mask = None
        self._dc = None
        self._tc = None
        
    def _get_mask(self):
        
        if self._mask is not None:
            return self._mask
        
        background = 255
        if self.label == 255:
            background = 245
        
        matrix_copy = self.label_matrix.copy()
        matrix_copy[matrix_copy != self.label] = background
        matrix_copy[matrix_copy == self.label] = 0
        if background == 245:
            matrix_copy[matrix_copy == background] = 255
            
        self._mask = matrix_copy
        return self._mask
    
    def _get_bb_mask(self):
        
        if self._mask is not None:
            return self._mask
        
        mask_img = Image.new("L", (self.label_matrix.shape[1], self.label_matrix.shape[0]), 255)
        bb = Image.new("L", (self.bounding_box.width, self.bounding_box.height), 0)
        mask_img.paste(bb, (self.bounding_box.x, self.bounding_box.y))
        return np.asarray(mask_img)
    
    def overlay_on_image(self, img):
        
        background = img.convert("RGBA")
                
        ndarray_img = np.asarray(img)
        segment_extract = np.bitwise_or(ndarray_img, self.mask)
        segment = Image.fromarray(segment_extract)
        segment = segment.convert("1") # Floyd-Steinberg dithering
        segment = segment.convert("RGBA")
        
        mask_img = Image.fromarray(self.mask)
        mask_img = mask_img.convert("1")
        background.putalpha(mask_img)
                
        return Image.alpha_composite(segment, background).convert(img.mode)
    
    def _get_dc(self):
        
        if self._dc is not None:
            return self._dc
        
        bin_copy = self.binary_img.copy()
        bin_copy[self.label_matrix != self.label] = 0
        return np.count_nonzero(bin_copy)
    
    def _get_tc(self):
        
        if self._tc is not None:
            return self._tc
        
        self._tc = 0
        for row_idx in range(self.bounding_box.y, self.bounding_box.y + self.bounding_box.height):
            current_color = WHITE
            for col_idx in range(self.bounding_box.y, self.bounding_box.y + self.bounding_box.height):
                if current_color != self.binary_img[row_idx, col_idx]:
                    self._tc += 1
                    current_color = self.binary_img[row_idx, col_idx]
        return self._tc
    
    mask = property(_get_bb_mask)
    bc = property(lambda self: self.stats[cv2.CC_STAT_AREA])
    dc = property(_get_dc)
    tc = property(_get_tc)
    h = property(lambda self: self.bounding_box.height)
    e = property(lambda self: self.bounding_box.eccentricity)
    s = property(lambda self: self.bc / self.bounding_box.size)
    r = property(lambda self: self.dc / self.tc)
        


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
        
        return self.collect_stats(img)
    
    def collect_stats(self, original_img: Image):
        
        gray_img = original_img.convert("L")

        binary_img = self.binarize(gray_img)
        smeared_img = self.smear_image(binary_img)
        smeared_gray_img = np.array(smeared_img, dtype=np.uint8)
        smeared_gray_img[smeared_gray_img == 0] = 255
        smeared_gray_img[smeared_gray_img == 1] = 0

        connectivity = 4
        no_of_components, label_matrix, stats, centroids = cv2.connectedComponentsWithStats(smeared_gray_img, connectivity)
        segments = []
        for label in range(1, no_of_components):
            segments.append(Segment(label, stats[label], label_matrix, binary_img))
        return segments
    
    def smear_image(self, binary_img: Image) -> Image:

        print("First horizontal smear")
        hor_smeared = self.smear_horizontal(binary_img, 300)
        print("Vertical smear")
        ver_smeared = self.smear_vertical(binary_img, 300)
        print("Second horizontal smear")
        combined = np.logical_or(hor_smeared, ver_smeared)
        final = self.smear_horizontal(combined, 20)
        print("Smearing done.")
        return final
        
    def binarize(self, gray_img: Image) -> ndarray:
        
        in_array = np.asarray(gray_img)
        threshold = threshold_otsu(in_array)
        return in_array > threshold
    
    def smear_vertical(self, bin_img: ndarray, constraint: int):
        
        smeared_img = self.smear_horizontal(np.rot90(bin_img, -1), constraint)
        return np.rot90(smeared_img)

    def smear_horizontal(self, bin_img: ndarray, constraint: int):
        
        height = bin_img.shape[0]
        width = bin_img.shape[1]
        smeared_img = bin_img.copy()
        for row_idx in range(0, height):
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
    
