'''
Created on 01.11.2022

@author: michael
'''
from enum import Enum

from PIL import Image

from Asb.ScanConvert2.Algorithms import Algorithm


class Mode(Enum):
    
    BW=1
    GRAY=2
    COLOR=3

class SortType(Enum):
    
    STRAIGHT=1
    SINGLE_ALL_FRONT_ALL_BACK=2
    SHEET=3
    SHEET_ALL_FRONT_ALL_BACK=4

class Scantype(Enum):
    
    SINGLE=1
    DOUBLE=2
    DOUBLE_90=3
    DOUBLE_270=4
    SHEET_90=5
    SHEET_270=6
    
class Scannertype(Enum):
    
    OVERHEAD=1
    FLATBED=2
    FEEDER_SIMPLEX=3
    FEEDER_DUPLEX=4

class MissingResolutionInfo(Exception):
    
    pass

class IllegalResolution(Exception):
    
    pass

class UnknownImageMode(Exception):
    
    pass

class IllegalRotationAngle(Exception):
    
    pass

class UpscalingError(Exception):
    
    pass

def get_image_resolution(img: Image) -> int:
        
    if not 'dpi' in img.info:
        return 300
        
    xres, yres = img.info['dpi']
    if xres == 1 or yres == 1:
        raise MissingResolutionInfo()
        
    if xres != yres:
        raise IllegalResolution()
    
    # newer versions of Pillow return a float
    return round(xres)

class Region(object):
    '''
    A simple data class to describe a part of a scan
    and the necessary mode transformation algorithm
    '''

    def __init__(self, x: int, y: int, width: int, height: int, mode_algorithm: Algorithm=Algorithm.OTSU):

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.mode_algorithm = mode_algorithm
        
    def __str__(self):
        
        return "Links oben: %d | %d\nRechts unten: %d | %d\nBreite: %d\nHöhe: %d" % (
            self.x, self.y, self.x2, self.y2, self.width, self.height)
        
    x2 = property(lambda self: self.x + self.width)
    y2 = property(lambda self: self.y + self.height)

class Scan(object):
    '''
    This is a simple container class with minimalistic
    logic. It expects a graphic file location as instantiation
    parameter and then reads the file and extracts basic
    graphic file parameters
    '''

    def __init__(self, filename: str):
        
        self.no_of_pages = 1
        self.filename = filename
        
        with Image.open(filename) as img:
            self.width = img.width
            self.height = img.height
            self.resolution = get_image_resolution(img)
            self.mode = self._get_mode(img)
        
    
    def _get_mode(self, img) -> Mode:
        
        # Some containers like png do not have a
        # native bw format but use a palette format
        # We won't support this - simply because
        # it is too complicated to detect if this
        # is true bw and we will not encourage creating
        # black and white scans - the qualitity is much
        # inferior to creating gray scans and convert these
        # to bw in software - which is the main purpose
        # of this program.
        if img.mode == "1":
            return Mode.BW
        if img.mode == "L":
            return Mode.GRAY
        if img.mode == "RGB" or img.mode == "RGBA":
            return Mode.COLOR
        
        raise UnknownImageMode(img.mode)

class NoRegionsOnPageException(Exception):
    
    pass

