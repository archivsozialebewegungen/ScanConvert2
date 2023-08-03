'''
Created on 03.08.2023

@author: michael
'''
import cv2
import numpy as np

class CroppingInformation(object):
    """
    Containerclass for cropping information
    """
    
    def __init__(self, rotation_angle, bounding_box):
        
        self.rotation_angle = rotation_angle
        self.bounding_box = bounding_box
        

class CroppingService(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    def get_cropping_information(self, input_filename):
        
        img = cv2.imread(input_filename, cv2.IMREAD_COLOR)
        contour = self._find_contour(img)
        rotation_angle = self._get_rotation_angle(contour)
        img = self._rotate_image(img, rotation_angle)
        
        contour = self._find_contour(img)
        final_rotation_angle = self._get_rotation_angle(contour)
        assert(abs(final_rotation_angle) < 0.01)

        min_rectangle = cv2.minAreaRect(contour)
        box_points = cv2.boxPoints(min_rectangle)
        bounding_box = (int(box_points[0,0]), int(box_points[1,1]), int(box_points[2,0]), int(box_points[3,1]))
        cv2.drawContours(img, [contour], -1, (0,0,255), 15)
        cv2.rectangle(img, bounding_box[0:2], bounding_box[2:4], (0,255,0), 15)
        cv2.imwrite("/tmp/contour.tif", img)
        
        return CroppingInformation(rotation_angle, bounding_box)
        
    def _get_rotation_angle(self, contour):
        
        min_rectangle = cv2.minAreaRect(contour)
        
        rectangle_angle = min_rectangle[2]
        if abs(rectangle_angle) < 20.0:
            return rectangle_angle
        if abs(rectangle_angle - 90) < 20.0:
            return (rectangle_angle - 90)
        raise Exception("Strange angle")
        
            
    def _find_contour(self, cv_img):
        
        imgray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        ret, bw = cv2.threshold(imgray, 127, 255, 0)
        
        contours, hierarchy = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_contour = None
        max_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_contour = contour
                max_area = area
        return max_contour
    
    def _rotate_image(self, image, angle):
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result
        