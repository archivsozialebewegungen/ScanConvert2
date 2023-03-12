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

from PIL import Image, ImageFilter, ImageOps
import cv2
from injector import Module, BoundKey, provider, singleton
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola, \
    threshold_niblack

import numpy as np
from math import sqrt
from numpy.core._multiarray_umath import dtype

Image.MAX_IMAGE_PIXELS = None

WHITE = (255, 255, 255)

AlgorithmImplementations = BoundKey("algorithm implementations")

class TooManyColors(Exception):

    pass

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
    ERASE=10
    STENCIL_PRINT_GOOD=11
    STENCIL_PRINT_BAD=12

    
    def __str__(self):
        texts = {
            Algorithm.NONE: "Modus beibehalten",
            Algorithm.GRAY: "Graustufen",
            Algorithm.GRAY_WHITE: "Grauer Text auf weißem Papier",
            Algorithm.OTSU: "Normal schwarzer Text auf weißem Papier",
            Algorithm.SAUVOLA: "Krisseliger Text auf weißem Papier",
            Algorithm.FLOYD_STEINBERG: "SW Photo",
            Algorithm.COLOR_PAPER_QUANTIZATION: "Text auf farbigem Papier",
            Algorithm.COLOR_TEXT_QUANTIZATION: "Farbiger Text auf weißem Papier",
            Algorithm.TWO_COLOR_QUANTIZATION: "Farbiger Text auf farbigem Papier",
            Algorithm.ERASE: "Ausradieren",
            Algorithm.STENCIL_PRINT_GOOD: "Guter Matrizendruck",
            Algorithm.STENCIL_PRINT_BAD: "Schlechter Matrizendruck"
        }
    
        return texts[self]

class AlgorithmHelper(object):

    def get_white_for_mode(self, mode):
    
        if mode == "1":
            return 1
        elif mode == "L":
            return 255
        else:
            return WHITE
    
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

    def replace_color_with_color(self, img: Image, src_color: (), target_color: ()) -> Image:
        
        resolution = self.get_image_resolution(img)
        
        np_array = np.array(img.convert("RGB"))
        red, green, blue = np_array.T
        src_color_areas = (red == src_color[0]) & (green == src_color[1]) & (blue == src_color[2])
        np_array[src_color_areas.T] = target_color
        
        img = Image.fromarray(np_array)
        img.info['dpi'] = (resolution, resolution)
        
        return img

    def get_colors(self, img: Image):
        
        color_infos = img.convert("RGB").getcolors()
        if color_infos is None:
            raise TooManyColors()
        
        colors = []
        for info in color_infos:
            colors.append(info[1])
        return colors

    def replace_white_with_color(self, img: Image, color: ()) -> Image:
        
        if color == WHITE:
            return img
        
        return self.replace_color_with_color(img, WHITE, color)
    
    def colors_are_similar(self, color1: (), color2: ()):
        
        value1 = sqrt(color1[0]^2 + color1[1]^2 + color1[2]^2)
        value2 = sqrt(color2[0]^2 + color2[1]^2 + color2[2]^2)
        return abs(value1 - value2) < 5
    
class ModeTransformationAlgorithm(AlgorithmHelper):
    """
    This is the base class for all ModeTransformationAlgorithms
    """
    
    def transform(self, img: Image, bg_color: () = WHITE) -> (Image, ()):
        
        raise Exception("Please implement in child class")
    
class NoneAlgorithm(ModeTransformationAlgorithm):
    """
    This implementation does nothing to the image.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE)->Image:

        # Replacement of background color does not make sense,
        # so we just return the background color without
        # application to the image
        return (img, bg_color)

class Gray(ModeTransformationAlgorithm):
    """
    Converts the image to a gray scale image regardless of the
    mode type of the input image, i.e., black and white will get
    transformed also to gray.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        
        # Replacement of background color does not make sense,
        # so we just return the background color without
        # application to the image
        return (img.convert("L"), bg_color)

