'''
Created on 28.01.2023

@author: michael
'''
from PySide6.QtWidgets import QGraphicsView, QRubberBand, QGraphicsScene
from PIL import Image
from PySide6.QtGui import QPixmap
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QRect, QSize, QPoint, QRectF
from Asb.ScanConvert2.ScanConvertDomain import Region

class PageViewBase(object):
    """
    This base class is used to separate (some of) the
    logic of the display in a testable class that
    needs no Qt classes.
    """
    
    def _get_screen_selection(self):
        """
        This should return the selection in the
        img as it is displayed
        """
        
        raise Exception("Implement in child class")
    
    def _get_screen_img_size(self):
        
        raise Exception("Implement in child class")

    def _get_page_img_size(self):
        
        raise Exception("Implement in child class")

    def _get_offsets(self):

        raise Exception("Implement in child class")

    def _get_img_screen_ratio(self):

        img_size = self._get_page_img_size()
        screen_size = self._get_screen_img_size()
        
        if abs(self.geometry().width() - screen_size[0]) < 0.01:
            ratio = img_size[0] / screen_size[0]
        else:
            #assert(self.geometry().height() == screen_size[1])
            ratio = img_size[1] / screen_size[1]
        
        return ratio

    def _calculate_img_region(self):

        img_screen_ratio = self._get_img_screen_ratio()        
        screen_selection = self._get_screen_selection()
        (x_offset, y_offset) = self._get_offsets()
        return Region((screen_selection[0] - x_offset) * img_screen_ratio,
                      (screen_selection[1] - y_offset) * img_screen_ratio,
                      screen_selection[2] * img_screen_ratio,
                      screen_selection[3] * img_screen_ratio
                    )

    def _calculate_screen_selection(self, region: Region):
        
        img_screen_ratio = self._get_img_screen_ratio()
        (x_offset, y_offset) = self._get_offsets()
        return (region.x / img_screen_ratio + x_offset,
                region.y / img_screen_ratio + y_offset,
                region.width / img_screen_ratio,
                region.height / img_screen_ratio,
                )
    
class PageView(QGraphicsView, PageViewBase):
    
    def __init__(self):
        
        QGraphicsView.__init__(self)
        self.img = None
        self.img_region_cache = None
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.reset_rubberband()
        self.region_select = False

    def set_page(self, img: Image):

        self.img = img
        self.region_cache = None
        pixmap = QPixmap(ImageQt(self.img))
        self.scene = QGraphicsScene()
        self.scene.addPixmap(pixmap)
        self.invalidateScene()
        self.setScene(self.scene)
        self.fitInView(self.image_rectangle, Qt.AspectRatioMode.KeepAspectRatio)
        self.reset_rubberband()

    def reset_rubberband(self):
        
        self.rubberBand.setGeometry(QRect(0,0,0,0).normalized())
        self.rubberBand.hide()
        self.img_region_cache = None

    def _get_screen_selection(self):
        
        (sel_x1,  sel_y1, sel_x2, sel_y2) = self.rubberBand.geometry().getCoords()
        
        return(sel_x1, sel_y1, sel_x2 - sel_x1 + 1, sel_y2 - sel_y1 + 1)

    def _get_screen_img_size(self):
        
        scale = self._get_scale()
        width = self.img.size[0] * scale 
        height = self.img.size[1] * scale
        
        #geometry = self.geometry()
        #assert((height == geometry.height() and width < geometry.width()) or
        #       (height < geometry.height() and width == geometry.width())) 
        
        return (width, height)

    def _get_page_img_size(self):
        
        return self.img.size
    
    def mousePressEvent(self, event):

        if not self.region_select:
            return
                
        self.origin = event.pos()
        self.rubberBand.setGeometry(QRect(self.origin, QSize()).normalized())
        self.rubberBand.show()

    def mouseMoveEvent(self, event):

        if not self.region_select:
            return

        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        self.region_cache = self._calculate_img_region()

    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        if self.img is not None:
            self.fitInView(self.image_rectangle, Qt.AspectRatioMode.KeepAspectRatio)
            if self.img_region_cache is not None:
                self.show_region(self.img_region_cache)
    
    def show_region(self, region: Region):

        self.img_region_cache = region

        screen_selection = self._calculate_screen_selection(region)
            
        self.origin = QPoint(screen_selection[0], screen_selection[1])
        size = QSize(screen_selection[2], screen_selection[3])
        
        self.rubberBand.hide()
        self.rubberBand.setGeometry(QRect(self.origin, size).normalized())
        self.rubberBand.show()

    def get_selected_region(self):
        
        return self.region_cache

    def _get_scale(self):

        graphics_view_geometry = self.geometry()
        
        scale_x = 1.0 * graphics_view_geometry.width() / self.img.width
        scale_y = 1.0 * graphics_view_geometry.height() / self.img.height

        if scale_x > scale_y:
            return scale_y
        
        return scale_x
        
    def _get_offsets(self):

        scale = self._get_scale()
        
        scaled_img_width = self.img.width * scale
        scaled_img_height = self.img.height * scale
        
        x_offset = round((self.geometry().width() - scaled_img_width) / 2)
        y_offset = round((self.geometry().height() - scaled_img_height) / 2)
        
        assert(x_offset == 0 or y_offset == 0)
        
        return (x_offset, y_offset)

    image_rectangle = property(lambda self: QRectF(0, 0, self.img.width, self.img.height))
