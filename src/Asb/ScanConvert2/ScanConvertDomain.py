'''
Created on 01.11.2022

@author: michael
'''
from enum import Enum

from PIL import Image

from Asb.ScanConvert2.Algorithms import Algorithm
import os
import re
from Asb.ScanConvert2.CroppingService import CroppingInformation

class Mode(Enum):
    
    BW=1
    GRAY=2
    COLOR=3
    
class ScanPart(Enum):
    
    WHOLE = 1
    LEFT = 2
    RIGHT = 3

class PdfMode(Enum):
    
    MANUAL=1
    MANUAL_WITH_ORIGINAL=2
    ORIGINAL=3
    OTSU=4
    SAUVOLA=5
    
    def __str__(self):

        texts = {
            PdfMode.MANUAL: "Nachbearbeiteter Scan",
            PdfMode.MANUAL_WITH_ORIGINAL: "Nachbearbeiteter Scan mit Originalansicht",
            PdfMode.ORIGINAL: "Originaler Scan",
            PdfMode.OTSU: "Schwellwert Binarisierung",
            PdfMode.SAUVOLA: "Adaptive Schwellwert Binarisierung"
        }
    
        return texts[self]
        
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

class DDFFileType(Enum):
    
    ARCHIVE = 1
    DISPLAY = 2
    PDF = 3
    METS = 4
    DDFXML = 5
    
    def description(self):
        
        if self.name == "ARCHIVE":
            return "longterm archive files"
        elif self.name == "DISPLAY":
            return "display files for viewers"
        elif self.name == "PDF":
            return "pdf files"
        elif self.name == "METS":
            return "metadata files"
        elif self.name == "DDFXML":
            return "ddf metadata files"
        else:
            raise Exception("Unknown file type!")
        
    def directory(self):
        
        if self.name == "METS" or self.name == "DDFXML":
            return "."
        
        return self.name.lower()
                
class DDFFile(object):
    
    def __init__(self, file_type: DDFFileType, sequence_no: str, temp_file_name):
        
        self.file_type = file_type
        self.sequence_no = sequence_no # may be "00005recto", so the type is string
        self.temp_file_name = temp_file_name
        self.img_object = None
        self._directory = None

    def _generate_file_id(self):
        
        basename = os.path.basename(self.temp_file_name)
        file_id = ""
        if basename[-4:] == ".tif":
            file_id += "af_"
        if basename[-4:] == ".jpg":
            file_id += "df_"
        if basename[-4:] == ".pdf":
            file_id += "pf_"
        file_id += basename[:-4]
        
        return file_id
    
    def _get_mime_type(self):
        
        if self.file_type == DDFFileType.ARCHIVE:
            return "image/tiff"
        elif self.file_type == DDFFileType.DISPLAY:
            return "image/jpeg"
        elif self.file_type == DDFFileType.PDF:
            return "application/pdf"
        elif self.file_type == DDFFileType.METS:
            return "application/xml"
        
        raise Exception("Unknown file type %s" % self.file_type)
    
    def _get_directory(self):
        
        if self._directory is None:
            return self.file_type.directory()
        
        return self._directory
    
    def _set_directory(self, directory):
        
        self._directory = directory 
        
    def _generate_alto_file_id(self):
        
        return "ocr_%s" % self._generate_file_id()
        
    def __lt__(self, other):
        
        return self.sequence_no < other.sequence_no
    
    def __gt__(self, other):

        return self.sequence_no > other.sequence_no

    def __le__(self, other):
        
        return self.sequence_no <= other.sequence_no
    
    def __ge__(self, other):

        return self.sequence_no >= other.sequence_no
    
    def __eq__(self, other):
        
        return self.sequence_no == other.sequence_no

    alto_file_name = property(lambda self: self.temp_file_name + ".alto")
    file_id = property(_generate_file_id)
    alto_file_id = property(_generate_alto_file_id)
    mime_type = property(_get_mime_type)
    basename = property(lambda self: os.path.basename(self.temp_file_name))
    alto_basename = property(lambda self: os.path.basename(self.alto_file_name))
    #zip_location = property(lambda self: os.path.join(self.file_type.name.lower(), self.basename))
    #alto_zip_location = property(lambda self: os.path.join(self.file_type.name.lower(), self.alto_basename))
    directory = property(_get_directory, _set_directory)

