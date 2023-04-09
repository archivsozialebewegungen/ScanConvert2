'''
Created on 22.03.2023

@author: michael
'''
import math

from PIL import Image
import cv2
from injector import inject
from numpy.array_api._dtypes import uint8

from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage, \
    Segment, BoundingBox, SegmentType, GRAY_WHITE
from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService, \
    BinarizationService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.SegmentSorter import SegmentSorterService
import numpy as np


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

        if self.bounding_box.intersects_with(other.bounding_box):
            return True
        
        if not self.bounding_box.is_vertically_near(other.bounding_box, 12):
            return False
        
        if not self.bounding_box.is_horizontally_contained_in(other.bounding_box, 24):
            if not other.bounding_box.is_horizontally_contained_in(self.bounding_box, 24):
                return False
        
        if self.bounding_box.has_nearly_the_same_width(other.bounding_box, 0.96):
            return True

        return False
    
    def can_be_merged_boldly(self, other):

        if self.bounding_box.intersects_with(other.bounding_box):
            return True
        
        if self.bounding_box.aligns_left_at_the_bottom(other.bounding_box, 12, 24):
            return True
        
        return False
        
    def merge(self, other):
        
        if other.bounding_box.x1 < self.bounding_box.x1:
            self.bounding_box.x1 = other.bounding_box.x1
            
        if other.bounding_box.x2 > self.bounding_box.x2:
            self.bounding_box.x2 = other.bounding_box.x2
            
        if other.bounding_box.y1 < self.bounding_box.y1:
            self.bounding_box.y1 = other.bounding_box.y1
            
        if other.bounding_box.y2 > self.bounding_box.y2:
            self.bounding_box.y2 = other.bounding_box.y2
        
class ContourClassificationService(object):
    
    def __init__(self, run_length_algorithm_service: RunLengthAlgorithmService()):
        
        self.run_length_algorithm_service = run_length_algorithm_service
    

    def classify_segment(self, img, segment):
        
        img = img.convert("L")
        img_ndarray = np.array(img)
        mask = self._get_segment_mask(segment, img_ndarray.shape)
        
        img_ndarray[mask > 0] = GRAY_WHITE
        
        img = Image.fromarray(img_ndarray)
        img.show()
        
        return SegmentType.UNKNOWN
    
    def _get_segment_mask(self, segment, shape):

        drawing_ndarray = np.zeros(shape, dtype=uint8)
        cv2.drawContours(drawing_ndarray, segment.contours, 0, 255, cv2.FILLED)
        img = Image.fromarray(drawing_ndarray)
        img.show()
        child_segments = segment.find_children()
        for child_segment in child_segments:
            cv2.drawContours(drawing_ndarray, child_segment.contours, -1, 0, cv2.FILLED)
            
        return drawing_ndarray
            

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
    def __init__(self,
                 sorter: SegmentSorterService,
                 line_removing_service: LineRemovingService,
                 run_length_algorithm_service: RunLengthAlgorithmService,
                 binarization_service: BinarizationService,
                 ndarray_service: NdArrayService):
        '''
        Constructor
        '''
        self.sorter = sorter
        self.line_removing_service = line_removing_service
        self.run_length_algorithm_service = run_length_algorithm_service
        self.binarization_service = binarization_service
        self.ndarray_service = ndarray_service
        self.skip_line_detection = False
        
    def get_segmented_page(self, img: Image):
        
        # Step 1: Binarization
        bin_ndarray = self.binarization_service.binarize_otsu(img)
        
        # Step 2: Remove borders and lines
        if not self.skip_line_detection:
            bin_ndarray = self.line_removing_service.remove_lines(bin_ndarray)
        
        # Step 3: Smear the binary input horizontally and get the
        # minimal inclosing rotated_rectangles 
        rotated_rectangles = self._calculate_rotated_rectangles(bin_ndarray)
        
        # Step 4: Inspect the rotated rectangles and check if the original
        # image is slightly rotated
        angle = self._calculate_rotation_angle(rotated_rectangles)            
        
        # Step 5 (optional): Rotate the image if necessary and repeat
        # steps 1 to 3
        if abs(angle) > 0.2:
            img = img.rotate(angle, expand=True, fillcolor="white")
            bin_ndarray = self.binarization_service.binarize_otsu(img)
            if not self.skip_line_detection:
                bin_ndarray = self.line_removing_service.remove_lines(bin_ndarray)
        
        rotated_rectangles = self._calculate_rotated_rectangles(bin_ndarray)
        
        # Step 6: Create Segments from the rotated rectangles
        segments = []
        for rectangle in rotated_rectangles:
            segment = SimpleSegment.create_from_rectangle(rectangle)
            segments.append(segment)

        segments = self._merge_segments(segments)

        segments = self.sorter.sort_segments(segments)

        segmented_page = SegmentedPage(img, segments)
        
        return segmented_page
    
    def _merge_segments(self, segments):
        
        segments = self._merge_intersections(segments)
        segments = self._merge_conservatively(segments)
        segments = self._merge_boldly(segments)
        return self._merge_intersections(segments)
    
    def _merge_conservatively(self, segments):

        segments.sort(key=lambda x: x.size, reverse=True)
        
        merged_segments = []
        for child in segments:
            
            is_merged = False
            for parent in merged_segments:
                if parent.can_be_merged_conservatively(child):
                    parent.merge(child)
                    is_merged = True
                    break
            if not is_merged:
                merged_segments.append(child)

        return merged_segments
    
    def _merge_boldly(self, segments):

        merged_segments = []
    
        segments.sort()
        
        for child in segments:
            
            is_merged = False
            for parent in merged_segments:
                if parent.can_be_merged_boldly(child):
                    parent.merge(child)
                    is_merged = True
                    break
            if not is_merged:
                merged_segments.append(child)
    
        return merged_segments

    def _merge_intersections(self, segments):
        
        no_of_segments = len(segments)
        segments = self._merge_intersections_loop(segments)
        while len(segments) < no_of_segments:
            no_of_segments = len(segments)
            segments = self._merge_intersections_loop(segments)
        return segments
    
    def _merge_intersections_loop(self, segments):

        segments.sort(key=lambda x: x.size, reverse=True)
        merged_segments = []
        for child in segments:
            is_merged = False
            for parent in merged_segments:
                if parent.bounding_box.intersects_with(child.bounding_box):
                    parent.merge(child)
                    is_merged = True
                    break
            if not is_merged:
                merged_segments.append(child)
            
        return merged_segments
    

    def _calculate_rotated_rectangles(self, bin_ndarray):

        smeared_ndarray = self.run_length_algorithm_service.smear_horizontal(bin_ndarray, 30)
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
        return math.sqrt(dx * dx + dy * dy)
