'''
Created on 22.03.2023

@author: michael
'''
from Asb.ScanConvert2.PageSegmentationModule.Operations import SmearingService,\
    BinarizationService
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage,\
    BINARY_BLACK, Segment, BoundingBox
from injector import inject
from PIL import Image

class PavlidisZhouSegmentedPage(SegmentedPage):
    
    def __init__(self, original_img: Image):
        
        super().__init__(original_img)
        
        self.segments = []

    

class ColumnInterval(Segment):
    
    def can_be_merged(self, other, epsilon_1 = 3, epsilon_2 = 3, epsilon_3 = 0.98):

        if not self.bounding_box.is_vertically_near(other.bounding_box, epsilon_1):
            return False
        
        if not self.bounding_box.is_horizontally_contained_in(other.bounding_box, epsilon_2):
            if not other.bounding_box.is_horizontally_contained_in(self.bounding_box, epsilon_2):
                return False
        
        if epsilon_3 == None:
            return True

        if self.bounding_box.has_nearly_the_same_width(other.bounding_box, epsilon_3):
            return True
        
        return False        
    
    def merge(self, other):
        
        old_size = self.bounding_box.size
        
        if other.bounding_box.x1 < self.bounding_box.x1:
            self.bounding_box.x1 = other.bounding_box.x1
            
        if other.bounding_box.x2 > self.bounding_box.x2:
            self.bounding_box.x2 = other.bounding_box.x2
            
        if other.bounding_box.y1 < self.bounding_box.y1:
            self.bounding_box.y1 = other.bounding_box.y1
            
        if other.bounding_box.y2 > self.bounding_box.y2:
            self.bounding_box.y2 = other.bounding_box.y2
        
        new_size = self.bounding_box.size
        assert(new_size >= old_size)
        
    def __str__(self):
        
        return "%s" % self.bounding_box
    

class PavlidisZhouSegmentationService(object):
    '''
    '''

    @inject
    def __init__(self, smearing_service: SmearingService, binarization_service: BinarizationService):
        '''
        Constructor
        '''
        self.smearing_service = smearing_service
        self.binarization_service = binarization_service
        
    def get_segmented_page(self, img: Image):
        
        print("Start binarization")
        binary_ndarray = self.binarization_service.binarize_otsu(img)
        print("Start smearing")
        # Remove white space between characters
        smeared_ndarray = self.smearing_service.smear_horizontal(binary_ndarray, 35)
        # Remove black noise in column gaps
        #smeared_ndarray = self.smearing_service.smear_vertical(smeared_ndarray, 5, BINARY_WHITE)
        print("Start segmentation")
        segmented_page = self._assemble_segment_matrix(smeared_ndarray, SegmentedPage(img))
        print("End Segmentation")
        
        return segmented_page
    
    def _assemble_segment_matrix(self, smeared_ndarray, segmented_page):

        width = smeared_ndarray.shape[1]
        height = smeared_ndarray.shape[0]
        this_row_segments = []
        for row_idx in range(0, height):
            last_row_segments = this_row_segments
            this_row_segments = []
            black_start = None
            black_end = None
            for col_idx in range(0, width):
                if smeared_ndarray[row_idx, col_idx] == BINARY_BLACK:
                    if black_start == None:
                        black_start = black_end = col_idx
                    else:
                        black_end = col_idx
                else:
                    if black_start == None:
                        continue
                    new_column_interval = ColumnInterval(BoundingBox(black_start, row_idx, black_end, row_idx))
                    black_start = black_end = None
                    is_merged = False
                    for column_interval in last_row_segments:
                        if column_interval.can_be_merged(new_column_interval):
                            column_interval.merge(new_column_interval)
                            this_row_segments.append(column_interval)
                            is_merged = True
                            break
        
                    if not is_merged:
                        segmented_page.segments.append(new_column_interval)
                        this_row_segments.append(new_column_interval)

        segmented_page.segments = self._merge_small_intervals(segmented_page.segments)
                    
        return segmented_page
    
    def _merge_small_intervals(self, column_interval_list):
        '''
        Tries to merge as much small intervals as possible into
        large intervals
        '''
        # Splitting into small and large column
        small_column_intervals = []
        large_column_intervals = []
        for column_interval in column_interval_list:
            # The paper does not state what "small" width or height means
            if column_interval.height > 30 or column_interval.width > 15:
                large_column_intervals.append(column_interval)
            else:
                small_column_intervals.append(column_interval)
        
        # We need at least one parent interval
        if len(large_column_intervals) == 0:
            large_column_intervals.append(small_column_intervals.pop())
            
        large_column_intervals.sort(key=lambda interval: interval.size, reverse=True)
        
        found_something_to_merge = True
        while len(small_column_intervals) > 0 and found_something_to_merge:
            found_something_to_merge = False
            # We can't remove while looping over the list
            # so we just not, which small intervals are already
            # merged
            for parent_interval in large_column_intervals:
                merged_list = []
                for s_idx in range(0, len(small_column_intervals)):
                    if s_idx in merged_list:
                        continue
                    if parent_interval.can_be_merged(small_column_intervals[s_idx], 20, 5, None):
                        parent_interval.merge(small_column_intervals[s_idx])
                        merged_list.append(s_idx)
                        found_something_to_merge = True
            
                merged_list.sort(reverse=True)
                for s_idx in merged_list:
                    del small_column_intervals[s_idx]

        final_list = large_column_intervals + small_column_intervals
        final_list.sort()
        return final_list
        