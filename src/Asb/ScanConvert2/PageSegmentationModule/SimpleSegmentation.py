'''
Created on 22.03.2023

@author: michael
'''
from Asb.ScanConvert2.PageSegmentationModule.Operations import SmearingService,\
    BinarizationService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage,\
    BINARY_BLACK, Segment, BoundingBox
from injector import inject
from PIL import Image
import numpy as np
import cv2
import math
from Asb.ScanConvert2.PageSegmentationModule.WahlWongCaseySegmentation import WahlWongCaseySegmentationService

class SimpleSegment(Segment):
    
    @classmethod
    def create_from_rectangle(cls, rectangle):
        
        points = cv2.boxPoints(rectangle)
        min_x = max_x = points[0][0]
        min_y = max_y = points[0][1]
        for point in points[1:]:
            if point[0] < min_x:
                min_x = point[0]
            if point[0] > max_x:
                max_x = point[0]
            if point[1] < min_y:
                min_y = point[1]
            if point[1] > max_y:
                max_y = point[1]
                
        return SimpleSegment(BoundingBox(min_x, min_y, max_x, max_y))
    
    def can_be_merged_conservatively(self, other):

        if self.bounding_box.overlaps_with(other.bounding_box):
            return True
        
        if not self.bounding_box.is_vertically_near(other.bounding_box, 6):
            return False
        
        if not self.bounding_box.is_horizontally_contained_in(other.bounding_box, 8):
            if not other.bounding_box.is_horizontally_contained_in(self.bounding_box, 8):
                return False
        
        if self.bounding_box.has_nearly_the_same_width(other.bounding_box, 0.98):
            return True

        return False
    
    def can_be_merged_boldly(self, other):

        if self.bounding_box.overlaps_with(other.bounding_box):
            return True
        
        if not self.bounding_box.is_vertically_near(other.bounding_box, 12):
            return False
        
        if not self.bounding_box.is_horizontally_contained_in(other.bounding_box, 10):
            if not other.bounding_box.is_horizontally_contained_in(self.bounding_box, 10):
                return False
        
        return True     

    def merge(self, other):
        
        if other.bounding_box.x1 < self.bounding_box.x1:
            self.bounding_box.x1 = other.bounding_box.x1
            
        if other.bounding_box.x2 > self.bounding_box.x2:
            self.bounding_box.x2 = other.bounding_box.x2
            
        if other.bounding_box.y1 < self.bounding_box.y1:
            self.bounding_box.y1 = other.bounding_box.y1
            
        if other.bounding_box.y2 > self.bounding_box.y2:
            self.bounding_box.y2 = other.bounding_box.y2
        
    def __str__(self):
        
        return "%s" % self.bounding_box

class SimpleSegmentationService(object):
    '''
    This mixes some ideas from Pavlidis / Zhou 1992 with some of my own.
    Preliminary segmentation is achieved by horizontal smearing (rather
    conservatively) and then using cv2 to get contours. We only take
    the outer contours, but these are still more than expected. Some
    contours have rather interesting shapes. So the bounding boxes may
    overlap or be contained within each others, although the contours
    do not.
    
    From the minimal rectangles enclosing the contours, we compute the
    rotation angle. This works quite reliable and fast. If the angle
    exceeds a threshold, we rotate the page accordingly and start again.
    
    Then we borrow from Pavlidis / Zhou the idea of merging segments, albeit
    with different parameters. Like them we do two merging passes. One
    rather conservatively. Here we start with the largest segments and go down
    to the smaller. This allows for removing small segments contained within
    other segments.
    
    The second pass goes from top to bottom and merges more freely (mostly
    shorter trailing lines at the end of paragraphs).
    '''

    @inject
    def __init__(self, wws_segmentation: WahlWongCaseySegmentationService, smearing_service: SmearingService, binarization_service: BinarizationService, ndarray_service: NdArrayService):
        '''
        Constructor
        '''
        self.wws_segmentation = wws_segmentation
        self.smearing_service = smearing_service
        self.binarization_service = binarization_service
        self.ndarray_service = ndarray_service
        
    def get_segmented_page(self, img: Image):
        
        rectangles = self._calculate_rectangles(img)
        angle = self._calculate_rotation_angle(rectangles)            
        if abs(angle) > 0.2:
            img = img.rotate(angle, expand=True, fillcolor="white")
            rectangles = self._calculate_rectangles(img)
        
        segments = []
        for rectangle in rectangles:
            segment = SimpleSegment.create_from_rectangle(rectangle)
            segments.append(segment)
            
        # First merge
        segments.sort(key=lambda x: x.size, reverse=True)
        
        merged_segments = []
        for child in segments:
            
            is_merged = False
            for parent in merged_segments:
                if parent.bounding_box.is_contained_within_self(child.bounding_box):
                    is_merged = True
                    break
                if parent.can_be_merged_conservatively(child):
                    parent.merge(child)
                    is_merged = True
                    break
            if not is_merged:
                merged_segments.append(child)
            
        segmented_page = SegmentedPage(img)
        segmented_page.segments = merged_segments
        
        segmented_page.segments = []
        merged_segments.sort(key=lambda x: x.bounding_box.y1)
        
        for child in merged_segments:
            
            is_merged = False
            for parent in segmented_page.segments:
                if parent.can_be_merged_boldly(child):
                    parent.merge(child)
                    is_merged = True
                    break
            if not is_merged:
                segmented_page.segments.append(child)
            #segmented_page.show_segments()
        
        return segmented_page
    
    def _calculate_rectangles(self, img: Image):

        binary_ndarray = self.binarization_service.binarize_otsu(img)
        smeared_ndarray = self.smearing_service.smear_horizontal(binary_ndarray, 30)
        smeared_ndarray_gray = self.ndarray_service.convert_binary_to_inverted_gray(smeared_ndarray)
        contours, _ = cv2.findContours(smeared_ndarray_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        for contour in contours:
            rectangle = cv2.minAreaRect(contour)
            rectangles.append(rectangle)

        return rectangles

    def _calculate_rotation_angle(self, rectangles):
        
        angles = []
        for rectangle in rectangles:
            line = self._find_long_side(rectangle)
            dy = line[1][1]-line[0][1]
            dx = line[1][0]-line[0][0]
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
            assert(abs(abs(angle1 - angle2) - 90.0) < 2.0)
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
        return math.sqrt(dx*dx + dy*dy)
