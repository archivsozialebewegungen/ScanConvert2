'''
Created on 20.03.2023

@author: michael
'''
from PIL import Image
from numpy.core._multiarray_umath import ndarray
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola,\
    threshold_niblack

from Asb.ScanConvert2.PageSegmentationModule.Domain import BINARY_BLACK, GRAY_WHITE,\
    BINARY_WHITE, GRAY_BLACK, BoundingBox
import numpy as np
from PIL.Image import Dither


class ImageStatisticsService(object):
    
    def count_transitions(self, binary_ndarray: ndarray, bounding_box: BoundingBox):
        
        transition_count = 0
        for row_idx in range(bounding_box.y1, bounding_box.y2):
            current_color = BINARY_WHITE
            for col_idx in range(bounding_box.x1, bounding_box.x2):
                if current_color != binary_ndarray[row_idx, col_idx]:
                    if binary_ndarray[row_idx, col_idx] == BINARY_BLACK:
                        transition_count += 1
                    current_color = binary_ndarray[row_idx, col_idx]
        return transition_count
        

class NdArrayService(object):
    
    def convert_binary_to_inverted_gray(self, binary_ndarray: ndarray):
        
        gray_ndarray = np.array(binary_ndarray, dtype=np.uint8)
        gray_ndarray[gray_ndarray == BINARY_BLACK] = GRAY_WHITE
        gray_ndarray[gray_ndarray == BINARY_WHITE] = GRAY_BLACK
        
        return gray_ndarray

class BinarizationService(object):

    def binarize_threshold(self, img: Image, threshold: int) -> ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        return in_array > threshold
    
    def binarize_floyd_steinberg(self, img: Image) -> ndarray:
        
        return np.asarray(img.convert("1"))
    
    def binarize_rasterize(self, img: Image) -> ndarray:
        
        return np.asarray(img.convert("1", dither=Dither.RASTERIZE))

    def binarize_ordered(self, img: Image) -> ndarray:
        
        return np.asarray(img.convert("1", dither=Dither.ORDERED))

    def binarize_otsu(self, img: Image) -> ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_otsu(in_array)
        return in_array > threshold
    
    def binarize_sauvola(self, img: Image) -> ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_sauvola(in_array)
        return in_array > threshold

    def binarize_niblack(self, img: Image) -> ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_niblack(in_array)
        return in_array > threshold

class RunLengthAlgorithmService(object):
    """
    Implementation of a constrained run length algorithm (CRLA)
    """
    
    def calculate_run_lengths(self, bin_img: ndarray) -> ndarray:

        zero = self.calculate_0_degrees_run_lengths(bin_img, BINARY_BLACK)
        fortyfive = self.calculate_45_degrees_run_lengths(bin_img, BINARY_BLACK)
        ninety = self.calculate_90_degrees_run_lengths(bin_img, BINARY_BLACK)
        onehundredthirtyfive = self.calculate_135_degrees_run_lenghts(bin_img, BINARY_BLACK)
        
        return np.array([zero, fortyfive, ninety, onehundredthirtyfive]).transpose()
        
    def calculate_0_degrees_run_lengths(self, bin_img: ndarray, projection_color=BINARY_BLACK) -> ndarray:
        
        matrix = np.zeros_like(bin_img, dtype=np.uint32)
        width = matrix.shape[1]
        height = matrix.shape[0]
        
        for row_idx in range(0, height):
            row = bin_img[row_idx]
            counter = 0
            for col_idx in range(0, width):
                if row[col_idx] != projection_color:
                    counter = 0
                else:
                    counter += 1
                    matrix[row_idx, col_idx] = counter
            for col_idx in reversed(range(0, width-1)):
                if matrix[row_idx, col_idx] == 0:
                    continue
                if matrix[row_idx, col_idx + 1] > matrix[row_idx, col_idx]:
                    matrix[row_idx, col_idx] = matrix[row_idx, col_idx + 1]

        return matrix
    
    def calculate_45_degrees_run_lengths(self, bin_img: ndarray, projection_color=BINARY_BLACK) -> ndarray:
        
        matrix = np.zeros_like(bin_img, dtype=np.float32)
        width = matrix.shape[1]
        height = matrix.shape[0]
        
        for projection_idx in range(0, width):
            col_idx = projection_idx
            row_idx = 0
            counter = 0
            while col_idx < width and row_idx < height:
                if bin_img[row_idx, col_idx] != projection_color:
                    counter = 0
                else:
                    counter += 1
                    matrix[row_idx, col_idx] = counter
                col_idx += 1
                row_idx += 1
            col_idx -= 1
            row_idx -= 1
            while col_idx > projection_idx:
                col_idx -= 1
                row_idx -= 1
                if matrix[row_idx, col_idx] == 0:
                    continue
                if matrix[row_idx + 1, col_idx + 1] > matrix[row_idx, col_idx]:
                    matrix[row_idx, col_idx] = matrix[row_idx + 1, col_idx + 1]

        for projection_idx in range(1, height):
            row_idx = projection_idx
            col_idx = 0
            counter = 0
            while col_idx < width and row_idx < height:
                if bin_img[row_idx, col_idx] != projection_color:
                    counter = 0
                else:
                    counter += 1
                    matrix[row_idx, col_idx] = counter
                col_idx += 1
                row_idx += 1

            col_idx -= 1
            row_idx -= 1
            while row_idx > projection_idx:
                col_idx -= 1
                row_idx -= 1
                if matrix[row_idx, col_idx] == 0:
                    continue
                if matrix[row_idx + 1, col_idx + 1] > matrix[row_idx, col_idx]:
                    matrix[row_idx, col_idx] = matrix[row_idx + 1, col_idx + 1]
        
        return matrix.astype(np.uint32)

    def calculate_90_degrees_run_lengths(self, bin_img: ndarray, projection_color = BINARY_BLACK):
        
        matrix = self.calculate_0_degrees_run_lengths(np.rot90(bin_img, -1), projection_color)
        return np.rot90(matrix)
    
    def calculate_135_degrees_run_lenghts(self, bin_img: ndarray, projection_color = BINARY_BLACK):
        
        matrix = self.calculate_45_degrees_run_lengths(np.rot90(bin_img, -1), projection_color)
        return np.rot90(matrix)
    
    def signal_cross_correlation(self, binary_segment_data: ndarray, line_idx: int, distance: int):
        
        width = binary_segment_data.shape[1]
        intermediate = np.bitwise_xor(binary_segment_data[line_idx], binary_segment_data[line_idx + distance])
        return 1 - (2 / width)*np.sum(intermediate)
        
    def smear_vertical(self, bin_img: ndarray, constraint: int, boundary_color = BINARY_BLACK):
        
        smeared_img = self.smear_horizontal(np.rot90(bin_img, -1), constraint, boundary_color)
        return np.rot90(smeared_img)

    def smear_horizontal(self, bin_img: ndarray, constraint: int, boundary_color = BINARY_BLACK):
        # This is much faster (factor 1:3) than using the generic
        # run length methods to implement smearing
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
