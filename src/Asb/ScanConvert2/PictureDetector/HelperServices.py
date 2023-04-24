'''
Created on 19.04.2023

@author: michael
'''
from injector import singleton
from PIL import Image
import pytesseract
from pytesseract.pytesseract import Output
import numpy as np
from PIL.Image import Dither
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola
import cv2
from statistics import median

BINARY_BLACK = False
BINARY_WHITE = True
GRAY_BLACK = 0
GRAY_WHITE = 255


class BinarizationService(object):

    def binarize_threshold(self, img: Image, threshold: int) -> np.ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        return in_array > threshold
    
    def binarize_floyd_steinberg(self, img: Image) -> np.ndarray:
        
        return np.asarray(img.convert("1"))
    
    def binarize_rasterize(self, img: Image) -> np.ndarray:
        
        return np.asarray(img.convert("1", dither=Dither.RASTERIZE))

    def binarize_ordered(self, img: Image) -> np.ndarray:
        
        return np.asarray(img.convert("1", dither=Dither.ORDERED))

    def binarize_otsu(self, img: Image) -> np.ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_otsu(in_array)
        return in_array > threshold
    
    def binarize_sauvola(self, img: Image) -> np.ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = threshold_sauvola(in_array)
        return in_array > threshold

    def binarize_niblack(self, img: Image) -> np.ndarray:
        
        gray_img = img.convert("L")
        in_array = np.asarray(gray_img)
        threshold = np.threshold_niblack(in_array)
        return in_array > threshold

@singleton
class OrientationCorrectionService(object):
    '''
    Uses tesseract to determine the orientation of a scan
    and rotates it correctly
    '''

    rotations = {90: Image.ROTATE_90,
             180: Image.ROTATE_180,
             270: Image.ROTATE_270}

    
    def correct_orientation(self, img):
        
        correction = self._determine_correction(img)
        if correction == 0:
            return img
        
        return img.transpose(self.rotations[correction])
        
    def _determine_correction(self, img):
        
        try:
            orientation = pytesseract.image_to_osd(img, output_type=Output.DICT)
        except:
            return 0
        return orientation["orientation"]

@singleton
class NdArrayService(object):
    
    def convert_binary_to_inverted_gray(self, binary_ndarray: np.ndarray):
        
        gray_ndarray = np.array(binary_ndarray, dtype=np.uint8)
        gray_ndarray[gray_ndarray == BINARY_BLACK] = GRAY_WHITE
        gray_ndarray[gray_ndarray == BINARY_WHITE] = GRAY_BLACK
        
        return gray_ndarray

@singleton
class SmearingService(object):
    """
    Implementation of a constrained run length algorithm (CRLA)
    """
    
    def smear_vertical(self, bin_img: np.ndarray, constraint: int, boundary_color = BINARY_BLACK):
        
        smeared_img = self.smear_horizontal(np.rot90(bin_img, -1), constraint, boundary_color)
        return np.rot90(smeared_img)

    def smear_horizontal(self, bin_img, constraint: int, boundary_color = BINARY_BLACK):
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

@singleton
class AngleCorrectionService(object):
    '''
    This uses a smearing algorithm to make text lines quite solid. Then it identifies
    text lines by the relation of width to height and puts a rotated rectangle around.
    The median of the rotation angles of these angles is considered to be the
    correct angle.
    '''

    rotations = {90: Image.ROTATE_90,
             180: Image.ROTATE_180,
             270: Image.ROTATE_270}

    def __init__(self,
                 binarization_service: BinarizationService,
                 smearing_service: SmearingService,
                 ndarray_service: NdArrayService):
        
        self.binarization_service = binarization_service
        self.smearing_service = smearing_service
        self.ndarray_service = ndarray_service
    
    def correct_angle(self, img):
        
        bin_ndarray = self.binarization_service.binarize_otsu(img)
        smeared_ndarray = self.smearing_service.smear_horizontal(bin_ndarray, 25, BINARY_BLACK)
        smeared_ndarray_gray = self.ndarray_service.convert_binary_to_inverted_gray(smeared_ndarray)
        contours, _ = cv2.findContours(smeared_ndarray_gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        text_contours = self._find_text_lines(contours)
        angle = self._find_angle(text_contours)
        
        if abs(angle) > 0.2:
            return self._rotate_image(img, angle)

        return img

    def _find_text_lines(self, contours):

        probable_text_contours = []
        for contour in contours:
            bounding_rectangle = cv2.boundingRect(contour)
            width = bounding_rectangle[2]
            height = bounding_rectangle[3]
            # if it is much longer than heigh, it probably
            # is text (or a horizontal line)
            if height * 5 < width:
                probable_text_contours.append(contour)
                
        return probable_text_contours
        
    def _find_angle(self, text_contours):
        
        angles = []
        for text_contour in text_contours:
            rotated_rectangle = cv2.minAreaRect(text_contour)
            angle = rotated_rectangle[2]
            if angle == 90 or angle == 0:
                continue
            angles.append(angle)
        
        median_angle = median(angles)
        if median_angle > 45:    
            return median_angle - 90
        else:
            return median_angle
        
    def _rotate_image(self, img, angle):
        
        width = img.width
        height = img.height
        
        img = img.rotate(angle, expand=True, fillcolor="white")

        return self._trim_image(img, width, height)
        
    def _trim_image(self, img: Image, width: int, height: int):
        
        x = int((img.width - width) / 2)
        y = int((img.height - height) / 2)
        return img.crop((x, y, x+width, y+height))