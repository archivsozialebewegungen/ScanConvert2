'''
Created on 20.05.2023

@author: michael
'''
from PIL import Image
import cv2
import numpy as np

from Asb.ScanConvert2.AutoProcessing.CommonOperations import BinarizationService,\
    ConstrainedRunLengthAlgorithmsService, NdArrayService
import math


class RotationService(object):
    
    def __init__(self,
                 ndarray_service: NdArrayService,
                 binarization_service: BinarizationService,
                 run_length_algorithms_service: ConstrainedRunLengthAlgorithmsService):
        
        self.ndarray_service = ndarray_service
        self.binarization_service = binarization_service
        self.run_length_algorithms_service = run_length_algorithms_service
    
    def correctRotation(self, img: Image) -> Image:
        
        angle = self.determine_rotation(img)
        if abs(angle) > 0.2:
            img = img.rotate(angle, expand=True, fillcolor="white")

        return img
    
    def determine_rotation(self, img):

        bin_ndarray = self.binarization_service.binarize_otsu(img)
        rotated_rectangles = self._calculate_rotated_rectangles(bin_ndarray)
        
        return self._calculate_rotation_angle(rotated_rectangles)
    
    def _calculate_rotated_rectangles(self, bin_ndarray):

        smeared_ndarray = self.run_length_algorithms_service.smear_horizontal(bin_ndarray, 25)
        smeared_ndarray_gray = self.ndarray_service.convert_binary_to_inverted_gray(smeared_ndarray)
        contours, _ = cv2.findContours(smeared_ndarray_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rotated_rectangles = []
        for contour in contours:
            if cv2.contourArea(contour) < 8:
                continue
            rotated_rectangle = cv2.minAreaRect(contour)
            rotated_rectangles.append(rotated_rectangle)

        return rotated_rectangles
    
    def _calculate_rotation_angle(self, rectangles):
        
        angles = []
        for rectangle in rectangles:
            line = self._find_long_side(rectangle)
            dy = line[1][1] - line[0][1]
            dx = line[1][0] - line[0][0]
            theta = math.atan2(dy, dx)
            angle = theta * 180 / math.pi
            angles.append(angle)
            
        angle_dict = {}
        tolerance = 2.0
        for angle in angles:
            for key in angle_dict.keys():
                if abs(angle - key) < tolerance:
                    angle_dict[key].append(angle)
                    break
            else:
                angle_dict[angle] = [angle]

        max1 = []
        max2 = []
        for angle in angle_dict.keys():
            if len(angle_dict[angle]) > len(max1):
                max2 = max1
                max1 = angle_dict[angle]
        
        if len(max2) / len(max1) < 0.1:
            angle = np.average(max1)
            if angle > 45:
                angle -= 90
            elif angle * -1 > 45:
                angle += 90
        else:
            angle1 = np.average(max1)
            angle2 = np.average(max2)
            if abs(abs(angle1 - angle2) - 90.0) > 2.0:
                # These are not meaningful values
                return 0.0
            if abs(angle1) < abs(angle2):
                angle = angle1
            else:
                angle = angle2

        return angle
    
    def _find_long_side(self, rectangle):
        '''
        returns the coordinates of one of the
        longer sides of the rectangle where the
        first coordinate is left from the right
        coordinate
        '''

        points = cv2.boxPoints(rectangle)
        length1 = self._calculate_length(points[0], points[1])
        length2 = self._calculate_length(points[0], points[3])
        
        if length1 > length2:
            if points[0][0] < points[1][0]:
                return points[0], points[1]
            else:
                return points[1], points[0]
        else:
            if points[0][0] < points[3][0]:
                return points[0], points[3]
            else:
                return points[3], points[0]

    def _calculate_length(self, coord1, coord2):
        
        dx = coord1[0] - coord2[0]
        dy = coord1[1] - coord2[1]
        
        # Good old Pythagoras
        return math.sqrt(dx * dx + dy * dy)
