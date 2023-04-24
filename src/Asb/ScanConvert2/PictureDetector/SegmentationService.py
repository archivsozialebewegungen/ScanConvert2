'''
Created on 19.04.2023

@author: michael
'''
from Asb.ScanConvert2.PictureDetector.HelperServices import OrientationCorrectionService,\
    BinarizationService, AngleCorrectionService, SmearingService, NdArrayService
from Asb.ScanConvert2.ScanConvertDomain import Page, Region
from PIL import Image
import numpy as np
import cv2

class BoundingBox(object):

    @classmethod
    def create_from_cv2_bounding_box(cls, bb):
        
        return BoundingBox(bb[0], bb[1], bb[2], bb[3])

    
    def __init__(self, x, y, width, height):
        
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        
    def is_vertically_near(self, other, tolerance):

        upper_self = self.y1
        lower_self = self.y2
        upper_other = other.y1
        lower_other = other.y2
        
        return abs(lower_self-upper_other) < tolerance or abs(lower_other-upper_self) < tolerance
 
        return False
    
    def is_horizontally_contained_in(self, other, tolerance):
        
        return other.x1 - tolerance < self.x1 and other.x2 + tolerance > self.x2
    
    
    def has_nearly_the_same_width(self, other, coefficient):
        
        minimum = np.min([self.width, other.width])
        maximum = np.max([self.width, other.width])
        return minimum / maximum >= coefficient

    def aligns_left_at_the_bottom(self, other, v_tolerance, h_tolerance):
        
        v_distance = other.y1 - self.y2
        
        if v_distance < 0 or v_distance > v_tolerance:
            return False
        
        if other.x2 > self.x2 + h_tolerance:
            return False
        
        return abs(self.x1 - other.x1) < h_tolerance

    def intersects_with(self, other):
        
        return not (self.x2 < other.x1 or other.x2 < self.x1 or self.y2 < other.y1 or other.y2 < self.y1)
    
    def is_contained_within_self(self, other, percent=100):
        
        if percent == 100:
        
            if not self.point_within_self(other.x1, other.y1):
                return False
            if not self.point_within_self(other.x2, other.y2):
                return False
        
        if other.x1 >= self.x1 and other.x1 <= self.x2:
            intersection_x1 = other.x1
        elif other.x1 < self.x1 and other.x2 >= self.x1:
            intersection_x1 = self.x1
        else:
            return False
        if other.x2 <= self.x2 and other.x2 >= self.x1:
            intersection_x2 = other.x2
        elif other.x2 > self.x2 and other.x1 <= self.x2:
            intersection_x2 = self.x2
        else:
            return False
        if other.y1 >= self.y1 and other.y1 <= self.y2:
            intersection_y1 = other.y1
        elif other.y1 < self.y1 and other.y2 >= self.y1:
            intersection_y1 = self.y1
        else:
            return False
        if other.y2 <= self.y2 and other.y2 >= self.y1:
            intersection_y2 = other.y2
        elif other.y2 > self.y2 and other.y1 <= self.y2:
            intersection_y2 = self.y2
        else:
            return False
        
        width = intersection_x2 - intersection_x1 + 1
        height = intersection_y2 - intersection_y1 + 1
        assert(width >= 0)
        assert(height >= 0)
        intersection_size = width * height
        percent_overlap = round(intersection_size * 100.0 / other.size)
        
        return percent_overlap > percent    

    def point_within_self(self, x, y):
        
        assert(self.x1 <= self.x2)
        assert(self.y1 <= self.y2)
        return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2
    
    def merge(self, other):
        
        if other.x1 < self.x1:
            self.x1 = other.x1
        if other.x2 > self.x2:
            self.x2 = other.x2
        if other.y1 < self.y1:
            self.y1 = other.y1
        if other.y2 > self.y2:
            self.y2 = other.y2

        assert(self.x1 <= self.x2)
        assert(self.y1 <= self.y2)


    def copy(self):
        
        return BoundingBox(self.x1, self.y1, self.x2, self.y2)
    
    width = property(lambda self: self.x2 - self.x1 + 1)            
    height = property(lambda self: self.y2 - self.y1 + 1)            
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)
    coordinates = property(lambda self: (self.x1, self.y1, self.x2, self.y2))
    
    def __str__(self):
        
        return "(%d,%d|%d,%d)" % (self.x1, self.y1, self.x2, self.y2)

    def __eq__(self, other):
       
        return self.x1 == other.x1 and \
            self.x2 == other.x2 and \
            self.y1 == other.y1 and \
            self.y2 == other.y2
    
    def __lt__(self, other):
        
        if self.__eq__(other):
            return False

        if self.y1 == other.y1:
            if self.x1 == other.x1:
                if self.y2 == other.y2:
                    return self.x2 < other.x2
                else:
                    return self.y2 < other.y2
            else:
                return self.x1 < other.x1
        else:
            return self.y1 < other.y1

    def __le__(self, other):
        
        return self.__eq__(other) or self.__lt__(other)
    
    def __gt__(self, other):

        return other.__lt__(self)        

    def __ge__(self, other):

        return  self.__eq__(other) or other.__lt__(self)        


class AutoPage(Page):
    
    def __init__(self, 
                 img: Image):
        
        self.img = img
        self.main_region = Region(0, 0, img.width, img.height)
        self.rotation_angle = 0
        self.additional_rotation_angle = 0
        self.sub_regions = []
        self.skip_page = False
        self.current_sub_region_no = 0

    def get_raw_image(self):
        
        return self.img

class SegmentationService(object):
    
    def __init__(self,
                 ndarray_service: NdArrayService,
                 binarization_service: BinarizationService,
                 smearing_service: SmearingService,
                 orientation_service: OrientationCorrectionService,
                 angle_correction_service: AngleCorrectionService):
        
        self.ndarray_service = ndarray_service
        self.binarization_service = binarization_service
        self.smearing_service = smearing_service
        self.orientation_service = orientation_service
        self.angle_correction_service = angle_correction_service
        
    def preprocess_page(self, page: Page):
        
        img = page.get_raw_image()
        img = self.orientation_service.correct_orientation(img)
        img = self.angle_correction_service.correct_angle(img)
        
        return AutoPage(img)
    
    def detect_picture_regions(self, page: Page):
  
        smeared_ndarray = self._smear_page(page)
        segments = self._find_segments(smeared_ndarray)
        
    def _smear_page(self, page: Page):      
        bin_ndarray = self.binarization_service.binarize_otsu(page.get_raw_image())
        hor_smeared = self.smearing_service.smear_horizontal(bin_ndarray, 300)
        ver_smeared = self.smearing_service_service.smear_vertical(bin_ndarray, 500)
        combined = np.logical_or(hor_smeared, ver_smeared)
        final = self.smearing_service.smear_horizontal(combined, 20)

    def _find_segments(self, ndarray: np.ndarray):
        
        contours, _ = cv2.findContours(self.ndarray_service.convert_binary_to_inverted_gray(ndarray), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = []
        for contour in contours:
            
            bb = BoundingBox.create_from_cv2_bounding_box(cv2.boundingRect(contour))
            if bb.size > 600:
                bounding_boxes.append(bounding_boxes)
        
        