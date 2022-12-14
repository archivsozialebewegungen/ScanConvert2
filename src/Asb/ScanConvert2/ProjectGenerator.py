'''
Created on 04.11.2022

@author: michael
'''
from injector import inject, singleton

from Asb.ScanConvert2.ScanConvertDomain import Page, Region, \
    Scan, Algorithm, SortType, Project

class NumberOfPagesDetector:
    
    def set_numbers(self, scans):
        
        sizes = []
        for scan in scans:
            scan.no_of_pages = 2
            sizes.append(1.0 * scan.width * scan.height)
        
        diff = max(sizes) / min(sizes)
        
        if abs(diff - 1) < 0.1:
            # All pages have roughly the same size, so all are
            # double sided and we're done
            return scans
        
        double_size = max(sizes)
        
        for i in range(len(sizes)):
            if abs((double_size / sizes[i]) - 2) < 0.1:
                scans[i].no_of_pages = 1

        return scans

@singleton
class PagesGenerator(object):
    '''
    This generator is complicated. There may be more than one page
    on a scan, for example when you scan a brochure that you don't
    want to cut up for scanning. This might even lead to mixed scans
    regarding the no of pages: While cover and back scans are single
    sided, the rest may be double sided.
    
    How many pages a scan does represent is already determined and
    registered in the scan object in the property no_of_pages, so we
    do not need to determine this. But we need to take care of
    rotation. And this rotation may be alternating (if you use a scanner
    with a duplex feeder). 
    '''
    
    alternating_rotation = {
            0: 180,
            90: 270,
            180: 0,
            270: 90,
        }
            
    page_rotation = {
            0: 0,
            90: 270,
            180: 180,
            270: 90,
        }
    
    def scans_to_pages(self, scans: [], scan_rotation: int, alternating: bool):

        if scan_rotation == 0:
            return self._0_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 90:
            return self._270_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 180:
            return self._180_degrees_region_rotation(scans, alternating)
        elif scan_rotation == 270:
            return self._90_degrees_region_rotation(scans, alternating)

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

    def _0_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 0
        pages = []
        for scan in scans:
            if next_rotation == 0:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 0))
                else:
                    pages.append(self._get_left(scan, 0))
                    pages.append(self._get_right(scan, 0))
            else:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 180))
                else:
                    pages.append(self._get_right(scan, 180))
                    pages.append(self._get_left(scan, 180))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

    def _90_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 90
        pages = []
        for scan in scans:
            if next_rotation == 90:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 90))
                else:
                    pages.append(self._get_bottom(scan, 90))
                    pages.append(self._get_top(scan, 90))
            else:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 270))
                else:
                    pages.append(self._get_top(scan, 270))
                    pages.append(self._get_bottom(scan, 270))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

    def _180_degrees_region_rotation(self, scans: [], alternating: bool):

        next_rotation = 180
        pages = []
        for scan in scans:
            if next_rotation == 180:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 180))
                else:
                    pages.append(self._get_right(scan, 180))
                    pages.append(self._get_left(scan, 180))
            else:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 0))
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
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 270))
                else:
                    pages.append(self._get_top(scan, 270))
                    pages.append(self._get_bottom(scan, 270))
            else:
                if scan.no_of_pages == 1:
                    pages.append(self._get_whole(scan, 90))
                else:
                    pages.append(self._get_bottom(scan, 90))
                    pages.append(self._get_top(scan, 90))
            if alternating:
                next_rotation = self.alternating_rotation[next_rotation]
        return pages

@singleton    
class PageSorter():

    def sort_pages(self, pages: [], sort_type: SortType):
        
        if sort_type == SortType.STRAIGHT:
            if pages[0].scan.no_of_pages == 2:
                # First page must be placed at the end
                return pages[1:] + [pages[0]]
            else:
                return pages
        
        if sort_type == SortType.SINGLE_ALL_FRONT_ALL_BACK:
            if len(pages) % 2 != 0:
                raise("Ungleiche Anzahl Vorder- und R??ckseiten")
            sorted_pages = []
            for i in range(0, int(len(pages) / 2)):
                sorted_pages.append(pages[i])
                sorted_pages.append(pages[(-1*i)-1])
            return sorted_pages
        
        if sort_type == SortType.SHEET_ALL_FRONT_ALL_BACK:
            if len(pages) % 4 != 0:
                raise("Keine korrekte Seitenzahl f??r Bogensortierung")
            sorted_pages = []
            for i in range(0, int(len(pages) / 2)):
                sorted_pages.append(pages[(i*2)+1])
                sorted_pages.append(pages[len(pages)-(i*2)-2])
            return sorted_pages
        
        if sort_type == SortType.SHEET:
            if len(pages) % 4 != 0:
                raise("Keine korrekte Seitenzahl f??r Bogensortierung")
            sorted_pages = []
            for i in range(0, int(len(pages) / 4)):
                sorted_pages.append(pages[(i*4)+1])
                sorted_pages.append(pages[(i*4)+2])
            for i in range(0, int(len(pages) / 4)):
                sorted_pages.append(pages[len(pages)-(i*4)-1])
                sorted_pages.append(pages[len(pages)-(i*4)-4])
            return sorted_pages

        raise("Diese Sortierung ist noch nicht implementiert!")
    
@singleton
class ProjectGenerator():
    
    @inject
    def __init__(self,
                 number_of_pages_detector: NumberOfPagesDetector,
                 page_generator: PagesGenerator,
                 page_sorter: PageSorter):
        
        self.number_of_pages_detector = number_of_pages_detector
        self.page_generator = page_generator
        self.page_sorter = page_sorter
    
    def scans_to_project(self,
                    scans: [],
                    pages_per_scan: int,
                    sort_type: SortType,
                    scan_rotation: int,
                    rotation_alternating: bool):
    
        if pages_per_scan == 2:
            scans = self.number_of_pages_detector.set_numbers(scans)
        
        pages = self.page_generator.scans_to_pages(
                    scans,
                    scan_rotation,
                    rotation_alternating)
        
        return Project(self.page_sorter.sort_pages(pages, sort_type))
