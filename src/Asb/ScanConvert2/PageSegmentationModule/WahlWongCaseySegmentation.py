'''
Created on 20.03.2023

@author: michael
'''
from PIL import Image
import cv2
from injector import inject, singleton
from numpy.core.records import ndarray

from Asb.ScanConvert2.PageSegmentationModule.Domain import Segment, BoundingBox, \
    SegmentedPage, BINARY_WHITE, SegmentType
from Asb.ScanConvert2.PageSegmentationModule.Operations import SmearingService, \
    BinarizationService, NdArrayService, ImageStatisticsService
import numpy as np

class NoMeaningfulTextFoundException(Exception):
    
    pass

class WahlWongCaseySegment(Segment):
    
    def __init__(self, label: int, label_matrix: ndarray, stats: []):
        
        super().__init__(BoundingBox(stats[cv2.CC_STAT_LEFT],
                                     stats[cv2.CC_STAT_TOP],
                                     stats[cv2.CC_STAT_LEFT] + stats[cv2.CC_STAT_WIDTH],
                                     stats[cv2.CC_STAT_TOP] + stats[cv2.CC_STAT_HEIGHT]
                                     ))
        self.label = label
        self.label_matrix = label_matrix
        self.stats = stats
        self.black_count = stats[cv2.CC_STAT_AREA]
        self.height = self.bounding_box.height
        self.eccentricity = self.bounding_box.eccentricity
        self.shape = self.black_count / self.bounding_box.size

        self.transition_count = None
        self.transition_ratio = None
        self.original_black_count = None

        self.bw_ratio = None
        self.smeared_bw_ratio = None
        self.smearing_coeffizient = None
        
    def is_probably_textsegment(self):

        if self.transition_ratio == 0:
            return False
        
        h_tr_ratio = self.height / self.transition_ratio
        
        if h_tr_ratio < 4:
            return False
        
        if self.height > 100:
            return False
        
        if self.eccentricity < 10:
            return False
        
        if self.shape < 0.5:
            return False
        
        return True


class WahlWongCaseySegmentedPage(SegmentedPage):
    
    def __init__(self, original_img: Image, binary_ndarray: ndarray, smeared_binary_ndarray: ndarray):
    
        super().__init__(original_img)
        self.binary_ndarray = binary_ndarray
        self.smeared_binary_ndarray = smeared_binary_ndarray
        
        self.mean_height = None
        self.mean_transition_ratio = None
        self.height_standard_deviation = None
        self.transition_ratio_standard_deviation = None