class FloydSteinberg(ModeTransformationAlgorithm):
    """
    This uses the default PIL conversion mode to black and white
    which applies the Floyd-Steinberg algorithm
    """

    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        
        img = img.convert("1")
        if bg_color is None:
            return (img, WHITE)
        
        return (self.replace_white_with_color(img, bg_color), bg_color)
        

class ThresholdAlgorithm(ModeTransformationAlgorithm):
    """
    For thresholding there are mask implementations in cv2. This
    is a base class to apply several cv2 thresholding algorithms
    to a PIL image.
    """
    
    def apply_cv2_mask(self, img:Image, bg_color: (), mask_implementation, **nargs) -> (Image, ()):
        
        resolution = self.get_image_resolution(img)
        in_array = np.asarray(img.convert("L"))
        mask = mask_implementation(in_array, **nargs)
        out_array = in_array > mask

        img = Image.fromarray(out_array)
        img.info['dpi'] = (resolution, resolution)
        
        if bg_color is None:
            return (img.convert("1"), WHITE)
        
        np_array = np.array(img.convert("RGB"))
        red, green, blue = np_array.T
        white_areas = (red == 255) & (green == 255) & (blue == 255)
        np_array[white_areas.T] = bg_color
        
        img = Image.fromarray(np_array)
        img.info['dpi'] = (resolution, resolution)
        
        return (img, bg_color)

class Otsu(ThresholdAlgorithm):
    """
    The bread and butter algorithm to convert scans to black and white.
    Works very well on even text and handles backgrounds like recycling
    paper well. It is not so strong on images and does a terrible job
    if the background is spotted or the text color uneven.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        return self.apply_cv2_mask(img, bg_color, threshold_otsu)

class Sauvola(ThresholdAlgorithm):
    """
    This is a (slower) alternative to Otsu that works best if the background
    is spotty or the text color uneven. Sometimes it also improves
    quantization on slanted characters.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        return self.apply_cv2_mask(img, bg_color, threshold_sauvola, window_size=51)
    
class Niblack(ThresholdAlgorithm):
    """
    It is, like Sauvola, a local thresholding algorithm but I did not find
    a use case where either Otsu or Sauvola would have produced a superior result.
    """

    def transform(self, img:Image, bg_color) -> (Image, ()):
        return self.apply_cv2_mask(img, bg_color, threshold_niblack, window_size=11)

class GoodStencilPrint(ThresholdAlgorithm):

    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):

        img_rgb = img.convert("RGB")
        np_rgb = np.asarray(img_rgb)
        np_converted = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2HSV)
        (p1, p2, p3) = np_converted.transpose()

        np_gray = np.array([p3, p3, p3]).transpose()
        img_gray = Image.fromarray(np_gray)
        img_gray.info['dpi'] = img.info['dpi']
        
        return Otsu().transform(img_gray)
    
class BadStencilPrint(ThresholdAlgorithm):
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):

        img_rgb = img.convert("RGB")
        np_rgb = np.asarray(img_rgb)
        np_converted = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2HLS)
        (p1, p2, p3) = np_converted.transpose()

        np_gray = np.array([p3, p3, p3]).transpose()
        img_gray = Image.fromarray(np_gray)
        img_gray.info['dpi'] = img.info['dpi']
        
        return Sauvola().transform(img_gray)


class QuantizationAlgorithm(ModeTransformationAlgorithm):
    """
    Base class for transforming images using a k-means algorithm to
    extract the 2 dominant colors of an image
    """
    
    def _apply_quantization(self, img: Image, no_of_colors=2) -> (Image, ()):
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
        
        return (new_img, self._find_bg_color(new_img))

    def _find_bg_color(self, quantized_img: Image) -> ():

        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            return colors[0][1] 
        else: 
            return colors[1][1] 
    
    def _find_fg_color(self, quantized_img: Image) -> ():
        
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 > sum0:
            return colors[0][1] 
        else: 
            return colors[1][1] 
        
