'''
Created on 20.03.2023

@author: michael
'''
from enum import Enum

from PIL import Image

import numpy as np

BINARY_BLACK = False
BINARY_WHITE = True
GRAY_BLACK = 0
GRAY_WHITE = 255

class SegmentType(Enum):
    
    UNKNOWN = 0
    TEXT = 1
    PHOTO = 2
    DRAWING = 3
    BORDER = 4

class BoundingBox(object):

    def __init__(self, x1, y1, x2, y2):
        
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __str__(self):
        
        return "(%d,%d|%d,%d)" % (self.x1, self.y1, self.x2, self.y2)

    width = property(lambda self: self.x2 - self.x1)            
    height = property(lambda self: self.y2 - self.y1)            
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)
    
class Segment(object):
    
    def __init__(self, bounding_box: BoundingBox, segment_type: SegmentType = SegmentType.UNKNOWN):
        
        self.bounding_box = bounding_box
        self.segment_type = segment_type
        
class SegmentedPage(object):
    
    def __init__(self, original_img: Image):
        
        self.original_img = original_img
        self.segments = []
        
    def _get_segments(self, segment_type: SegmentType):
        
        type_segments = []
        for segment in self.segments:
            if segment.segment_type == segment_type:
                type_segments. append(segment)
        return type_segments
    
    def add_segment(self, segment: Segment):
        
        self.segments.append(segment)

    text_segments = property(lambda self: self._get_segments(SegmentType.TEXT))
    photo_segments = property(lambda self: self._get_segments(SegmentType.PHOTO))
    drawing_segments = property(lambda self: self._get_segments(SegmentType.DRAWING))
    border_segments = property(lambda self: self._get_segments(SegmentType.BORDER))
