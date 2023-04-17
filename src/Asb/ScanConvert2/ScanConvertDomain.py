'''
Created on 01.11.2022

@author: michael
'''
from enum import Enum

from PIL import Image

from Asb.ScanConvert2.Algorithms import Algorithm
import os
import re
from Asb.ScanConvert2.PageSegmentationModule.Domain import SegmentedPage


class Mode(Enum):
    
    BW=1
    GRAY=2
    COLOR=3

class ScantypeObsolete(Enum):
    
    SINGLE=1
    DOUBLE=2
    DOUBLE_90=3
    DOUBLE_270=4
    SHEET_90=5
    SHEET_270=6
    
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
        raise MissingResolutionInfo
        
    xres, yres = img.info['dpi']
    if xres == 1 or yres == 1:
        raise MissingResolutionInfo()
        
    if xres != yres:
        raise IllegalResolution()
    
    # newer versions of Pillow return a float
    return round(xres)

class ProjectProperties(object):
    
    def __init__(self):
        
        self.pdf_resolution = 300
        self.tif_resolution = 300
        self.run_ocr = True
        self.create_pdfa = True
        self.ocr_lang = "deu"
        self.normalize_background_colors = True

class Region(object):
    '''
    A simple data class to describe a part of a scan
    and the necessary mode transformation algorithm
    '''

    def __init__(self, x: float, y: float, width: float, height: float, mode_algorithm: Algorithm=Algorithm.OTSU):

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
            try:
                self.resolution = get_image_resolution(img)
            except:
                self.resolution = None
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
        if img.mode == "L" or img.mode == "LA":
            return Mode.GRAY
        if img.mode == "RGB" or img.mode == "RGBA":
            return Mode.COLOR
        
        raise UnknownImageMode(img.mode)
    
    def is_resolution_sane(self):
        
        if self.resolution is None:
            return False
        
        if self.width * 1.0 / self.resolution > 22:
            # We consider a with > 22 inches as insane
            return False
        
        return True

class NoRegionsOnPageException(Exception):
    
    pass

class Page:
    '''
    This class describes a single page of a project. In
    principle it consists of a set of rules
    to extract an Image from a Scan: Mainly
    cutting a region from the scan and rotating it.
    It also contains the algorithm to apply to the
    scan, the default being the Otsu algorithm for
    binarization.
    
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
            
    def get_raw_image(self):
        """
        The only operation performed on the scan is cutting
        the page region from the scan and rotating it appropriately
        """
        
        img = Image.open(self.scan.filename)
        img = img.crop((self.main_region.x, self.main_region.y, self.main_region.x2, self.main_region.y2))
        if img.mode == "1" or img.mode == "L":
            pass
        elif img.mode == "LA":
            img = img.convert("L")
        else:
            img = img.convert("RGB")
        if self.final_rotation_angle != 0:
            img = self._rotate_image(img, self.final_rotation_angle)
        img.info['dpi'] = (self.scan.resolution, self.scan.resolution)
        return img
            
    def add_region(self, region: Region):
        
        self.sub_regions.append(region)
    
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

        return Page.algorithms._apply_algorithm(img, algorithm)        
    
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
    
    def _get_source_resolution(self):
        
        return self.scan.resolution
        
    main_algorithm = property(lambda self: self.main_region.mode_algorithm)
    final_rotation_angle = property(_get_final_rotation_angle)
    current_sub_region = property(_get_current_region)
    no_of_sub_regions = property(_get_number_of_sub_regions)
    source_resolution = property(lambda self: self._get_source_resolution())

class SegmentedPagePage(Page):
    
    def __init__(self, segmented_page: SegmentedPage):
        
        self.segmented_page = segmented_page
        main_region = Region(0, 0,
                             segmented_page.original_img.width, segmented_page.original_img.height,
                             Algorithm.OTSU)
        super().__init__(None, main_region, 0)
        self._create_regions(self.segmented_page)
    
    def get_raw_image(self):
        
        return self.segmented_page.original_img
    
    def _get_source_resolution(self):
        
        return get_image_resolution(self.segmented_page.original_img)

    def _create_regions(self, segmented_page):
        
        for photo_segment in segmented_page.photo_segments:
            
            region = Region(photo_segment.bounding_box.x1,
                            photo_segment.bounding_box.y1,
                            photo_segment.width,
                            photo_segment.height, Algorithm.FLOYD_STEINBERG)
            self.add_region(region)
    
class MetaData(object):
    
    def __init__(self):
        
        self.title = ""
        self.author = ""
        self.subject = ""
        self.keywords = ""
        self.reviewed = False

    def as_dict(self):
        
        return {"title": self.title, "author": self.author, "subject": self.subject,
                "keywords": self.keywords, "creator": 'Scan-Convert 2'}

class NoPagesInProjectException(Exception):
    
    pass

class Project(object):
    
    def __init__(self,
                 pages: []):

        self.pages = pages
        self.metadata = MetaData()
        self.current_page_no = None
        self.project_properties = ProjectProperties()
    
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
    
    def _get_proposed_file(self, suffix):
        
        if len(self.pages) == 0:
            return "unknown.%s" % suffix
        return re.sub("[-_]?\d*\.[^\.]+?$", ".%s" % suffix, self.pages[0].scan.filename)
        
        
    
    current_page = property(_get_current_page)
    no_of_pages = property(_get_number_of_pages)
    proposed_pdf_file = property(lambda self: self._get_proposed_file("pdf"))
    proposed_zip_file = property(lambda self: self._get_proposed_file("zip"))
