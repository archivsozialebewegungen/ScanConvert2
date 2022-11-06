'''
Created on 04.11.2022

@author: michael
'''
from injector import provider, BoundKey, Module

from Asb.ScanConvert2.ScanConvertDomain import Page, Region, Scantype, \
    Scan, Algorithm


PAGE_GENERATORS = BoundKey("page generators")

class BasePageGenerator(object):

    def _get_whole(self, scan: Scan, algorithm: Algorithm, angle: int = 0):
        
        return Page(scan, Region(0,0,scan.width,scan.height, algorithm), angle)
    
    def _get_left(self, scan: Scan, algorithm: Algorithm, angle: int = 0):
    
        return Page(scan, Region(0, 0, round(scan.width/2.0), scan.height, algorithm), angle)
    
    def _get_right(self, scan: Scan, algorithm: Algorithm, angle: int = 0):
        
        return Page(scan,
                    Region(round(scan.width/2.0)+1, 0,
                           scan.width-round(scan.width/2.0), scan.height,
                           algorithm),
                    angle)
        
    def _get_top(self, scan: Scan, algorithm: Algorithm, angle: int = 0):

        return Page(scan, Region(0, 0, scan.width, round(scan.height/2.0), algorithm), angle)

    def _get_bottom(self, scan: Scan, algorithm: Algorithm, angle: int = 0):

        return Page(scan,
                    Region(0,round(scan.height/2.0)+1,
                           scan.width, scan.height-round(scan.height/2.0),
                           algorithm),
                    angle)

    def _detect_first_page_needs_splitting(self, scans: []):
        
        area_first_scan = 1.0 * scans[0].width * scans[0].height
        area_second_scan = 1.0 * scans[1].width * scans[1].height
        
        diff = area_second_scan / area_first_scan
        if abs(diff - 2) < 0.1:
            # First scan is nearly half the size of the second scan
            return False
        
        return True
        
class SinglePagesGenerator(BasePageGenerator):
    
    def scans_to_pages(self, scans: [], algorithm: Algorithm):
        
        pages = []
        for scan in scans:
            pages.append(self._get_whole(scan, algorithm))
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
    
    def scans_to_pages(self, scans: [], algorithm: Algorithm):

        if len(scans) == 1:
            return self._simple_one_scan_split(scans[0], algorithm)
                
        first_page_needs_splitting = self._detect_first_page_needs_splitting(scans)

        pages = []
        if first_page_needs_splitting:
            # We start with the right side of the first scan, because the left side
            # is the back couver
            pages.append(self._get_right(scans[0], algorithm))
            for scan in scans[1:]:
                pages.append(self._get_left(scan, algorithm))
                pages.append(self._get_right(scan, algorithm))
            # We finish with the left side of the first scan, see above.
            pages.append(self._get_left(scans[0], algorithm))
        else:
            # We start with the whole first scan
            pages.append(self._get_whole(scans[0], algorithm))
            for scan in scans[1:-1]:
                pages.append(self._get_left(scan, algorithm))
                pages.append(self._get_right(scan, algorithm))
            # We finish with the whole last scan.
            pages.append(self._get_whole(scans[-1], algorithm))
            
        return pages
    
    def _simple_one_scan_split(self, scan: Scan, algorithm: Algorithm):
        """
        If it is just one scan it is probably not a back + a front page
        but just a double sided scan, so no reordering is assumed. Left
        is page 1, right is page 2
        """
            
        pages = []
        pages.append(self._get_left(scan, algorithm))
        pages.append(self._get_right(scan, algorithm))
        return pages
    
class DoublePages90DegreesGenerator(BasePageGenerator):
    '''
    See comment for DoublePagesGenerator. The only difference is the
    rotation of the pages by 90 Degrees
    '''

    def scans_to_pages(self, scans: [], algorithm: Algorithm):

        if len(scans) == 1:
            return self._simple_one_scan_split(scans[0], algorithm)
                
        first_page_needs_splitting = self._detect_first_page_needs_splitting(scans)

        pages = []
        if first_page_needs_splitting:
            # We start with the top side of the first scan, because the bottom side
            # is the back couver
            pages.append(self._get_top(scans[0], algorithm, 90))
            for scan in scans[1:]:
                pages.append(self._get_bottom(scan, algorithm, 90))
                pages.append(self._get_top(scan, algorithm, 90))
            # We finish with the left side of the first scan, see above.
            pages.append(self._get_bottom(scans[0], algorithm, 90))
        else:
            # We start with the whole first scan
            pages.append(self._get_whole(scans[0], algorithm, 90))
            for scan in scans[1:-1]:
                pages.append(self._get_bottom(scan, algorithm, 90))
                pages.append(self._get_top(scan, algorithm, 90))
            # We finish with the whole last scan.
            pages.append(self._get_whole(scans[-1], algorithm, 90))
            
        return pages
    

class PageGeneratorsModule(Module):

    @provider
    def get_page_generators(self) -> PAGE_GENERATORS:
    
        return {
            Scantype.SINGLE: SinglePagesGenerator(),
            Scantype.DOUBLE: DoublePagesGenerator(),
            Scantype.DOUBLE_90: DoublePages90DegreesGenerator(),
        }