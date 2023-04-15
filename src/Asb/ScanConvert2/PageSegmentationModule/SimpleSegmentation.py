'''
Created on 22.03.2023

@author: michael
'''
import math

from PIL import Image
import cv2
from injector import inject
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage, \
    Segment, BoundingBox, SegmentType
from Asb.ScanConvert2.PageSegmentationModule.LineRemoving import LineRemovingService
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService, \
    BinarizationService, NdArrayService
from Asb.ScanConvert2.PageSegmentationModule.SegmentSorter import SegmentSorterService
import numpy as np
from Asb.ScanConvert2.PageSegmentationModule.SegmentClassification import SegmentClassificationService


class SimpleSegment(Segment):
    
    @classmethod
    def create_from_segment(cls, segment: Segment):
        
        assert(segment.segment_type is not None)
        return SimpleSegment(segment.bounding_box, segment.segment_type)
    
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
                 classification_service: SegmentClassificationService,
                 run_length_algorithm_service: RunLengthAlgorithmService,
                 binarization_service: BinarizationService,
                 ndarray_service: NdArrayService):
        '''
        Constructor
        '''
        self.sorter = sorter
        self.line_removing_service = line_removing_service
        self.classification_service = classification_service
        self.run_length_algorithm_service = run_length_algorithm_service
        self.binarization_service = binarization_service
        self.ndarray_service = ndarray_service
        self.skip_line_detection = False
        
    def get_segmented_page(self, img: Image):
        
        print("Step 1")
        # Step 1: Binarization
        bin_ndarray = self.binarization_service.binarize_otsu(img)
        
        print("Step 2")
        # Step 2: Remove borders and lines
        if not self.skip_line_detection:
            bin_ndarray, border_segments = self.line_removing_service.remove_lines(bin_ndarray)
        
        print("Step 3")
        # Step 3: Smear the binary input horizontally and get the
        # minimal inclosing rotated_rectangles 
        rotated_rectangles = self._calculate_rotated_rectangles(bin_ndarray)
        
        print("Step 4")
        # Step 4: Inspect the rotated rectangles and check if the original
        # image is slightly rotated
        angle = self._calculate_rotation_angle(rotated_rectangles)            
        
        print("Step 5")
        # Step 5 (optional): Rotate the image if necessary and repeat
        # steps 1 to 3
        if abs(angle) > 0.2:
            img = img.rotate(angle, expand=True, fillcolor="white")
            bin_ndarray = self.binarization_service.binarize_otsu(img)
            if not self.skip_line_detection:
                bin_ndarray, border_segments = self.line_removing_service.remove_lines(bin_ndarray)
        
        rotated_rectangles = self._calculate_rotated_rectangles(bin_ndarray)
        
        print("Step 6")
        # Step 6: Create Segments from the rotated rectangles
        segments = []
        for rectangle in rotated_rectangles:
            segment = SimpleSegment(BoundingBox.create_from_cv2_rotated_rectangle(rectangle))
            segments.append(segment)

        print("Step 7")
        # Step 7: Merge segments that seem to belong together
        segments = self._merge_segments(segments)
        
        print("Step 8")
        # Step 8: Add the detected border segments to improve sorting
        for segment in border_segments:
            segments.append(SimpleSegment.create_from_segment(segment))
            
        print("Step 9")
        # Step 9: Sort segments
        segments = self.sorter.sort_segments(segments)
        
        print("Step 10")
        # Step 10: Remove unnecessary border segment that lie within other
        # segments
        segmented_page = SegmentedPage(img, self._remove_border_segments(segments))
        
        print("Step 11")
        # Step 11: Classifiy the segments
        segmented_page = self.classification_service.classify_segmented_page(segmented_page)
        
        print("Step 12")
        # Step 12: Remove very small "photos" and "drawings"
        segmented_page = self._remove_small_illustrations(segmented_page)

        print("Step 13")
        segmented_page = self._merge_text_segments_into_columns(segmented_page)
        
        print("Step 14")
        segmented_page.segments = self.sorter.sort_segments(segmented_page.segments)
        return segmented_page
    
    def _remove_small_illustrations(self, segmented_page):

        removable_segments = []
        for segment in segmented_page.segments:
            if segment.size < 50:
                removable_segments.append(segment)
                
        for segment in removable_segments:
            segmented_page.segments.remove(segment)
                    
        return segmented_page
    
    def _remove_border_segments(self, segments):

        removable_border_segments = []
        for segment in segments:
            if segment.segment_type == SegmentType.BORDER:
                for other_segment in segments:
                    if segment.bounding_box == other_segment.bounding_box:
                        continue
                    if other_segment.bounding_box.is_contained_within_self(segment.bounding_box, 90):
                        removable_border_segments.append(segment)
                        break

        for segment in removable_border_segments:
            segments.remove(segment)
            
        return segments
    
    def _merge_text_segments_into_columns(self, segmented_page):

        new_segment_list = []
        segmented_page.segments.sort()
        while len(segmented_page.segments) > 0:
            current_segment = segmented_page.segments.pop(0)
            new_segment_list.append(current_segment)
            if current_segment.segment_type != SegmentType.TEXT:
                continue
            mergable_segment = self._find_mergable_text_segment(current_segment, new_segment_list + segmented_page.segments)
            while mergable_segment is not None:
                current_segment.merge(mergable_segment)
                segmented_page.segments.remove(mergable_segment)
                mergable_segment = self._find_mergable_text_segment(current_segment, new_segment_list + segmented_page.segments)
        
        segmented_page.segments = new_segment_list
        
        return segmented_page
    
    def _find_mergable_text_segment(self, current, segments):
        
        for segment in segments:
            if segment.segment_type != SegmentType.TEXT:
                continue
            if segment == current:
                continue
            if (not segment.bounding_box.is_horizontally_contained_in(current.bounding_box, 10)) and \
                (not current.bounding_box.is_horizontally_contained_in(segment.bounding_box, 10)):
                continue
            if self._are_mergable_without_collision(current, segment, segments):
                return segment
        return None
        
        
    def _are_mergable_without_collision(self, segment1, segment2, segments):
        
        test_bounding_box = segment1.bounding_box.copy()
        test_bounding_box.merge(segment2.bounding_box)
        for segment in segments:
            if segment == segment1 or segment == segment2:
                continue
            if test_bounding_box.intersects_with(segment.bounding_box):
                return False
        return True
    
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

        smeared_ndarray = self.run_length_algorithm_service.smear_horizontal(bin_ndarray, 40)
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