class Page:
    '''
    This class describes a single page of a project. In
    principle it consists of a set of rules
    to extract an Image from a Scan. The rules may contain
    change of resolution, the region of the scan we are
    interested in and which mode changing algorithm we want
    to apply to this region, the target resolution we desire
    and, optionally, a rotation angle.
    
    Additionally it should be possible to define certain
    special region, on which we want to apply different
    algorithms. The coordinates of the sub region relate
    to the already transformed scan, not the original
    scan coordinates. 
    '''
    
    def __init__(self, 
                 scan: Scan,
                 region: Region,
                 rotation_angle: int=0):
        
        self.scan = scan
        self.main_region = region
        if rotation_angle not in (0, 90, 180, 270):
            raise IllegalRotationAngle()
        self.rotation_angle = rotation_angle
        self.additional_rotation_angle = 0
        self.sub_regions = []
        self.skip_page = False
        self.current_sub_region_no = 0
 
    def first_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException
        self.current_sub_region_no = 1
        
    def last_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException
        self.current_sub_region_no = self.no_of_sub_regions
        
    def next_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException

        if self.current_sub_region_no + 1 > self.no_of_sub_regions:
            self.current_sub_region_no = 1
        else:
            self.current_sub_region_no += 1

    def previous_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException

        if self.current_sub_region_no <= 1:
            self.current_sub_region_no = self.no_of_sub_regions
        else:
            self.current_sub_region_no -= 1

    def get_base_image(self, target_resolution=300) -> Image:
        
        if target_resolution > self.scan.resolution:
            pass
            #raise UpscalingError()
        
        img = Image.open(self.scan.filename)
        img = img.crop((self.main_region.x, self.main_region.y, self.main_region.x2, self.main_region.y2))
        if target_resolution != self.scan.resolution:
            img = self._change_resolution(img, self.scan.resolution, target_resolution)
        if self.final_rotation_angle != 0:
            img = self._rotate_image(img, self.final_rotation_angle)
        return img
            
    def add_region(self, region: Region):
        
        self.sub_regions.append(region)
    
    def _change_resolution(self, img: Image, source_resolution: int, target_resolution: int) -> Image:

        current_width, current_height = img.size
        new_width = int(current_width * target_resolution / source_resolution)
        new_height = int(current_height * target_resolution / source_resolution)

        scaled_img = img.resize((new_width, new_height))
        scaled_img.info['dpi'] = (target_resolution, target_resolution)
  
        return scaled_img
    
    def _rotate_image(self, img: Image, angle: int) -> Image:
        '''
        Is this a bug in PIL? Do I understand something wrong?
        Why does ROTATE_90 produce a rotation by 90° counterclockwise?
        '''

        if angle == 270:
            return img.transpose(Image.ROTATE_90)
        if angle == 180:
            return img.transpose(Image.ROTATE_180)
        if angle == 90:
            return img.transpose(Image.ROTATE_270)
        raise IllegalRotationAngle()

    def _apply_algorithm(self, img: Image, algorithm: int) -> Image:

        return Page.algorithms.apply_algorithm(img, algorithm)        
    
    def _get_final_rotation_angle(self):
        
        angle = self.rotation_angle + self.additional_rotation_angle
        while angle >= 360:
            angle -= 360
        return angle

    def _get_current_region(self):
        
        if self.no_of_sub_regions == 0:
            raise(NoRegionsOnPageException())
        return self.sub_regions[self.current_sub_region_no-1]
    
    def _get_number_of_sub_regions(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException()
        return len(self.sub_regions)
        
    main_algorithm = property(lambda self: self.main_region.mode_algorithm)
    final_rotation_angle = property(_get_final_rotation_angle)
    current_sub_region = property(_get_current_region)
    no_of_sub_regions = property(_get_number_of_sub_regions)

class MetaData(object):
    
    def __init__(self):
        
        self.title = ""
        self.author = ""
        self.subject = ""
        self.keywords = ""

class NoPagesInProjectException(Exception):
    
    pass

class Project(object):
    
    def __init__(self,
                 pages: []):

        self.pages = pages
        self.metadata = MetaData()
        self.current_page_no = None
    
    def first_page(self):
        
        if len(self.pages) == 0:
            raise(NoPagesInProjectException)
        self.current_page_no = 1
        
    def last_page(self):
        
        if len(self.pages) == 0:
            raise(NoPagesInProjectException)
        self.current_page_no = self.no_of_pages

    def next_page(self):
        
        if len(self.pages) == 0:
            raise(NoPagesInProjectException)

        if self.current_page_no + 1 > self.no_of_pages:
            self.current_page_no = 1
        else:
            self.current_page_no += 1

    def previous_page(self):

        if len(self.pages) == 0:
            raise(NoPagesInProjectException)
        
        if self.current_page_no <= 1:
            self.current_page_no = self.no_of_pages
        else:
            self.current_page_no -= 1

    def _get_current_page(self):
        
        if self.no_of_pages == 0:
            raise(NoPagesInProjectException())
        return self.pages[self.current_page_no-1]
    
    def _get_number_of_pages(self):
        
        if len(self.pages) == 0:
            raise NoPagesInProjectException()
        return len(self.pages)
    
    current_page = property(_get_current_page)
    no_of_pages = property(_get_number_of_pages)
