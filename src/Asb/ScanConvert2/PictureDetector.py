'''
This class tries to detect pictures in an image,
because in binarization we want to treat pictures
differently from text areas.

The idea is: We use tesseracts segmentation algorithm
to split the provided images into areas. And then
we use the histogram of the different areas to determine,
if this really is text or a picture in the text.

Created on 06.01.2023

@author: michael
'''
import pytesseract
from PIL import Image, ImageOps
from xml.dom.minidom import parseString
import re
import numpy as np
from skimage.filters.thresholding import threshold_otsu
import cv2

class PictureDetector(object):
    
    def __init__(self):
        
        self.re_boundingbox = re.compile(r'bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+).*')

    def find_pictures(self, img: Image) -> Image:
        
        img = self._convert_to_bw(img)
        # should improve segmentation
        img = self._denoise_img(img)
        pictures = []
        for bbox in self._get_areas(img):
            if self._is_image_area(bbox, img):
                pictures.append(bbox)
            
        return pictures
    
    def _is_image_area(self, bbox, img: Image) -> bool:
        
        part = img.crop(bbox)
        histogram = part.histogram()
        if histogram[255] == 0:
            return True
        ratio = 1.0 * histogram[0] / histogram[255]
        return ratio > 0.6
    
    def _get_areas(self, img: Image) -> []:
        
        hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr', lang="deu", config='--psm 1')
        bboxes = []
        dom = parseString(hocr)
        #with open("/tmp/hocr.xml", "w") as output:
        #    output.write(dom.toprettyxml("  "))
        for element in dom.getElementsByTagName("div"):
            if element.getAttribute("class") == "ocr_carea":
                matcher = re.match(self.re_boundingbox, element.getAttribute("title"))
                if matcher:
                    bboxes.append((int(matcher.group(1)),
                                   int(matcher.group(2)),
                                   int(matcher.group(3)),
                                   int(matcher.group(4))))
        return bboxes
                                   
    def _convert_to_bw(self, img: Image) -> Image:
        
        in_array = np.asarray(img.convert("L"))
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        return Image.fromarray(out_array)

    def _denoise_img(self, img: Image) -> Image:
        
        
        no_of_components, labels, sizes = self._connected_components_with_stats(img)

        threshold = 13

        bw_new = np.ones((labels.shape), dtype=bool)
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] > threshold:
                bw_new[labels == shape_identifier] = 0
        return Image.fromarray(bw_new)

    def _connected_components_with_stats(self, img: Image):
        '''
        Just a wrapper around the cv2 method.
        '''

        inverted = ImageOps.invert(img.convert("RGB"))
        ndarray = np.array(inverted.convert("1"), dtype=np.uint8)
        no_of_components, labels, stats, centroids = cv2.connectedComponentsWithStats(ndarray, connectivity=8)
        sizes = stats[:, cv2.CC_STAT_AREA]
        
        # Leave out background 
        return no_of_components, labels, sizes
