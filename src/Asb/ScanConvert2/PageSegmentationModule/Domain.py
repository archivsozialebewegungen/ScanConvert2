'''
Created on 20.03.2023

@author: michael
'''
from enum import Enum

from PIL import Image, ImageDraw, ImageFont
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

    @classmethod
    def create_from_rectangle(cls, rectangle):
        
        return BoundingBox(rectangle[0],
                           rectangle[1],
                           rectangle[0] + rectangle[2] - 1,
                           rectangle[1] + rectangle[3] - 1)

    def __init__(self, x1, y1, x2, y2):
        
        assert(x1 <= x2)
        assert(y1 <= y2)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.verbose = False

    def is_vertically_near(self, other, tolerance):

        upper_self = self.y1
        lower_self = self.y2
        upper_other = other.y1
        lower_other = other.y2
        
        return abs(lower_self-upper_other) < tolerance or abs(lower_other-upper_self) < tolerance
 
        return False
    
    def is_horizontally_contained_in(self, other, tolerance):
        
        return other.x1 - tolerance < self.x1 and other.x2 + tolerance > self.x1
    
    def has_nearly_the_same_width(self, other, coefficient):
        
        minimum = np.min([self.width, other.width])
        maximum = np.max([self.width, other.width])
        return minimum / maximum >= coefficient

    def aligns_left_at_the_bottom(self, other, v_tolerance, h_tolerance):
        
        v_distance = other.y1 - self.y2
        
        if v_distance < 0 or v_distance > v_tolerance:
            return False
        
        if other.x2 > self.x2 + h_tolerance:
            return False
        
        return abs(self.x1 - other.x1) < h_tolerance

    def intersects_with(self, other):
        
        if other.is_contained_within_self(self):
            return True
        if self.is_contained_within_self(other):
            return True
        if self.point_within_self(other.x1, other.y1):
            return True
        if self.point_within_self(other.x1, other.y2):
            return True
        if self.point_within_self(other.x2, other.y1):
            return True
        if self.point_within_self(other.x2, other.y2):
            return True
        return False
    
    def is_contained_within_self(self, other):
        
        if not self.point_within_self(other.x1, other.y1):
            return False
        if not self.point_within_self(other.x2, other.y2):
            return False
        
        return True
        

    def point_within_self(self, x, y):
        
        assert(self.x1 <= self.x2)
        assert(self.y1 <= self.y2)
        return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2
    
    def merge(self, other):
        
        if other.x1 < self.x1:
            self.x1 = other.x1
        if other.x2 > self.x2:
            self.x2 = other.x2
        if other.y1 < self.y1:
            self.y1 = other.y1
        if other.y2 > self.y2:
            self.y2 = other.y2

        assert(self.x1 <= self.x2)
        assert(self.y1 <= self.y2)


    def copy(self):
        
        return BoundingBox(self.x1, self.y1, self.x2, self.y2)
    
    width = property(lambda self: self.x2 - self.x1 + 1)            
    height = property(lambda self: self.y2 - self.y1 + 1)            
    size = property(lambda self: self.width * self.height)
    eccentricity = property(lambda self: self.width / self.height)
    coordinates = property(lambda self: (self.x1, self.y1, self.x2, self.y2))
    
    def __str__(self):
        
        return "(%d,%d|%d,%d)" % (self.x1, self.y1, self.x2, self.y2)

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

class ObjectWithBoundingBox(object):
    
    def __init__(self, bounding_box):
        
        self.bounding_box = bounding_box

    def __eq__(self, other):
        
        return self.bounding_box == other.bounding_box
            
    def __le__(self, other):
        
        return self < other or self == other
    
    def __lt__(self, other):
        
        if abs(self.bounding_box.y1 - other.bounding_box.y1) < 20:
            return self.bounding_box.x1 < other.bounding_box.x1
        else:
            return self.bounding_box.y1 < other.bounding_box.y1

    def __ge__(self, other):
        
        return self > other or self == other
        
    def __gt__(self, other):
        
        return other < self
    
    def __str__(self):
        
        return "%s" % self.bounding_box

        
    width = property(lambda self: self.bounding_box.width)
    height = property(lambda self: self.bounding_box.height)
    size = property(lambda self: self.bounding_box.size)
    coordinates = property(lambda self: self.bounding_box.coordinates)

class Segment(ObjectWithBoundingBox):
    
    def __init__(self, bounding_box: BoundingBox, segment_type: SegmentType = SegmentType.UNKNOWN):

        super().__init__(bounding_box)
        self.segment_type = segment_type
        
        
class SegmentedPage(object):
    
    def __init__(self, original_img: Image, segments):
        
        self.original_img = original_img
        self.segments = segments
        
    def _get_segments(self, segment_type: SegmentType=None):
        
        type_segments = []
        for segment in self.segments:
            if segment_type is None:
                type_segments.append(segment)
            elif segment.segment_type == segment_type:
                type_segments.append(segment)
        return type_segments
        
    def show_segments(self, segment_type = None):
        
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
                                width = 5)
        counter = 0
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf", 80)
        for segment in display_segments: 
            counter += 1
            draw_img.text([segment.bounding_box.x1,
                           segment.bounding_box.y1],
                           "%d" % counter,
                           fill="red",
                           font=font)
        
        out = Image.alpha_composite(background, foreground)
        out.show()

    def show_blocks(self):
        
        background = self.original_img.convert("RGBA")
        foreground = Image.new("RGBA", background.size, (255, 255, 255, 0))
        draw_img = ImageDraw.Draw(foreground)
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf", 80)
        counter = 0
        for block in self.bb_objects: 
            draw_img.rectangle([block.bounding_box.x1,
                                block.bounding_box.y1,
                                block.bounding_box.x2,
                                block.bounding_box.y2], 
                                fill = (0, 255, 0, 60),
                                outline =(0, 255, 0,255),
                                width = 5)
        for block in self.bb_objects: 
            counter += 1
            draw_img.text([block.bounding_box.x1,
                           block.bounding_box.y1],
                           "%d" % counter,
                           fill="red",
                           font=font)
        out = Image.alpha_composite(background, foreground)
        out.show()
                
    text_segments = property(lambda self: self._get_segments(SegmentType.TEXT))
    photo_segments = property(lambda self: self._get_segments(SegmentType.PHOTO))
    drawing_segments = property(lambda self: self._get_segments(SegmentType.DRAWING))
    border_segments = property(lambda self: self._get_segments(SegmentType.BORDER))
