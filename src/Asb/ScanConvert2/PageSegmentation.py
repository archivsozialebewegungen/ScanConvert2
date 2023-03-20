'''
Created on 19.02.2023

@author: michael

This module implements the page segmentations algorithm described in
"Block Segmentation and Text Extraction in Mixed Text/Image Documents"
by FRIEDRICH M. WAHL, KWAN Y. WONG, AND RICHARD G. CASEY
(https://doi.org/10.1016/0146-664X(82)90059-4)

There are two modifications: We added a criterium to detect border
frames (via black / white ratio) and we distinguish between photos
and drawings (also unsing the black / white ratio).
'''

from PIL import Image
from numpy.core._multiarray_umath import ndarray
from skimage.filters.thresholding import threshold_otsu
from Asb.ScanConvert2.ScanConvertDomain import Region

import numpy as np
import cv2
from injector import singleton

BLACK = False
WHITE = True

class BoundingBox(Region):
    
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)

class NoMeaningfulTextFoundException(Exception):
    
    pass

class Segments(object):
    
    def __init__(self, segment_list):
        
        self.segments = {}
        for segment in segment_list:
            self.segments[segment.label] = segment
            
        self.height_mean = None
        self.height_standard_deviation = None
        self.transition_ratio_mean = None
        self.transition_ratio_standard_deviation = None
        
        self._text_segments = None
        self._photo_segments = None
        self._drawing_segments = None
        self._border_segments = None
        
    def _classify_segments(self):
        
        text_segments = self._get_text_segment_cluster()
        self.height_mean,\
        self.height_standard_deviation,\
        self.transition_ratio_mean,\
        self.transition_ratio_standard_deviation = self._calculate_means_and_standard_deviations(text_segments)
        
        self._verify_text_infos()

        self._text_segments = []
        self._border_segments = []
        self._photo_segments = []
        self._drawing_segments = []
        
        for segment in self.segments.values():
            
            if segment.bw_ratio < 0.1:
                # Just a black border frame with lot of white inside
                self._border_segments.append(segment.label)
                continue
            
            if segment.height <= 3 * self.height_mean:
                if segment.transition_ratio <= 3 * self.transition_ratio_mean:
                    # Text
                    self._text_segments.append(segment.label)
                else:
                    # horizontal border
                    self._border_segments.append(segment.label)
            else:
                if segment.eccentricity > 1 / 5:
                    # Picture
                    if segment.bw_ratio > 0.5:
                        self._photo_segments.append(segment.label)
                    else:
                        self._drawing_segments.append(segment.label)
                else:
                    self._border_segments.append(segment.label)
        
    def _get_text_segment_cluster(self):

        text_segments = []
        for segment in self.segments.values():
            if segment.is_probably_textsegment():
                text_segments.append(segment)

        #assert(len(text_segments) > 10)
        #assert(len(text_segments) / len(self.segments) > 0.5)
        
        return text_segments
    
    def _calculate_means_and_standard_deviations(self, text_segments):     

        h_array = []
        r_array = []
        for segment in text_segments:
            h_array.append(segment.height)
            r_array.append(segment.transition_ratio)
            
        mean_h = np.mean(h_array)
        mean_r = np.mean(r_array)
        sigma_h = np.std(h_array)
        sigma_r = np.std(r_array)
            
        return mean_h, sigma_h, mean_r, sigma_r

    def _verify_text_infos(self):
        
        return
        
        if self.height_mean < 60 \
            and self.transition_ratio_mean < 8 \
            and self.height_standard_deviation < 5 \
            and self.transition_ratio_standard_deviation < 2 \
            and self.height_standard_deviation / self.height_mean < 0.5 \
            and self.transition_ratio_standard_deviation / self.transition_ratio_mean < 0.5:
            return
        
        raise NoMeaningfulTextFoundException()
    
    def _collect_segments(self, label_list):

        segments = []
        for label in label_list:
            segments.append(self.segments[label])
        return segments
    
    def _get_photo_segments(self):
        
        if self._photo_segments == None:
            self._classify_segments()
        
        return self._collect_segments(self._photo_segments)
        
    
    photo_segments = property(_get_photo_segments)


