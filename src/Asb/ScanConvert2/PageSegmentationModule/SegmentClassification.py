'''
Created on 09.04.2023

@author: michael
'''
from Asb.ScanConvert2.PageSegmentationModule.Operations import RunLengthAlgorithmService,\
    BinarizationService
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage,\
    Segment, SegmentType
from PIL import Image
import numpy as np

class SegmentClassificationService(object):
    '''
    classdocs
    '''


    def __init__(self, run_length_algorithm_service: RunLengthAlgorithmService,
                 binarization_service: BinarizationService):
        '''
        Constructor
        '''
        self.rla_service = run_length_algorithm_service
        self.binarization_service = binarization_service
        
    def classify_segmented_page(self, segmented_page: SegmentedPage):
        
        for segment in segmented_page.segments:
            segment.segment_type = self._classify_segment(segment, segmented_page.original_img)
        
        return segmented_page
    
    def _classify_segment(self, segment: Segment, img: Image):
        
        if segment.segment_type != SegmentType.UNKNOWN:
            return segment.segment_type
        
        segment_img = img.crop(segment.coordinates)
        bin_ndarray = self.binarization_service.binarize_sauvola(segment_img)
        
        rla_stats = self.rla_service.calculate_run_lengths(bin_ndarray)
        
        d_min = np.minimum.reduce(rla_stats, axis=2)
        d_max = np.maximum.reduce(rla_stats, axis=2)
        
        d_min_mean = np.mean(d_min[d_min > 0])
        print("Mean minimum: %0.4f" % d_min_mean)
        d_max_mean = np.mean(d_max[d_max > 0])
        print("Mean maximum: %0.4f" % d_max_mean)
        print("Segment size: %d" % segment.size)
        white = np.sum(bin_ndarray)
        black = segment.size - white
        black_white_ratio = black / white
        print("Black/white ratio: %0.4f" % black_white_ratio)
        f1 = segment.size / (d_min_mean * d_min_mean)
        f2 = segment.size / (d_max_mean * d_max_mean)
        
        min_max_ratio = d_min_mean / d_max_mean
        print("Min/max ratio: %0.4f" % min_max_ratio)
        
        # Avoid division by 0
        d_min[d_min == 0] = 10000
        ecc = d_max / d_min
        ecc_mean = np.mean(ecc[d_min != 10000])
        
        print("F1: %0.4f" % f1)
        print("F2: %0.4f" % f2)
        print("Eccentricity: %0.4f" % ecc_mean)
        
        if min_max_ratio < 0.1:
            return SegmentType.DRAWING
        
        if d_max_mean > 100:
            return SegmentType.PHOTO
        
        return SegmentType.TEXT
