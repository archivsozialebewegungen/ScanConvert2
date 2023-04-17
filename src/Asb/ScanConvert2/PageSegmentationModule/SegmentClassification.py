'''
Created on 09.04.2023

@author: michael
'''
from PIL import Image

from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage, \
    Segment, SegmentType
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService, \
    BinarizationService
import numpy as np
from injector import singleton, inject


@singleton
class SegmentClassificationService(object):
    '''
    A service to classify segments according to their type.
    '''

    @inject
    def __init__(self, run_length_algorithm_service: RunLengthAlgorithmService,
                 binarization_service: BinarizationService):

        self.rla_service = run_length_algorithm_service
        self.binarization_service = binarization_service
        
    def classify_segmented_page(self, segmented_page: SegmentedPage):
        
        for segment in segmented_page.segments:
            segment.segment_type = self._classify_segment(segment, segmented_page.original_img)
        
        return segmented_page

    def _classify_segment_unfinished(self, segment: Segment, img: Image):

        if segment.segment_type != SegmentType.UNKNOWN:
            return segment.segment_type
        
        segment_img = img.crop(segment.coordinates)

        bin_ndarray = self.binarization_service.binarize_floyd_steinberg(segment_img)

        correlations = self._get_next_line_correlations(bin_ndarray)
        
        mean = np.mean(correlations)
        median = np.median(correlations)
        std_deviation = np.std(correlations)

        print("Mean: %0.3f Median: %0.3f Standard deviation: %0.3f" % (mean, median, std_deviation))        
        if mean > 0.5 and std_deviation < 0.25 and std_deviation > 0.1:
            return SegmentType.TEXT

        return SegmentType.DRAWING

    def _classify_segment(self, segment: Segment, img: Image):

        if segment.segment_type != SegmentType.UNKNOWN:
            return segment.segment_type
        
        segment_img = img.crop(segment.coordinates)

        bin_ndarray = self.binarization_service.binarize_otsu(segment_img)

        o_upper_mean, o_lower_mean, o_diff = self._calculate_correlations(bin_ndarray)
        
        if o_upper_mean > 0.7 and o_diff > 0.40:
            return SegmentType.TEXT

        if o_lower_mean < -0.1 or o_diff > 0.5:
            return SegmentType.PHOTO

        return SegmentType.DRAWING
        
    def _get_next_line_correlations(self, bin_ndarray):

        height = bin_ndarray.shape[0]
        correlations = []
        for line_idx in range(0, height - 1):
            correlations.append(self.rla_service.signal_cross_correlation(bin_ndarray, line_idx, 1))
        return correlations
    
    def _calculate_correlations(self, bin_ndarray):    

        height = bin_ndarray.shape[0]
        correlations = []
        for line_idx in range(0, height):
            for distance in range(1, height - line_idx):
                correlations.append(self.rla_service.signal_cross_correlation(bin_ndarray, line_idx, distance))
            
        corr_ndarray = np.array(correlations)
        corr_ndarray = np.sort(corr_ndarray)
        start_idx = int(corr_ndarray.shape[0]*0.7)
        upper_mean = np.mean(corr_ndarray[start_idx:])
        end_idx = int(corr_ndarray.shape[0]*0.3)
        lower_mean = np.mean(corr_ndarray[:end_idx])
        diff = upper_mean - lower_mean
        
        return (upper_mean, lower_mean, diff)
    
    def _classify_segment_wahl(self, segment: Segment, img: Image):
        '''
        This is quite slow and not very reliable.
        '''
        
        if segment.segment_type != SegmentType.UNKNOWN:
            return segment.segment_type
        
        segment_img = img.crop(segment.coordinates)
                
        bin_ndarray = self.binarization_service.binarize_sauvola(segment_img)
        
        rla_stats = self.rla_service.calculate_run_lengths(bin_ndarray)
        
        d_min = np.minimum.reduce(rla_stats, axis=2)
        d_max = np.maximum.reduce(rla_stats, axis=2)
        
        d_min_mean = np.mean(d_min[d_min > 0])
        d_max_mean = np.mean(d_max[d_max > 0])
        white = np.sum(bin_ndarray)
        black = segment.size - white
        black_white_ratio = black / white
        f1 = segment.size / (d_min_mean * d_min_mean)
        f2 = segment.size / (d_max_mean * d_max_mean)
        
        min_max_ratio = d_min_mean / d_max_mean
        
        # Avoid division by 0
        d_min[d_min == 0] = 10000
        ecc = d_max / d_min
        ecc_mean = np.mean(ecc[d_min != 10000])
        
        if min_max_ratio < 0.1:
            return SegmentType.DRAWING
        
        if d_max_mean > 100:
            return SegmentType.PHOTO
        
        return SegmentType.TEXT
