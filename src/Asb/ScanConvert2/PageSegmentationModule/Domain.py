'''
Created on 20.03.2023

@author: michael
'''
from enum import Enum

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

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

border_colors = {
    SegmentType.UNKNOWN: (255, 255, 0, 255),
    SegmentType.TEXT: (255, 0, 0, 255),
    SegmentType.PHOTO: (0, 255, 0, 255),
    SegmentType.DRAWING: (0, 0, 255, 255),
    SegmentType.BORDER: (0, 255, 255, 255),
    }

fill_colors = {
    SegmentType.UNKNOWN: (255, 255, 0, 60),
    SegmentType.TEXT: (255, 0, 0, 60),
    SegmentType.PHOTO: (0, 255, 0, 60),
    SegmentType.DRAWING: (0, 0, 255, 60),
    SegmentType.BORDER: (0, 255, 255, 60),
    }

class BoundingBox(object):

    @classmethod
    def create_from_cv2_bounding_box(cls, cv2_bounding_box):
        
        return BoundingBox(cv2_bounding_box[0],
                           cv2_bounding_box[1],
                           cv2_bounding_box[0] + cv2_bounding_box[2] - 1,
                           cv2_bounding_box[1] + cv2_bounding_box[3] - 1)

    @classmethod
    def create_from_cv2_rotated_rectangle(cls, cv2_rotated_rectangle):
        
        points = cv2.boxPoints(cv2_rotated_rectangle)
        x1 = x2 = points[0][0]
        y1 = y2 = points[0][1]
        for point in points[1:]:
            if point[0] < x1:
                x1 = point[0]
            if point[0] > x2:
                x2 = point[0]
            if point[1] < y1:
                y1 = point[1]
            if point[1] > y2:
                y2 = point[1]
        
        return BoundingBox(round(x1), round(y1), round(x2), round(y2))

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
        
        return other.x1 - tolerance < self.x1 and other.x2 + tolerance > self.x2
    
    
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
    
    def is_contained_within_self(self, other, percent=100):
        
        if percent == 100:
        
            if not self.point_within_self(other.x1, other.y1):
                return False
            if not self.point_within_self(other.x2, other.y2):
                return False
        
        if other.x1 >= self.x1 and other.x1 <= self.x2:
            intersection_x1 = other.x1
        elif other.x1 < self.x1 and other.x2 >= self.x1:
            intersection_x1 = self.x1
        else:
            return False
        if other.x2 <= self.x2 and other.x2 >= self.x1:
            intersection_x2 = other.x2
        elif other.x2 > self.x2 and other.x1 <= self.x2:
            intersection_x2 = self.x2
        else:
            return False
        if other.y1 >= self.y1 and other.y1 <= self.y2:
            intersection_y1 = other.y1
        elif other.y1 < self.y1 and other.y2 >= self.y1:
            intersection_y1 = self.y1
        else:
            return False
        if other.y2 <= self.y2 and other.y2 >= self.y1:
            intersection_y2 = other.y2
        elif other.y2 > self.y2 and other.y1 <= self.y2:
            intersection_y2 = self.y2
        else:
            return False
        
        width = intersection_x2 - intersection_x1 + 1
        height = intersection_y2 - intersection_y1 + 1
        assert(width >= 0)
        assert(height >= 0)
        intersection_size = width * height
        percent_overlap = round(intersection_size * 100.0 / other.size)
        
        return percent_overlap > percent    

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
       
        return self.x1 == other.x1 and \
            self.x2 == other.x2 and \
            self.y1 == other.y1 and \
            self.y2 == other.y2
    
    def __lt__(self, other):
        
        if self.__eq__(other):
            return False

        if self.y1 == other.y1:
            if self.x1 == other.x1:
                if self.y2 == other.y2:
                    return self.x2 < other.x2
                else:
                    return self.y2 < other.y2
            else:
                return self.x1 < other.x1
        else:
            return self.y1 < other.y1

    def __le__(self, other):
        
        return self.__eq__(other) or self.__lt__(other)
    
    def __gt__(self, other):

        return other.__lt__(self)        

    def __ge__(self, other):

        return  self.__eq__(other) or other.__lt__(self)        

class ObjectWithBoundingBox(object):
    
    def __init__(self, bounding_box):
        
        self.bounding_box = bounding_box
        self.y_tolerance = 40
        self.x_tolerance = 15

    def merge(self, other):

        self.bounding_box.merge(other.bounding_box)        

    def __eq__(self, other):
        
        return abs(self.bounding_box.y1 - other.bounding_box.y1) < self.y_tolerance and \
            abs(self.bounding_box.x1 - other.bounding_box.x1) < self.x_tolerance and \
            abs(self.bounding_box.y2 - other.bounding_box.y2) < self.y_tolerance and \
            abs(self.bounding_box.x2 - other.bounding_box.x2) < self.x_tolerance
            
    def __le__(self, other):
        
        return self.__eq__(other) or self.__lt__(other) 
    
    def __lt__(self, other):
        
        if self.__eq__(other):
            return False
        
        if abs(self.bounding_box.y1 - other.bounding_box.y1) < self.y_tolerance:
            if abs(self.bounding_box.x1 < other.bounding_box.x1) < self.x_tolerance:
                if abs(self.bounding_box.y2 - other.bounding_box.y2) < self.y_tolerance:
                    return self.bounding_box.x2 < other.bounding_box.x2
                else:
                    return self.bounding_box.y2 < other.bounding_box.y2
            else:
                return self.bounding_box.x1 < other.bounding_box.x1
        else:
            return self.bounding_box.y1 < other.bounding_box.y1

    def __ge__(self, other):
        
        return self.__eq__(other) or other.__lt__(self) 
        
    def __gt__(self, other):
        
        return other.__lt__(self)
    
    def __str__(self):
        
        return "%s" % self.bounding_box

        
    width = property(lambda self: self.bounding_box.width)
    height = property(lambda self: self.bounding_box.height)
    size = property(lambda self: self.bounding_box.size)
    coordinates = property(lambda self: self.bounding_box.coordinates)

class Segment(ObjectWithBoundingBox):
    
    def __init__(self, bounding_box: BoundingBox, segment_type: SegmentType = SegmentType.UNKNOWN):

        assert(segment_type is not None)
        super().__init__(bounding_box)
        self.segment_type = segment_type

    def merge(self, other):
        
        super().merge(other)
        if other.segment_type != self.segment_type:
            self.segment_type = SegmentType.UNKNOWN
        
        
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
                                fill = fill_colors[segment.segment_type],
                                outline = border_colors[segment.segment_type],
                                width = 5)
        counter = 0
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf", 80)
        for segment in display_segments: 
            counter += 1
            draw_img.text([segment.bounding_box.x1,
                           segment.bounding_box.y1],
                           "%d" % counter,
                           fill= border_colors[segment.segment_type],
                           font=font)
        
        out = Image.alpha_composite(background, foreground)
        out.show()

    text_segments = property(lambda self: self._get_segments(SegmentType.TEXT))
    photo_segments = property(lambda self: self._get_segments(SegmentType.PHOTO))
    drawing_segments = property(lambda self: self._get_segments(SegmentType.DRAWING))
    border_segments = property(lambda self: self._get_segments(SegmentType.BORDER))
