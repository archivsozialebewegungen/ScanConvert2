'''
Created on 19.02.2023

@author: michael

This module implements the page segmentations algorithm described in
"Block Segmentation and Text Extraction in Mixed Text/Image Documents"
by FRIEDRICH M. WAHL, KWAN Y. WONG, AND RICHARD G. CASEY
(https://doi.org/10.1016/0146-664X(82)90059-4)

There are two modifications: We added a criterium to detect border
frames (via black / white ratio) and we distinguish between photos
and drawings (also unsing the black / white ratio).
'''

from PIL import Image
from Asb.ScanConvert2.ScanConvertDomain import Region

from injector import singleton, inject
from Asb.ScanConvert2.PageSegmentationModule.WahlWongCaseySegmentation import WahlWongCaseySegmentationService
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentType
from Asb.ScanConvert2.Algorithms import Algorithm


@singleton
class SegmentationService(object):
    '''
    classdocs
    '''
    
    @inject
    def __init__(self, implementation: WahlWongCaseySegmentationService):
        
        self.implementation = implementation

    def find_photos(self, img: Image) -> []:
    
        segmented_page = self.implementation.get_segmented_page(img)
        regions = []
        for segment in segmented_page.segments:
            if segment.type == SegmentType.PHOTO:
                regions.append(Region(segment.bounding_box.x1,
                                      segment.bounding_box.y1,
                                      segment.bounding_box.width,
                                      segment.bounding_box.height,
                                      Algorithm.FLOYD_STEINBERG))
        return regions