class Segment(object):
    
    C1 = 4
    C2 = 100
    C3 = 10
    C4 = 0.5
    
    def __init__(self, label, stats, label_matrix, binary_img, smeared_img):
        
        self.label_matrix = label_matrix
        self.binary_img = binary_img
        self.smeared_img = smeared_img
        self.label = label
        self.stats = stats
        self.bounding_box = BoundingBox(self.stats[cv2.CC_STAT_LEFT],
                                        self.stats[cv2.CC_STAT_TOP],
                                        self.stats[cv2.CC_STAT_WIDTH],
                                        self.stats[cv2.CC_STAT_HEIGHT])
        self._mask = None
        self._original_black_count = None
        self._transition_count = None
        
    def is_probably_textsegment(self):

        if self.transition_ratio == 0:
            return False
        
        h_tr_ratio = self.height / self.transition_ratio
        
        if h_tr_ratio < 4:
            return False
        
        if self.height > 100:
            return False
        
        if self.eccentricity < 10:
            return False
        
        if self.shape < 0.5:
            return False
        
        return True
        
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
    
    def overlay_on_image_exact(self, img):
        
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
    
    def overlay_on_image_bounding_box(self, img):
        
        segment = img.crop(self.bounding_box.x, self.bounding_box.y, self.bounding_box.x + self.bounding_box.width, self.bounding_box.y + self.bounding_box.height)
        segment = segment.convert("1")
        img.paste(segment, (self.bounding_box.x, self.bounding_box.y))
        
        return img
                
    def _get_original_black_count(self):
        
        if self._original_black_count is not None:
            return self._original_black_count
        
        
        bin_copy = self.binary_img.copy()
        bin_copy[self.label_matrix != self.label] = WHITE
        count = bin_copy.shape[0] * bin_copy.shape[1] - np.count_nonzero(bin_copy)
        assert(count >= 0)
        return count
    
    def _get_white_black_transition_count(self):
        
        if self._transition_count is not None:
            return self._transition_count
        
        self._transition_count = 0
        for row_idx in range(self.bounding_box.y, self.bounding_box.y + self.bounding_box.height):
            current_color = WHITE
            for col_idx in range(self.bounding_box.x, self.bounding_box.x + self.bounding_box.width):
                if current_color != self.binary_img[row_idx, col_idx]:
                    if self.binary_img[row_idx, col_idx] == BLACK:
                        self._transition_count += 1
                    current_color = self.binary_img[row_idx, col_idx]
        return self._transition_count
    
    def _get_transition_ratio(self):
        
        return self.original_black_count * 1.0 / self.transition_count
    
    def _get_bw_ratio(self):
        
        whites = self.bounding_box.size - self.original_black_count
        if whites == 0:
            return 10000
        return self.original_black_count / whites
    
    def _get_smeared_bw_ratio(self):
        
        whites = self.bounding_box.size - self.black_count
        if whites == 0:
            return 10000
        return self.original_black_count / whites
    
    def _get_smearing_coeffizient(self):
        
        return self.smeared_bw_ratio / self.bw_ratio

    def __str__(self):
        
        result = "Segment %d:\n" % self.label
        result += "  Bounding box: %s\n" % self.bounding_box
        result += "  Black count: %d\n" % self.black_count
        result += "  Black count in original: %d\n" % self.original_black_count
        result += "  Eccentricity: %0.2f\n" % self.eccentricity
        result += "  Shape: %0.2f\n" % self.shape
        result += "  Transition ratio: %0.2f\n" % self.transition_ratio
        result += "  Black/white ratio: %0.2f\n" % self.bw_ratio
        result += "  Smeared black/white ratio: %0.2f\n" % self.smeared_bw_ratio
        result += "  Smearing coeffzient: %0.2f" % self.smearing_coeffizient
        
        return result
        
        
 
    
    mask = property(_get_mask)
    black_count = property(lambda self: self.stats[cv2.CC_STAT_AREA])
    original_black_count = property(_get_original_black_count)
    transition_count = property(_get_white_black_transition_count)
    height = property(lambda self: self.bounding_box.height)
    eccentricity = property(lambda self: self.bounding_box.eccentricity)
    shape = property(lambda self: self.black_count * 1.0 / self.bounding_box.size)
    transition_ratio = property(_get_transition_ratio)
    bw_ratio = property(_get_bw_ratio)
    smeared_bw_ratio = property(_get_smeared_bw_ratio)
    smearing_coeffizient = property(_get_smearing_coeffizient)
        

@singleton
class WahlWongCaseySegmentationService(object):
    '''
    classdocs
    '''

    def find_photo_segments(self, img: Image) -> []:
    
        return Segments(self._collect_stats(img)).photo_segments
    
    def find_photos(self, img: Image) -> []:
        
        regions = []
        try:
            for segment in self.find_photo_segments(img):
                regions.append(segment.bounding_box)
        except NoMeaningfulTextFoundException:
            print("No meaningful text found on page!")
            pass
        return regions
    
    def _collect_stats(self, original_img: Image):
        
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
            segment = Segment(label, stats[label], label_matrix, binary_img, smeared_gray_img)
            if segment.transition_count == 0:
                # White segment empedded in Black segment
                continue
            segments.append(segment)
    
        return segments
    
    def smear_image(self, binary_img: Image) -> Image:

        print("First horizontal smear")
        hor_smeared = self.smear_horizontal(binary_img, 300)
        print("Vertical smear")
        ver_smeared = self.smear_vertical(binary_img, 500)
        print("Second horizontal smear")
        combined = np.logical_or(hor_smeared, ver_smeared)
        final = self.smear_horizontal(combined, 20)
        print("Smearing done.")
        #Image.fromarray(final).show("Smeared Image")
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
