'''
Created on 04.11.2022

@author: michael
'''
from injector import inject, singleton

from Asb.ScanConvert2.ScanConvertDomain import Page, Region, \
    Scan, Algorithm, SortType, Project

class SortDetector:
    
    def _is_mixed(self, scans):

        area_first_scan = 1.0 * scans[0].width * scans[0].height
        area_second_scan = 1.0 * scans[1].width * scans[1].height
        
        diff = area_second_scan / area_first_scan
        if abs(diff - 2) < 0.1:
            # First scan is nearly half the size of the second scan
            return True
        
        return False

class BasePageGenerator(object):
    
    def __init__(self):
        
        self.alternating_rotation = {
            0: 180,
            90: 270,
            180: 0,
            270: 90,
        }
            
        self.page_rotation = {
            0: 0,
            90: 270,
            180: 180,
            270: 90,
        }
    
    def _get_whole(self, scan: Scan, angle: int = 0):
        
        return Page(scan, Region(0,0,scan.width,scan.height), angle)
    
    def _get_left(self, scan: Scan, angle: int = 0):
    
        return Page(scan, Region(0, 0, round(scan.width/2.0), scan.height), angle)
    
    def _get_right(self, scan: Scan, angle: int = 0):
        
        return Page(scan,
                    Region(round(scan.width/2.0)+1, 0,
                           scan.width-round(scan.width/2.0), scan.height),
                    angle)
        
    def _get_top(self, scan: Scan, angle: int = 0):

        return Page(scan, Region(0, 0, scan.width, round(scan.height/2.0)), angle)

    def _get_bottom(self, scan: Scan, angle: int = 0):

        return Page(scan,
                    Region(0,round(scan.height/2.0)+1,
                           scan.width, scan.height-round(scan.height/2.0)),
                    angle)

class SinglePagesGenerator(BasePageGenerator):
    
    def scans_to_pages(self, scans: [], scan_rotation: int, alternating: bool):
        
        pages = []
        next_rotation = self.page_rotation[scan_rotation]
        for scan in scans:
            pages.append(self._get_whole(scan, next_rotation))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
                    
        return pages
    
class DoublePagesGenerator(BasePageGenerator):
    '''
    This generator is more complicated than the single pages one.
    It is used for A3 overhead scanners where you may scan both
    sides of a brochure or journal (or an A3 flatbed scanner
    where you are able to scan double sided A5 page already with the
    correct alignment). It assumes that the scans are already aligned properly
    with the right upper corner really being the right upper corner.
    
    But it is not so trivial as it seems to be on first glance.
    The first scan might be the title and the back cover of  brochure or journal,
    so we need some rearranging of the pages. It might also be that the first
    and the last scans are only single pages. So we try to detect these cases.
    '''
    
    def scans_to_pages(self, scans: [], scan_rotation: int, alternating: bool):

        if scan_rotation == 0:
            return self._0_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 90:
            return self._270_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 180:
            return self._180_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 270:
            return self._90_degrees_region_rotation(scans, alternating)

    def _0_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 0
        pages = []
        for scan in scans:
            if next_rotation == 0:
                pages.append(self._get_left(scan, 0))
                pages.append(self._get_right(scan, 0))
            else:
                pages.append(self._get_right(scan), 180)
                pages.append(self._get_left(scan), 180)
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

    def _90_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 90
        pages = []
        for scan in scans:
            if next_rotation == 90:
                pages.append(self._get_top(scan, 90))
                pages.append(self._get_bottom(scan, 90))
            else:
                pages.append(self._get_bottom(scan, 270))
                pages.append(self._get_top(scan, 270))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

    def _180_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 180
        pages = []
        for scan in scans:
            if next_rotation == 180:
                pages.append(self._get_right(scan, 180))
                pages.append(self._get_left(scan, 180))
            else:
                pages.append(self._get_left(scan, 0))
                pages.append(self._get_right(scan, 0))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

    def _270_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 270
        pages = []
        for scan in scans:
            if next_rotation == 270:
                pages.append(self._get_bottom(scan, 270))
                pages.append(self._get_top(scan, 270))
            else:
                pages.append(self._get_top(scan), 90)
                pages.append(self._get_bottom(scan), 90)
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

@singleton    
class PageSorter():

    def sort_pages(self, pages: [], sort_type: SortType):
        
        if sort_type == SortType.STRAIGHT:
            return pages
        
        if sort_type == SortType.STRAIGHT_DOUBLE:
            # First page must be placed at the end
            return pages[1:] + [pages[0]]
        
        if sort_type == SortType.SINGLE_ALL_FRONT_ALL_BACK:
            if len(pages) % 2 != 0:
                raise("Ungleiche Anzahl Vorder- und Rückseiten")
            sorted_pages = []
            for i in range(0, int(len(pages) / 2)):
                sorted_pages.append(pages[i])
                sorted_pages.append(pages[(-1*i)-1])
            return sorted_pages
        
        raise("Diese Sortierung ist noch nicht implementiert!")
    
@singleton
class ProjectGenerator():
    
    @inject
    def __init__(self,
                 sort_detector: SortDetector,
                 single_page_generator: SinglePagesGenerator,
                 double_page_generator: DoublePagesGenerator,
                 page_sorter: PageSorter):
        
        self.sort_detector = sort_detector
        self.single_page_generator = single_page_generator
        self.double_page_generator = double_page_generator
        self.page_sorter = page_sorter
    
    def scans_to_project(self,
                    scans: [],
                    pages_per_scan: int,
                    sort_type: SortType,
                    scan_rotation: int,
                    rotation_alternating: bool,
                    pdf_algorithm: Algorithm):
    
        if pages_per_scan == 1:
            pages = self._generate_single_pages(scans, scan_rotation, rotation_alternating)
        else:
            is_mixed = sort_type == SortType.STRAIGHT and self.sort_detector._is_mixed(scans)
            if not is_mixed:
                sort_type = SortType.STRAIGHT_DOUBLE
            pages = self._generate_double_pages(scans, scan_rotation, rotation_alternating, is_mixed)
        
        if pdf_algorithm != Algorithm.NONE:
            for page in pages:
                page.main_region.mode_algorithm = pdf_algorithm
                
        return Project(self.page_sorter.sort_pages(pages, sort_type))

    def _generate_single_pages(self, scans, scan_rotation, rotation_alternating):
        
        return self.single_page_generator.scans_to_pages(scans,
                                                        scan_rotation,
                                                        rotation_alternating)
    
    def _generate_double_pages(self, scans: [], scan_rotation: int, rotation_alternating: bool, is_mixed: bool):
        
        if is_mixed:
            front_and_back = self.single_page_generator.scans_to_pages(
                [scans[0], scans[-1]],
                scan_rotation,
                rotation_alternating)
            middle = self.double_page_generator.scans_to_pages(
                scans[1:-1],
                scan_rotation,
                rotation_alternating)
            return [front_and_back[0]] + middle + [front_and_back[1]]
        else:
            return self.double_page_generator.scans_to_pages(
                scans,
                scan_rotation,
                rotation_alternating)