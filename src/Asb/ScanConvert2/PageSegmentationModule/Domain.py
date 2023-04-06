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

    def intersects_with(self, other):
        
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
        
        return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2
    
    def merge(self, other):
        
        if other.x1 > self.x1:
            self.x1 = other.x1
        if other.x2 < self.x2:
            self.x2 = other.x2
        if other.y1 > self.y1:
            self.y1 = other.y1
        if other.y2 < self.y2:
            self.y2 = other.y2


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
        
class Column(object):
    
    def __init__(self):
        
        self._threshold = 20
        self._segments = []
        self._bounding_box = None
    
    def add_segment(self, segment):
        
        self._bounding_box = None
        self._segments.append(segment)
    
    def _calculate_bounding_box(self):
        
        if self._bounding_box is not None:
            return self._bounding_box
        
        self._bounding_box = self._segments[0].bounding_box
        for segment in self._segments[1:]:
            if segment.bounding_box.x1 < self._bounding_box.x1:
                self._bounding_box.x1 = segment.bounding_box.x1
            if segment.bounding_box.x2 > self._bounding_box.x2:
                self._bounding_box.x2 = segment.bounding_box.x2
            if segment.bounding_box.y1 < self._bounding_box.y1:
                self._bounding_box.y1 = segment.bounding_box.y1
            if segment.bounding_box.y2 > self._bounding_box.y2:
                self._bounding_box.y2 = segment.bounding_box.y2
        
        return self._bounding_box
        
    def __eq__(self, other):
        
        return self.bounding_box == other.bounding_box
    
    def __lt__(self, other):
        """
        A larger y1 value for self means that this columns comes *before*
        the other column, because the coordinate system is upside down.
        """
        
        if abs(self.bounding_box.y1 - other.bounding_box.y1) > self._threshold:
            # Start with the most simple case: the columns are completely
            # above each other
            
            if self.bounding_box.y1 < other.bounding_box.y2:
                return True
            if other.bounding_box.y1 < self.bounding_box.y2:
                return False 
           
            # The columns are vertically apart, so the higher starting column is
            # is the smaller, i.e. left column.
            
            if self.bounding_box.y1 < other.bounding_box.y1:
                first = self
                second = other
            else:
                second = self
                first = other
            
            assert(first.bounding_box.y1 < second.bounding_box.y1)
            
            # But there is an exception: If the second column is to
            # the left of the first column and starts before the
            # end of the first column, then the second is really
            # the first column
            # side starts
            # within the length of the right column, it still needs
            # to come first
            
            if second.bounding_box.x2 < first.bounding_box.x1:
                # second is left to first
                if second.bounding_box.y1 > first.bounding_box.y2:
                    # starts prior to the end of the first column
                    return self == second
                
            return self == first
        
        # The columns start nearly at the same height, so the
        # leftmost column is the "smaller" one
        return self.bounding_box.x1 < other.bounding_box.x1
            
    def __gt__(self, other):
        
        return (not self.__eq__(other)) and (not self.__lt__(other))

    def __le__(self, other):
        
        
        return self == other or self < other
    
    def __ge__(self, other):

        return self == other or self > other
        
    bounding_box = property(_calculate_bounding_box)
    size = property(lambda self: self.bounding_box.size)
    
    
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
                                width = 5)
        out = Image.alpha_composite(background, foreground)
        out.show()

    def show_columns(self, segment_type = None):
        
        background = self.original_img.convert("RGBA")
        foreground = Image.new("RGBA", background.size, (255, 255, 255, 0))
        draw_img = ImageDraw.Draw(foreground)
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf", 80)
        counter = 0
        columns = self.get_sorted_columns()
        #assert(columns[5] < columns[10])
        for column in columns: 
            draw_img.rectangle([column.bounding_box.x1,
                                column.bounding_box.y1,
                                column.bounding_box.x2,
                                column.bounding_box.y2], 
                                fill = (0, 255, 0, 60),
                                outline =(0, 255, 0,255),
                                width = 5)
        for column in columns: 
            counter += 1
            draw_img.text([column.bounding_box.x1,
                           column.bounding_box.y1],
                        "%d (%d,%d|%d,%d)" % (counter,
                                        column.bounding_box.x1,
                                        column.bounding_box.y1,
                                        column.bounding_box.x2,
                                        column.bounding_box.y2,
                                ),
                           fill="red",
                           font=font)
        out = Image.alpha_composite(background, foreground)
        out.show()

    def get_sorted_columns(self):
        
        unsorted_columns = self.find_columns()
        sorted_columns = []
        while len(unsorted_columns) > 1:
            min_column = unsorted_columns[0]
            for column in unsorted_columns[1:]:
                if abs(column.bounding_box.y1 - min_column.bounding_box.y1) < 20:
                    # sloppy implementation of "equals"
                    if column.bounding_box.x1 < min_column.bounding_box.x1:
                        min_column = column
                else:
                    if column.bounding_box.y1 < min_column.bounding_box.y1:
                        min_column = column
            sorted_columns.append(min_column)
            unsorted_columns.remove(min_column)
        sorted_columns.append(unsorted_columns[0])

        sort_error = True
        while sort_error:
            sort_error = False
            for idx in range(0, len(sorted_columns) - 1):
                if sorted_columns[idx] > sorted_columns[idx + 1]:
                    print("Fixing sort error")
                    next_col = sorted_columns[idx + 1]
                    sorted_columns[idx + 1] = sorted_columns[idx]
                    sorted_columns[idx] = next_col
                    sort_error = True
                    break
    
        return sorted_columns
    
    def find_columns(self):
        
        columns = []
        segments = self.segments.copy()
        segments.sort(key=lambda x: x.size, reverse=True)
        for segment in segments:
            segment_merged = False
            for column in columns:
                if segment.bounding_box.is_horizontally_contained_in(column.bounding_box, 10) and \
                    segment.bounding_box.has_nearly_the_same_width(column.bounding_box, 0.95):
                    column.add_segment(segment)
                    segment_merged = True
                    break
            if not segment_merged:
                column = Column()
                column.add_segment(segment)
                columns.append(column)
                
        columns.sort(key=lambda x: x.size, reverse=True)
        merged_columns = []
        for column in columns:
            column_merged = False
            for merge_column in merged_columns:
                if merge_column.bounding_box.intersects_with(column.bounding_box):
                    for segment in column._segments:
                        merge_column.add_segment(segment)
                    column_merged = True
            if not column_merged:
                merged_columns.append(column)
                
        return merged_columns
                
    text_segments = property(lambda self: self._get_segments(SegmentType.TEXT))
    photo_segments = property(lambda self: self._get_segments(SegmentType.PHOTO))
    drawing_segments = property(lambda self: self._get_segments(SegmentType.DRAWING))
    border_segments = property(lambda self: self._get_segments(SegmentType.BORDER))