@singleton
class WahlWongCaseySegmentationService(object):
    
    @inject
    def __init__(self,
                 smearing_service: SmearingService,
                 binarization_service: BinarizationService,
                 ndarray_sevice: NdArrayService,
                 image_statistics_service: ImageStatisticsService):
        
        self.smearing_service = smearing_service
        self.binarization_service = binarization_service
        self.ndarray_service = ndarray_sevice
        self.image_statistics_service = image_statistics_service
        
    def get_segmented_page(self, img: Image):

        binary_ndarray = self.binarization_service.binarize_otsu(img)
        smeared_binary_ndarray = self._smear_image(binary_ndarray)
        segmented_page = WahlWongCaseySegmentedPage(img, binary_ndarray, smeared_binary_ndarray)
        segmented_page = self._find_segments(segmented_page)
        segmented_page = self._calculate_page_statistics(segmented_page)
        segmented_page = self._classify_segments(segmented_page)
        
        return segmented_page
        
    
    def _find_segments(self, segmented_page: WahlWongCaseySegmentedPage) -> SegmentedPage:
        
        smeared_gray_ndarray = self.ndarray_service.convert_binary_to_inverted_gray(segmented_page.smeared_binary_ndarray)
        connectivity = 4
        no_of_components, label_matrix, stats, centroids = cv2.connectedComponentsWithStats(smeared_gray_ndarray, connectivity)
        for label in range(1, no_of_components):
            segment = WahlWongCaseySegment(label, label_matrix, stats[label])
            segment.transition_count = self.image_statistics_service.count_transitions(
                segmented_page.binary_ndarray,
                segment.bounding_box)
            if  segment.transition_count == 0:
                # Ignore white segment empedded in Black segment
                continue
            segment = self._calculate_segment_statistics(segment, segmented_page)
            segmented_page.add_segment(segment)
    
        return segmented_page
    
    def _smear_image(self, binary_ndarray: ndarray) -> ndarray:
        
        print("First horizontal smear")
        hor_smeared = self.smearing_service.smear_horizontal(binary_ndarray, 300)
        print("Vertical smear")
        ver_smeared = self.smearing_service.smear_vertical(binary_ndarray, 500)
        print("Second horizontal smear")
        combined = np.logical_or(hor_smeared, ver_smeared)
        final = self.smearing_service.smear_horizontal(combined, 20)
        print("Smearing done.")
        return final
    
    def _calculate_segment_statistics(self, segment: Segment, segmented_page: SegmentedPage) -> Segment:
        
        segment.original_black_count = self._calculate_original_black_count(segment, segmented_page.binary_ndarray)
        segment.transition_ratio = segment.original_black_count / segment.transition_count
        
        whites = segment.bounding_box.size - segment.original_black_count
        if whites == 0:
            segment.bw_ratio = 10000
        else:
            segment.bw_ratio = segment.original_black_count / whites
    
        whites = segment.bounding_box.size - segment.black_count
        if whites == 0:
            segment.smeared_bw_ratio = 10000
        else:
            segment.smeared_bw_ratio = segment.original_black_count / whites
    
        segment.smearing_coeffizient = segment.smeared_bw_ratio / segment.bw_ratio

        return segment
    
    def _calculate_original_black_count(self, segment: Segment, binary_ndarray: ndarray):
        
        bin_copy = binary_ndarray.copy()
        bin_copy[segment.label_matrix != segment.label] = BINARY_WHITE
        count = bin_copy.shape[0] * bin_copy.shape[1] - np.count_nonzero(bin_copy)
        assert(count >= 0)
        
        return count

    
    def _calculate_page_statistics(self, segmented_page: SegmentedPage) -> SegmentedPage:
        
        text_segments = self._get_text_segment_cluster(segmented_page)
        
        height_array = []
        transition_ratio_array = []
        for segment in text_segments:
            height_array.append(segment.height)
            transition_ratio_array.append(segment.transition_ratio)
            
        segmented_page.mean_height = np.mean(height_array)
        segmented_page.mean_transition_ratio = np.mean(transition_ratio_array)
        segmented_page.height_standard_deviation = np.std(height_array)
        segmented_page.transition_ratio_standard_deviation = np.std(transition_ratio_array)
        
        return segmented_page
    
    def _get_text_segment_cluster(self, segmented_page) -> []:

        text_segments = []
        for segment in segmented_page.segments:
            if segment.is_probably_textsegment():
                text_segments.append(segment)
        return text_segments

    def _calculate_means_and_standard_deviations(self, text_segments):     

        height_array = []
        transition_ratio_array = []
        for segment in text_segments:
            height_array.append(segment.height)
            transition_ratio_array.append(segment.transition_ratio)
            
        mean_height = np.mean(height_array)
        mean_transition_ratio = np.mean(transition_ratio_array)
        height_standard_deviation = np.std(height_array)
        transition_ratio_standard_deviation = np.std(transition_ratio_array)
            
        return mean_height, height_standard_deviation, mean_transition_ratio, transition_ratio_standard_deviation

    def _verify_text_infos(self):
        
        return
        
        if self.height_mean < 60 \
            and self.transition_ratio_mean < 8 \
            and self.height_standard_deviation < 5 \
            and self.transition_ratio_standard_deviation < 2 \
            and self.height_standard_deviation / self.height_mean < 0.5 \
            and self.transition_ratio_standard_deviation / self.transition_ratio_mean < 0.5:
            return
        
        raise NoMeaningfulTextFoundException()

    
    def _classify_segments(self, segmented_page: SegmentedPage) -> SegmentedPage:
        
        for segment in segmented_page.segments:
            
            segment.type = SegmentType.BORDER
            
            if segment.bw_ratio < 0.1:
                # Just a black border frame with lot of white inside
                continue
            
            if segment.height <= 3 * segmented_page.mean_height:
                if segment.transition_ratio <= 3 * segmented_page.mean_transition_ratio:
                    # Text
                    segment.type = SegmentType.TEXT
            else:
                if segment.eccentricity > 1 / 5:
                    # Picture
                    if segment.bw_ratio > 0.5:
                        segment.type = SegmentType.PHOTO
                    else:
                        segment.type = SegmentType.DRAWING

        return segmented_page
