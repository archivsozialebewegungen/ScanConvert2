'''
Created on 07.04.2023

@author: michael
'''
import math

from PIL.Image import Image
import cv2

from Asb.ScanConvert2.PageSegmentationModule.Domain import BoundingBox, \
    BINARY_BLACK, BINARY_WHITE
import numpy as np
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService,\
    NdArrayService


def value_or_none(contour_id):
    
    if contour_id == -1:
        return None
    return contour_id

class RotatedRectangle(object):
    
    def __init__(self, cv2_rectangle):
        
        self.cv2_rectangle = cv2_rectangle
        self.height, self.width = self._calculate_dimensions(cv2_rectangle)
        self.eccentricity = 0
        try:
            self.eccentricity = self.height / self.width
        except ZeroDivisionError:
            pass
        self.area = self.height * self.width
        
    def _calculate_dimensions(self, cv2_rectangle):
        
        coords = cv2.boxPoints(cv2_rectangle)
        lengths = []
        
        if coords[1][0] < coords[3][0]:
            height = 1
            width = 3
        else:
            height = 3
            width = 1
        
        for idx in (height, width):
            lengths.append(self._calculate_length(coords[0], coords[idx]))

        return lengths
    
    def _calculate_length(self, coord1, coord2):
        
        dx = coord1[0] - coord2[0]
        dy = coord1[1] - coord2[1]
        
        # Good old Pythagoras
        return math.sqrt(dx * dx + dy * dy)


class Contour(object):
    
    def __init__(self, contour_id, cv2_contour, hierarchy):
        
        self.contour_id = contour_id
        self.cv2_contour = cv2_contour
        self.next_id = value_or_none(hierarchy[0])
        self.previous_id = value_or_none(hierarchy[1])
        self.parent_id = value_or_none(hierarchy[2])
        self.first_child_id = value_or_none(hierarchy[3])
        self.rectangle = RotatedRectangle(cv2.minAreaRect(cv2_contour))
        self.bounding_box = BoundingBox.create_from_rectangle(cv2.boundingRect(cv2_contour))
        
    def fetch_child_ids(self, all_contours, parent_id=None, child_ids=[]):
        
            if parent_id is None:
                return self.fetch_child_ids(all_contours, self.contour_id, child_ids)
            
            for child_contour in all_contours:
                if child_contour.parent_id == parent_id:
                    child_ids.append(child_contour.contour_id)
                    child_ids = child_ids + self.fetch_child_ids(all_contours, child_contour.contour_id, child_ids)
            
            return child_ids

    eccentricity = property(lambda self: self.rectangle.eccentricity)

class LineRemovingService(object):
    '''
    classdocs
    '''


    def __init__(self, run_length_algorithm_service: RunLengthAlgorithmService,
                 ndarray_service: NdArrayService):
        
        self.run_length_algorithm_service = run_length_algorithm_service
        self.ndarray_service = ndarray_service

    def remove_lines(self, bin_ndarray):

        v_line_mask = self.get_vertical_line_mask(bin_ndarray)
        h_line_mask = self.get_horizontal_line_mask(bin_ndarray)
        bin_ndarray[v_line_mask > 0] = 1
        bin_ndarray[h_line_mask > 0] = 1
        
        return bin_ndarray
        
    def get_vertical_line_mask(self, bin_ndarray):
        
        mask = self.get_horizontal_line_mask(np.rot90(bin_ndarray, -1))
        return np.rot90(mask)
        
    def get_horizontal_line_mask(self, bin_ndarray):
        
        h_smeared_bin_ndarray = self.run_length_algorithm_service.smear_horizontal(bin_ndarray, 60, BINARY_WHITE)
        gray_ndarray = self.ndarray_service.convert_binary_to_inverted_gray(h_smeared_bin_ndarray)
        contours = self.get_contours(gray_ndarray)
        
        large_contours = []
        for contour in contours:
            if cv2.contourArea(contour.cv2_contour) > 50:
                large_contours.append(contour)
                
        large_contours.sort(key=lambda x: x.eccentricity)
        cv2_contours = []
        for contour in large_contours:
            if contour.eccentricity > 0.17:
                break
            cv2_contours.append(contour.cv2_contour)
        
        mask = np.zeros_like(gray_ndarray)
        cv2.drawContours(mask, cv2_contours, -1, 255, cv2.FILLED)
        mask = self.run_length_algorithm_service.smear_horizontal(mask, 100, BINARY_BLACK)
        return cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 8)))
        
        bin_ndarray[mask > 0] = 1
        Image.fromarray(bin_ndarray).show()

        
    def get_contours(self, bin_ndarray):
                
        contours, hierarchy = cv2.findContours(bin_ndarray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contour_objects = []
        for idx in range(0, len(contours)):
            contour_objects.append(Contour(idx, contours[idx], hierarchy[0][idx]))
        return contour_objects
        