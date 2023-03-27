'''
Created on 22.03.2023

@author: michael
'''
from Asb.ScanConvert2.PageSegmentationModule.Operations import SmearingService,\
    BinarizationService
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage,\
    BINARY_BLACK, Segment, BoundingBox, BINARY_WHITE
from injector import inject
from PIL import Image

class PavlidisZhouSegmentedPage(SegmentedPage):
    
    def __init__(self, original_img: Image):
        
        super().__init__(original_img)
        
        self.segments = []

    

class ColumnInterval(Segment):
    
    def can_be_merged(self, other, epsilon_1 = 3, epsilon_2 = 3, epsilon_3 = 0.98):

        if not self.bounding_box._is_vertically_near(other.bounding_box, epsilon_1):
            return False
        
        if not self.bounding_box._is_horizontally_contained_in(other.bounding_box, epsilon_2):
            if not other.bounding_box._is_horizontally_contained_in(self.bounding_box, epsilon_2):
                return False
        
        if epsilon_3 == None:
            return True

        if self.bounding_box._has_nearly_the_same_width(other.bounding_box, epsilon_3):
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
        
        return "%" % self.bounding_box
    

class PavlidisZhouSegmentationService(object):
    '''
    Glossary:
    
    horizontal| vertical projection profile
      The sum of black pixels in a row or column
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
        smeared_ndarray = self.smearing_service.smear_vertical(smeared_ndarray, 5, BINARY_WHITE)
        Image.fromarray(smeared_ndarray).show()
        #Image.fromarray(smeared_ndarray).show()
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
        segmented_page.show_segments()
        segmented_page.segments = self._merge_small_intervals(segmented_page.segments)
        segmented_page.show_segments()
                    
        return segmented_page
    
    def _merge_small_intervals(self, column_interval_list):
        
        initial_list_size = len(column_interval_list)
        print("Initialial list size: %d" % initial_list_size)
        merge_operations = 0
        
        final_column_interval_list = []
        merge_candidates = column_interval_list.copy()
        for column_interval in column_interval_list:
            # The paper does not state what "small" width or height means
            if column_interval.height > 10 or column_interval.width > 40:
                final_column_interval_list.append(column_interval)
                continue
            is_merged = False
            for merge_interval in merge_candidates:
                if merge_interval == column_interval:
                    continue
                if merge_interval.can_be_merged(column_interval, 20, 5, None):
                    merge_operations += 1
                    merge_interval.merge(column_interval)
                    is_merged = True
                    break
            if not is_merged:
                final_column_interval_list.append(column_interval)
        
        final_list_size = len(final_column_interval_list)
        print("Final list size: %d" % final_list_size)
        print("Merges: %d" % merge_operations)
        assert(final_list_size + merge_operations == initial_list_size)
        return final_column_interval_list
    
    def _is_segment_start(self, row_idx, start, end, segment_matrix):
        
        if row_idx == 0:
            return True
        
        upper_row = segment_matrix[row_idx - 1]
        current_row = segment_matrix[row_idx]
        