'''
Created on 01.11.2022

@author: michael
'''
from PIL import Image, ImageFilter
from enum import Enum
import numpy as np
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola
import cv2


class Mode(Enum):
    
    BW=1
    GRAY=2
    COLOR=3

class Algorithm(Enum):

    NONE=1
    GRAY=2
    GRAY_WHITE=3
    OTSU=4
    SAUVOLA=5
    FLOYD_STEINBERG=6
    COLOR_PAPER_QUANTIZATION=7
    COLOR_TEXT_QUANTIZATION=8
    TWO_COLOR_QUANTIZATION=9
    BW_QUANTIZATION=10
    WEISS=11

ALGORITHM_TEXTS = {
    Algorithm.NONE: "Modus beibehalten",
    Algorithm.GRAY: "Graustufen",
    Algorithm.GRAY_WHITE: "Grau auf Weiß",
    Algorithm.OTSU: "SW Otsu (Text gleichmäßig)",
    Algorithm.SAUVOLA: "SW Sauvola (Text fleckig)",
    Algorithm.FLOYD_STEINBERG: "SW Floyd-Steinberg (Bilder)",
    Algorithm.COLOR_PAPER_QUANTIZATION: "Farbiges Papier",
    Algorithm.COLOR_TEXT_QUANTIZATION: "Farbige Schrift auf weißem Hintergrund",
    Algorithm.TWO_COLOR_QUANTIZATION: "Schrift und Text farbig",
    Algorithm.BW_QUANTIZATION: "Hintergrundfarbe entfernen",
    Algorithm.WEISS: "Komplett weiss"
    }
    
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
        return 72
        
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
        
    def next_region(self):
        
        if self.current_sub_region_no + 1 > self.no_of_sub_regions:
            self.current_sub_region_no = 1
        else:
            self.current_sub_region_no += 1

    def previous_region(self):
        
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
            print(self.final_rotation_angle)
            img = self._rotate_image(img, self.final_rotation_angle)
        return img
            
    def get_final_image(self, target_resolution=300) -> Image:
        
        img = final_img = self.get_base_image(target_resolution)
        
        if self.main_region.mode_algorithm != Algorithm.NONE:
            final_img = self._apply_algorithm(img, self.main_region.mode_algorithm)
            
        return self.apply_regions(final_img, img, target_resolution)
        
    def apply_regions(self, final_img: Image, img: Image, target_resolution) -> Image:
        
        if len(self.sub_regions) == 0:
            return final_img
        
        for region in self.sub_regions:
            final_img = self.apply_region(region, final_img, img, target_resolution)
    
        return final_img
    
    def apply_region(self, region: Region, final_img: Image, img: Image, target_resolution) -> Image:
        
        region_img = img.crop((region.x, region.y, region.x2, region.y2))
        region_img = self._apply_algorithm(region_img, region.mode_algorithm)
        if region_img.mode == "RGBA" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGBA")
        if region_img.mode == "RGB" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGB")
        if region_img.mode == "L" and final_img.mode == "1":
            final_img = final_img.convert("L")
        final_img.paste(region_img, (region.x, region.y, region.x2, region.y2))
        return final_img
    
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
        
        if algorithm == Algorithm.NONE:
            return img
        if algorithm == Algorithm.GRAY:
            return self._apply_algorithm_gray(img)
        if algorithm == Algorithm.GRAY_WHITE:
            return self._apply_algorithm_gray_on_white_text(img)
        if algorithm == Algorithm.OTSU:
            return self._apply_threshold_algorithm(img, Algorithm.OTSU)
        if algorithm == Algorithm.SAUVOLA:
            return self._apply_threshold_algorithm(img, Algorithm.SAUVOLA)
        if algorithm == Algorithm.FLOYD_STEINBERG:
            return self._apply_algorithm_floyd_steinberg(img)
        if algorithm == Algorithm.COLOR_PAPER_QUANTIZATION:
            return self._apply_algorithm_color_paper(img)
        if algorithm == Algorithm.COLOR_TEXT_QUANTIZATION:
            return self._apply_algorithm_color_text_quantization(img)
        if algorithm == Algorithm.TWO_COLOR_QUANTIZATION:
            return self._apply_algorithm_quantization(img)
        if algorithm == Algorithm.BW_QUANTIZATION:
            return self._apply_algorithm_bw_quantization(img)
        if algorithm == Algorithm.WEISS:
            return self._apply_algorithm_white(img)
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
        in_array = np.asarray(self._apply_algorithm_gray(img))
        if algorithm == Algorithm.OTSU:
            mask = threshold_otsu(in_array)
        elif algorithm == Algorithm.SAUVOLA:
            mask = threshold_sauvola(in_array, window_size=11)
        else:
            raise Exception("Unknown threshold algorithm")
        out_array = in_array > mask
        img = Image.fromarray(out_array)
        img.info['dpi'] = (resolution, resolution)
        img.convert("1")
        return img
    
    def _apply_algorithm_quantization(self, img: Image) -> Image:
        """
        Uses the k-means algorithm to quantize the image
        """
        
        if img.mode != "RGB":
            img = img.convert("RGB")
        np_array = np.array(img)
        flattend = np.float32(np_array).reshape(-1,3)
        condition = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,20,1.0)
        ret,label,center = cv2.kmeans(flattend, 2 , None, condition,10,cv2.KMEANS_RANDOM_CENTERS)
        center = np.uint8(center)
        final_flattend = center[label.flatten()]
        final_img_array = final_flattend.reshape(np_array.shape)
        new_img = Image.fromarray(final_img_array)
        new_img.info['dpi'] = img.info['dpi']
        return new_img
    
    def _apply_algorithm_gray_on_white_text(self, img: Image) -> Image:

        if img.mode != "RGB":
            img = img.convert("RGB")

        mask = self._apply_algorithm_bw_quantization(img)
        mask = mask.convert("RGB")
        mask = mask.filter(ImageFilter.BLUR)

        np_img = np.array(img)
        np_mask = np.array(mask)
        red, green, blue = np_mask.T

        white_areas = (red == 255) & (green == 255) & (blue == 255)
        np_img[white_areas.T] = (255, 255, 255)

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img.convert("L")
    
    def _apply_algorithm_bw_quantization(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            white = colors[0][1] 
            black = colors[1][1]
        else: 
            white = colors[1][1] 
            black = colors[0][1]
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 3 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        white_areas = (red == white[0]) & (green == white[1]) & (blue == white[2])
        np_img[white_areas.T] = (255, 255, 255) # Transpose back needed
        black_areas = (red == black[0]) & (green == black[1]) & (blue == black[2])
        np_img[black_areas.T] = (0, 0, 0) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img.convert("1")
    
    def _apply_algorithm_color_paper(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            black = colors[1][1]
        else: 
            black = colors[0][1]
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 3 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        black_areas = (red == black[0]) & (green == black[1]) & (blue == black[2])
        np_img[black_areas.T] = (0, 0, 0) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img
    
    def _apply_algorithm_color_text_quantization(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            white = colors[0][1] 
        else: 
            white = colors[1][1] 
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 4 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        # Replace white with red... (leaves alpha values alone...)
        white_areas = (red == white[0]) & (green == white[1]) & (blue == white[2])
        np_img[white_areas.T] = (255, 255, 255) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img

    def _apply_algorithm_white(self, img):
        
        return Image.new("1", img.size, 1)
        
        

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
        self.current_page_no = 0
        
    def next_page(self):
        
        if self.current_page_no + 1 > self.no_of_pages:
            self.current_page_no = 1
        else:
            self.current_page_no += 1

    def previous_page(self):
        
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