class ProjectProperties(object):
    
    def __init__(self, pages_per_scan, sort_type, scan_rotation, rotation_alternating):
        
        self.pages_per_scan = pages_per_scan
        self.sort_type = sort_type
        self.scan_rotation = scan_rotation
        self.rotation_alternating = rotation_alternating
        self.pdf_resolution = 300
        self.pdf_mode = PdfMode.SAUVOLA
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
        self.cropping_information = None
        
        with Image.open(filename) as img:
            self.width = img.width
            self.height = img.height
            try:
                self.resolution = get_image_resolution(img)
            except:
                self.resolution = None
            self.mode = self._get_mode(img)
            
    def add_cropping_information(self, cropping_information: CroppingInformation):
        
        self.cropping_information = cropping_information
        self.width = cropping_information.bounding_box[2] - cropping_information.bounding_box[0]
        self.height = cropping_information.bounding_box[3] - cropping_information.bounding_box[1]

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
    
    def get_raw_image(self):

        img = Image.open(self.filename)
        if self.cropping_information is not None:
            img = img.rotate(self.cropping_information.rotation_angle, Image.BICUBIC)
            img = img.crop(self.cropping_information.bounding_box)
        return img
 
    def _rotate_image(self, img: Image, angle: int) -> Image:

        if angle == 270:
            return img.transpose(Image.ROTATE_90)
        if angle == 180:
            return img.transpose(Image.ROTATE_180)
        if angle == 90:
            return img.transpose(Image.ROTATE_270)
        

    
    def __eq__(self, other):
        
        return self.filename == other.filename

    source_resolution = property(lambda self: self.resolution)

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
                 scan_part: ScanPart,
                 region: Region,
                 rotation_angle: int=0):
        
        self.scan = scan
        self.scan_part = scan_part
        self.main_region = self.initial_main_region = region
        if rotation_angle not in (0, 90, 180, 270):
            raise IllegalRotationAngle()
        self.rotation_angle = rotation_angle
        self.alignment_angle = 0.0
        self.additional_rotation_angle = 0
        self.sub_regions = []
        self.skip_page = False
        self.current_sub_region_no = 0
 
    def set_first_as_current_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException
        self.current_sub_region_no = 1
        
    def set_last_as_current_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException
        self.current_sub_region_no = self.no_of_sub_regions
        
    def set_next_as_current_region(self):
        
        if len(self.sub_regions) == 0:
            raise NoRegionsOnPageException

        if self.current_sub_region_no + 1 > self.no_of_sub_regions:
            self.current_sub_region_no = 1
        else:
            self.current_sub_region_no += 1

    def set_previous_as_current_region(self):
        
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
        
        img = self.scan.get_raw_image()
        img = img.crop((self.main_region.x, self.main_region.y, self.main_region.x2, self.main_region.y2))
        if img.mode == "1" or img.mode == "L":
            pass
        elif img.mode == "LA":
            img = img.convert("L")
        else:
            img = img.convert("RGB")
        if self.final_rotation_angle != 0:
            img = self._rotate_image(img, self.final_rotation_angle)
        img = self.align_image(img)
        img.info['dpi'] = (self.scan.resolution, self.scan.resolution)
        return img
    
    def align_image(self, img):
        
        if self.alignment_angle == 0.0:
            return img
        
        return img.rotate(self.alignment_angle, expand=False, fillcolor="white")

    def add_region(self, region: Region):
        
        self.sub_regions.append(region)
        
    def crop_page(self, region: Region):
        # TODO: Rotation angle berücksichtigen
        
        self.main_region = self._calculate_crop_region(region, self.final_rotation_angle)

    def uncrop_page(self):
        
        self.main_region = self.initial_main_region
        
    def is_cropped(self) -> bool:
        
        return self.main_region != self.initial_main_region
                
    def _calculate_crop_region(self, region: Region, final_rotation_angle: int):
        
        if final_rotation_angle == 0:
            return Region(self.main_region.x + region.x,
                          self.main_region.y + region.y,
                          region.width,
                          region.height)
        
        if final_rotation_angle == 90:

        #    return Region(region.y,
        #                  self.main_region.height - region.width - region.x,
        #                  region.height,
        #                  region.width)

            return Region(self.main_region.x + region.y,
                          self.main_region.y + self.main_region.height - region.width - region.x,
                          region.height,
                          region.width)

        if final_rotation_angle == 180:

            return Region(self.main_region.x + self.main_region.width - region.width - region.x,
                          self.main_region.height - region.height - region.y,
                          region.width,
                          region.height)
        

        return Region(self.main_region.width - region.y - region.height,
                      self.main_region.y + region.x,
                      region.height,
                      region.width)
    
    def _rotate_image(self, img: Image, angle: int) -> Image:
        '''
        Is this a bug in PIL? Do I understand something wrong?
        Why does ROTATE_90 produce a rotation_angle by 90° counterclockwise?
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
        
    main_algorithm = property(lambda self: self.main_region.mode_algorithm)
    final_rotation_angle = property(_get_final_rotation_angle)
    current_sub_region = property(_get_current_region)
    no_of_sub_regions = property(_get_number_of_sub_regions)
    source_resolution = property(lambda self: self.scan.resolution)
    
class MetaData(object):
    
    def __init__(self):
        
        self.title = ""
        self.author = ""
        self.subject = ""
        self.keywords = ""
        self.reviewed = False

        self.ddf_prefix = ""
        self.signatur = ""
        self.source = "Feministisches Archiv Freiburg"
        self.city = "Freiburg im Breisgau"
        self.special_instructions = "Erstellt mit Mitteln des Bundesministeriums fuer Familie, Senioren, Frauen und Jugend"
        self.mets_type = "volume"
        self.ddf_type = "Visuelle Materialien"
        self.ddf_subtype = "Plakat / Flugblatt"
        
        self.publication_year = ""
        self.publication_city = ""
        self.publisher = ""
        self.publication_language = "deutsch"
        

    def as_pdf_metadata_dict(self):
        
        return {"title": self.title,
                "author": self.author,
                "subject": self.subject,
                "keywords": self.keywords,
                "creator": 'Scan-Convert 2'
                }
                
class NoPagesInProjectException(Exception):
    
    pass

class Project(object):
    
    def __init__(self,
                 scans: [],
                 pages: [],
                 project_properties):

        self.scans = scans
        self.pages = pages
        self.metadata = MetaData()
        self.current_page_no = None
        self.project_properties = project_properties
    
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
    proposed_png_file = property(lambda self: self._get_proposed_file("png"))
    proposed_pdf_file = property(lambda self: self._get_proposed_file("pdf"))
    proposed_zip_file = property(lambda self: self._get_proposed_file("zip"))
