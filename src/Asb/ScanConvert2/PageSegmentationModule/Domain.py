'''
Created on 20.03.2023

@author: michael
'''
from enum import Enum

from PIL import Image, ImageDraw
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
        
        assert(x1 <= x2)
        assert(y1 <= y2)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def _is_vertically_near(self, other, tolerance):

        if self.y2 > other.y1:
            return self.y2 - other.y1 < tolerance
 
        return other.y2 - self.y1 < tolerance
    
    def _is_horizontally_contained_in(self, other, tolerance):
        
        return other.x1 - tolerance < self.x1 and other.x2 + tolerance > self.x1
    
    def _has_nearly_the_same_width(self, other, coefficient):
        
        minimum = np.min([self.width, other.width])
        maximum = np.max([self.width, other.width])
        return minimum / maximum >= coefficient

    def __str__(self):
        
        return "(%d,%d|%d,%d)" % (self.x1, self.y1, self.x2, self.y2)

    width = property(lambda self: self.x2 - self.x1 + 1)            
    height = property(lambda self: self.y2 - self.y1 + 1)            
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)
    coordinates = property(lambda self: (self.x1, self.y1, self.x2, self.y2))
    
    def __eq__(self, other):
        """
        This is slightly inconsistent - this operator is
        more exact than the other comparison operators, but it
        makes sense: The others are primarily for sorting while
        this is really for seeing if we have the same segment         
        """
        
        return self.x1 == other.x1 and \
            self.x2 == other.x2 and \
            self.y1 == other.y1 and \
            self.y2 == other.y2
    
    def __lt__(self, other):
        
        if self.y1 == other.y1:
            return self.x1 < other.x1
        else:
            return self.y1 < other.y1

    def __le__(self, other):
        
        if self.y1 == other.y1:
            return self.x1 <= other.x1
        else:
            return self.y1 <= other.y1
    
    def __gt__(self, other):
        
        if self.y1 == other.y1:
            return self.x1 > other.x1
        else:
            return self.y1 > other.y1

    def __ge__(self, other):
        
        if self.y1 == other.y1:
            return self.x1 >= other.x1
        else:
            return self.y1 >= other.y1
    
class Segment(object):
    
    def __init__(self, bounding_box: BoundingBox, segment_type: SegmentType = SegmentType.UNKNOWN):
        
        self.bounding_box = bounding_box
        self.segment_type = segment_type
        
    def __eq__(self, other):
        
        return self.bounding_box == other.bounding_box
            
    def __le__(self, other):
        
        return self.bounding_box <= other.bounding_box
        
    def __lt__(self, other):
        
        return self.bounding_box < other.bounding_box

    def __ge__(self, other):
        
        return self.bounding_box >= other.bounding_box
        
    def __gt__(self, other):
        
        return self.bounding_box > other.bounding_box

        
    width = property(lambda self: self.bounding_box.width)
    height = property(lambda self: self.bounding_box.height)
    size = property(lambda self: self.bounding_box.size)
    coordinates = property(lambda self: self.bounding_box.coordinates)
        
class SegmentedPage(object):
    
    def __init__(self, original_img: Image):
        
        self.original_img = original_img
        self.segments = []
        
    def _get_segments(self, segment_type: SegmentType):
        
        type_segments = []
        for segment in self.segments:
            if segment.segment_type == segment_type:
                type_segments.append(segment)
        return type_segments
    
    def add_segment(self, segment: Segment):
        
        self.segments.append(segment)
        
    def show_segments(self, segment_type = None):
        
        display_segments = self.segments
        if segment_type is not None:
            display_segments = self._get_segments(segment_type)
            
        background = self.original_img.convert("RGBA")
        foreground = Image.new("RGBA", background.size, (255, 255, 255, 0))
        draw_img = ImageDraw.Draw(foreground) 
        for segment in display_segments: 
            draw_img.rectangle([segment.bounding_box.x1,
                                segment.bounding_box.y1,
                                segment.bounding_box.x2,
                                segment.bounding_box.y2], 
                                fill = (255, 0, 0, 60),
                                outline =(255,0,0,255),
                                width = 1)
        out = Image.alpha_composite(background, foreground)
        out.show()


    text_segments = property(lambda self: self._get_segments(SegmentType.TEXT))
    photo_segments = property(lambda self: self._get_segments(SegmentType.PHOTO))
    drawing_segments = property(lambda self: self._get_segments(SegmentType.DRAWING))
    border_segments = property(lambda self: self._get_segments(SegmentType.BORDER))
