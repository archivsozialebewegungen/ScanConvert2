'''
Created on 01.11.2022

@author: michael
'''
from PIL import Image
from enum import Enum
from numpy import asarray
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola


class Mode(Enum):
    
    BW=1
    GRAY=2
    COLOR=3

class Algorithm(Enum):

    NONE=1
    GRAY=2
    OTSU=3
    SAUVOLA=4
    FLOYD_STEINBERG=5

ALGORITHM_TEXTS = {
    Algorithm.NONE: "Modus beibehalten",
    Algorithm.GRAY: "Graustufen",
    Algorithm.OTSU: "SW Otsu (Text gleichmäßig)",
    Algorithm.SAUVOLA: "SW Sauvola (Text fleckig)",
    Algorithm.FLOYD_STEINBERG: "SW Floyd-Steinberg (Bilder)"}
    
class SortType(Enum):
    
    STRAIGHT=1
    SINGLE_ALL_FRONT_ALL_BACK=2
    SHEET=3
    SHEET_ALL_FRONT_ALL_BACK=4
    STRAIGHT_DOUBLE=5

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

class Projecttype(Enum):
    
    TIFF=1
    PDF=2
    BOTH=3

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
        raise MissingResolutionInfo()
        
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

    def __init__(self, x: int, y: int, width: int, height: int, mode_algorithm: Algorithm=Algorithm.NONE):

        print("x: %d y: %d with: %d height: %d" % (x, y, width, height))
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
    scan coordinates. [This is not part of the MVP and will be
    implemented later.] 
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
        self.sub_regions = []
    
    def get_base_image(self, target_resolution=300) -> Image:
        
        if target_resolution > self.scan.resolution:
            raise UpscalingError()
        
        img = Image.open(self.scan.filename)
        img = img.crop((self.main_region.x, self.main_region.y, self.main_region.x2, self.main_region.y2))
        if target_resolution != self.scan.resolution:
            img = self._change_resolution(img, self.scan.resolution, target_resolution)
        if self.rotation_angle != 0:
            img = self._rotate_image(img, self.rotation_angle)
        return img
            
    def get_final_image(self, target_resolution=300) -> Image:
        
        img = final_img = self.get_base_image(target_resolution)
        
        if self.main_region.mode_algorithm != Algorithm.NONE:
            final_img = self._apply_algorithm(img, self.main_region.mode_algorithm)
        
        return final_img
    
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
        
        if algorithm == Algorithm.GRAY:
            return self._apply_algorithm_gray(img)
        if algorithm == Algorithm.OTSU:
            return self._apply_threshold_algorithm(img, Algorithm.OTSU)
        if algorithm == Algorithm.SAUVOLA:
            return self._apply_threshold_algorithm(img, Algorithm.SAUVOLA)
        if algorithm == Algorithm.FLOYD_STEINBERG:
            return self._apply_algorithm_floyd_steinberg(img)
        raise Exception("Unknown Algorithm.")
    
    def _apply_algorithm_gray(self, img: Image):
        '''
        TODO: The default algorithm is probably optimized for
        photo images. This might not be the best option for
        scanned papers. Do more research.
        '''
        if img.mode == "1" or img.mode == "L":
            return img
        
        return img.convert("L")

    def _apply_algorithm_floyd_steinberg(self, img: Image):
        '''
        Floyd-Steinberg is the default for PIL
        '''
        if img.mode == "1":
            return img
        
        return img.convert("1")

    def _apply_threshold_algorithm(self, img: Image, algorithm: Algorithm):

        resolution = get_image_resolution(img)
        in_array = asarray(self._apply_algorithm_gray(img))
        if algorithm == Algorithm.OTSU:
            mask = threshold_otsu(in_array)
        elif algorithm == Algorithm.SAUVOLA:
            mask = threshold_sauvola(in_array)
        else:
            raise Exception("Unknown threshold algorithm")
        out_array = in_array > mask
        img = Image.fromarray(out_array)
        img.info['dpi'] = (resolution, resolution)
        img.convert("1")
        return img

class Project(object):
    
    def __init__(self,
                 pages: []):

        self.pages = pages
        