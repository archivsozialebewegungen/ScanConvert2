'''
This packages a lot of different algorithms to change the mode
of an image - mostly to two colors. This module should never
have any dependencies on any other part of the scan converter.

It just provides a list of the available algorithms (as Enum) and
a map of all implementations.

Created on 18.01.2023

@author: michael
'''
from enum import Enum

from PIL import Image, ImageFilter
import cv2
from injector import Module, BoundKey, provider, singleton
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola, \
    threshold_niblack

import numpy as np


AlgorithmImplementations = BoundKey("algorithm implementations")

class Algorithm(Enum):

    NONE=1
    GRAY=2
    GRAY_WHITE=3
    OTSU=4
    SAUVOLA=5
    #NIBLACK=6
    FLOYD_STEINBERG=7
    COLOR_PAPER_QUANTIZATION=8
    COLOR_TEXT_QUANTIZATION=9
    TWO_COLOR_QUANTIZATION=10
    WEISS=11

    
    def __str__(self):
        texts = {
            Algorithm.NONE: "Modus beibehalten",
            Algorithm.GRAY: "Graustufen",
            Algorithm.GRAY_WHITE: "Grauer Text auf weißem Papier",
            Algorithm.OTSU: "Normal schwarzer Text auf weißem Papier",
            #Algorithm.NIBLACK: "SW NIBLACK (Text fleckig)",
            Algorithm.SAUVOLA: "Krisseliger Text auf weißem Papier",
            Algorithm.FLOYD_STEINBERG: "Photo",
            Algorithm.COLOR_PAPER_QUANTIZATION: "Text auf farbigem Papier",
            Algorithm.COLOR_TEXT_QUANTIZATION: "Farbiger Text auf weißem Papier",
            Algorithm.TWO_COLOR_QUANTIZATION: "Farbiger Text auf farbigem Papier",
            Algorithm.WEISS: "Ausradieren"
        }
    
        return texts[self]

class ModeTransformationAlgorithm(object):
    """
    This is the base class for all ModeTransformationAlgorithms
    """
    
    def transform(self, img: Image) -> Image:
        
        raise Exception("Please implement in child class")
    
    def get_image_resolution(self, img: Image) -> int:
        
        if not 'dpi' in img.info:
            return 300
        
        xres, yres = img.info['dpi']
        if xres == 1 or yres == 1:
            raise Exception("No valid resolution!")
        
        if xres != yres:
            raise Exception("No support for different x/y resolutions")
    
        # newer versions of Pillow return a float
        return round(xres)
    
class NoneAlgorithm(ModeTransformationAlgorithm):
    """
    This implementation does nothing to the image.
    """
    
    def transform(self, img:Image)->Image:
        return img

class Gray(ModeTransformationAlgorithm):
    """
    Converts the image to a gray scale image regardless of the
    mode type of the input image, i.e., black and white will get
    transformed also to gray.
    """
    
    def transform(self, img:Image)->Image:
        
        return img.convert("L")
    
class FloydSteinberg(ModeTransformationAlgorithm):
    """
    This uses the default PIL conversion mode to black and white
    which applies the Floyd-Steinberg algorithm
    """

    def transform(self, img:Image)->Image:
        return img.convert("1")

class ThresholdAlgorithm(ModeTransformationAlgorithm):
    """
    For thresholding there are mask implementations in cv2. This
    is a base class to apply several cv2 thresholding algorithms
    to a PIL image.
    """
    
    def apply_cv2_mask(self, img:Image, mask_implementation, **nargs)->Image:
        
        resolution = self.get_image_resolution(img)
        in_array = np.asarray(img.convert("L"))
        mask = mask_implementation(in_array, **nargs)
        out_array = in_array > mask
        img = Image.fromarray(out_array)
        img.info['dpi'] = (resolution, resolution)
        img.convert("1")

        return img

class Otsu(ThresholdAlgorithm):
    """
    The bread and butter algorithm to convert scans to black and white.
    Works very well on even text and handles backgrounds like recycling
    paper well. It is not so strong on images and does a terrible job
    if the background is spotted or the text color uneven.
    """
    
    def transform(self, img:Image)->Image:
        return self.apply_cv2_mask(img, threshold_otsu)

class Sauvola(ThresholdAlgorithm):
    """
    This is a (slower) alternative to Otsu that works best if the background
    is spotty or the text color uneven. Sometimes it also improves
    quantization on slanted characters.
    """
    
    def transform(self, img:Image)->Image:
        return self.apply_cv2_mask(img, threshold_sauvola, window_size=11)
    
