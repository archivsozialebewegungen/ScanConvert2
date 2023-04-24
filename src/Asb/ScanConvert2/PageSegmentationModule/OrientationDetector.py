'''
Created on 16.04.2023

@author: michael
'''
import pytesseract
from pytesseract.pytesseract import Output
from PIL import Image
from injector import singleton

rotations = {90: Image.ROTATE_90,
             180: Image.ROTATE_180,
             270: Image.ROTATE_270}

@singleton
class OrientationCorrectionService(object):
    '''
    classdocs
    '''

    
    def correct_orientation(self, img):
        
        correction = self._determine_correction(img)
        if correction == 0:
            return img
        
        return img.transpose(rotations[correction])
        
    def _determine_correction(self, img):
        
        try:
            orientation = pytesseract.image_to_osd(img, output_type=Output.DICT)
        except:
            return 0
        return orientation["orientation"]
        
        