class TwoColors(QuantizationAlgorithm):
    
    def transform(self, img:Image, bg_color: () = None)-> (Image, ()):
        
        (img, calculated_bg_color) = self._apply_quantization(img)
        if bg_color is None:
            return (img, calculated_bg_color)
        else:
            return (self.replace_color_with_color(img, calculated_bg_color, bg_color), bg_color)

class ColorTextOnWhite(QuantizationAlgorithm):
    """
    This is most useful if you have some color elements on an
    otherwise black and white document (for example red headings
    or a blue signature). Then you may apply regions in combination
    with this algorithm to these color segments and retain the color.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        
        if bg_color is None:
            bg_color = WHITE
            
        quantized_img, quantized_bg_color = self._apply_quantization(img)

        np_img = np.array(quantized_img)
        red, green, blue = np_img.T

        bg_areas = (red == quantized_bg_color[0]) & (green == quantized_bg_color[1]) & (blue == quantized_bg_color[2])
        np_img[bg_areas.T] = bg_color

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return (final_img, bg_color)

class BlackTextOnColor(QuantizationAlgorithm):
    """
    This is the algorithm to use when you have black printed on a color paper.
    """
    
    def transform(self, img:Image, bg_color: () = None)  -> (Image, ()):
        
        quantized_img, calculated_bg_color = self._apply_quantization(img)
        fg_color = self._find_fg_color(quantized_img)
        
        np_img = np.array(quantized_img)
        red, green, blue = np_img.T

        black_areas = (red == fg_color[0]) & (green == fg_color[1]) & (blue == fg_color[2])
        np_img[black_areas.T] = (0, 0, 0)

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        if bg_color is None:
            return (final_img, calculated_bg_color)

        return (self.replace_color_with_color(final_img, calculated_bg_color, bg_color), bg_color)

class GrayTextOnWhite(Otsu):
    """
    This is not the most useful of algorithms, but if you want to keep
    the text in grayscale but want to clean up the background to pure
    white, this is the algorithm to use
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        
        (mask, col) = super().transform(img, bg_color)
        mask = mask.convert("RGB")
        mask = mask.filter(ImageFilter.BLUR)

        np_img = np.array(img.convert("RGB"))
        np_mask = np.array(mask)
        red, green, blue = np_mask.T

        white_areas = (red == 255) & (green == 255) & (blue == 255)
        np_img[white_areas.T] = (255, 255, 255)

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        if bg_color is None or bg_color == WHITE:
            return (final_img.convert("L"), WHITE)
        
        return (self.replace_white_with_color(final_img, bg_color), bg_color)
    
class Erase(ModeTransformationAlgorithm):
    """
    This returns just a white image in the same size to patch
    over holes, missing corners etc. on the scan.
    """
    
    def transform(self, img:Image, bg_color: () = WHITE) -> (Image, ()):
        
        resolution = self.get_image_resolution(img)
        if bg_color is None or bg_color == WHITE:
            img = Image.new(img.mode, img.size, self.get_white_for_mode(img.mode))
            img.info['dpi'] = (resolution, resolution)
            return (img, WHITE)
        
        img = Image.new("RGB", img.size, bg_color)
        img.info['dpi'] = (resolution, resolution)
        return (img, bg_color)
    
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
                Algorithm.TWO_COLOR_QUANTIZATION: TwoColors(),
                Algorithm.COLOR_PAPER_QUANTIZATION: BlackTextOnColor(),
                Algorithm.COLOR_TEXT_QUANTIZATION: ColorTextOnWhite(),
                Algorithm.STENCIL_PRINT_GOOD: GoodStencilPrint(),
                Algorithm.STENCIL_PRINT_BAD: BadStencilPrint(),
                Algorithm.ERASE: Erase()}