class Niblack(ThresholdAlgorithm):
    """
    It is, like Sauvola, a local thresholding algorithm but I did not find
    a use case where either Otsu or Sauvola would have produced a superior result.
    """

    def transform(self, img:Image)->Image:
        return self.apply_cv2_mask(img, threshold_niblack, window_size=11)

class QuantizationAlgorithm(ModeTransformationAlgorithm):
    """
    Base class for transforming images using a k-means algorithm to
    extract the 2 dominant colors of an image
    """
    
    def _apply_quantization(self, img: Image, no_of_colors=2) -> Image:
        """
        Uses the k-means algorithm to quantize the image for two colors
        """
        
        img = img.convert("RGB")
        np_array = np.array(img)
        flattend = np.float32(np_array).reshape(-1,3)
        condition = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,20,1.0)
        ret,label,center = cv2.kmeans(flattend, no_of_colors , None, condition, 10, cv2.KMEANS_RANDOM_CENTERS)
        center = np.uint8(center)
        final_flattend = center[label.flatten()]
        final_img_array = final_flattend.reshape(np_array.shape)
        
        new_img = Image.fromarray(final_img_array)
        new_img.info['dpi'] = img.info['dpi']
        
        return new_img
    
class TwoColors(QuantizationAlgorithm):
    
    def transform(self, img:Image)->Image:
        return self._apply_quantization(img)

class ColorTextOnWhite(QuantizationAlgorithm):
    """
    This is most useful if you have some color elements on an
    otherwise black and white document (for example red headings
    or a blue signature). Then you may apply regions in combination
    with this algorithm to these color segments and retain the color.
    """
    
    def transform(self, img:Image)->Image:
        
        quantized_img = self._apply_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            white = colors[0][1] 
        else: 
            white = colors[1][1] 
        
        np_img = np.array(quantized_img)   # "data" is a height x width x 4 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        # Replace white with red... (leaves alpha values alone...)
        white_areas = (red == white[0]) & (green == white[1]) & (blue == white[2])
        np_img[white_areas.T] = (255, 255, 255) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img

class BlackTextOnColor(QuantizationAlgorithm):
    """
    This is the algorithm to use when you have black printed on a color paper.
    """
    
    def transform(self, img:Image)->Image:
        
        quantized_img = self._apply_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            black = colors[1][1]
        else: 
            black = colors[0][1]
        
        np_img = np.array(quantized_img)   # "data" is a height x width x 3 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        black_areas = (red == black[0]) & (green == black[1]) & (blue == black[2])
        np_img[black_areas.T] = (0, 0, 0) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img

class GrayTextOnWhite(Otsu):
    """
    This is not the most useful of algorithms, but if you want to keep
    the text in grayscale but want to clean up the background to pure
    white, this is the algorithm to use
    """
    
    def transform(self, img:Image)->Image:
        
        mask = super().transform(img)
        mask = mask.convert("RGB")
        mask = mask.filter(ImageFilter.BLUR)

        np_img = np.array(img.convert("RGB"))
        np_mask = np.array(mask)
        red, green, blue = np_mask.T

        white_areas = (red == 255) & (green == 255) & (blue == 255)
        np_img[white_areas.T] = (255, 255, 255)

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img.convert("L")
    
class White(ModeTransformationAlgorithm):
    """
    This returns just a white image in the same size to patch
    over holes, missing corners etc. on the scan.
    """
    
    def transform(self, img:Image)->Image:
        new_img = Image.new("1", img.size, 1)
        new_img.info['dpi'] = img.info['dpi']
        return new_img

    
class AlgorithmModule(Module):
    """
    This is the injector module
    """
    
    @provider
    @singleton
    def algorithm_provider(self) -> AlgorithmImplementations:
        
        return {Algorithm.NONE: NoneAlgorithm(),
                Algorithm.GRAY: Gray(),
                Algorithm.GRAY_WHITE: GrayTextOnWhite(),
                Algorithm.FLOYD_STEINBERG: FloydSteinberg(),
                Algorithm.OTSU: Otsu(),
                Algorithm.SAUVOLA: Sauvola(),
                #Algorithm.NIBLACK: Niblack(),
                Algorithm.TWO_COLOR_QUANTIZATION: TwoColors(),
                Algorithm.COLOR_PAPER_QUANTIZATION: BlackTextOnColor(),
                Algorithm.COLOR_TEXT_QUANTIZATION: ColorTextOnWhite(),
                Algorithm.WEISS: White()}
