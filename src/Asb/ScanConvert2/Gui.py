'''
Created on 06.11.2022

@author: michael
'''
import os
import pickle
import shutil
import sys
import tempfile

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QRect, QSize, QRectF, Qt, QPoint
from PySide6.QtGui import QPixmap, QAction, QIcon
from PySide6.QtWidgets import QGraphicsScene, QRubberBand, \
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, \
    QMainWindow, \
    QWidget, QGraphicsView, QApplication, QComboBox, QFileDialog, QGroupBox,\
    QButtonGroup, QRadioButton, QCheckBox
from injector import inject, Injector, singleton

from Asb.ScanConvert2.ProjectWizard import ExpertProjectWizard
from Asb.ScanConvert2.ScanConvertDomain import Project, \
    Region, ALGORITHM_TEXTS, Page
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Asb.ScanConvert2.TaskRunner import ExportTarget, TaskManager, JobDefinition


CREATE_REGION = "Region anlegen"
APPLY_REGION = "Auswahl übernehmen"
DELETE_REGION = "Region löschen"
CANCEL_REGION = "Auswahl abbrechen"

class PageView(QGraphicsView):
    
    def __init__(self):
        
        super().__init__()
        self.img = None
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.reset_rubberband()
        self.selection_cache = (0,0,0,0)
        self.region_select = False

    def set_page(self, img: Image):

        self.img = img
        pixmap = QPixmap(ImageQt(self.img))
        self.scene = QGraphicsScene()
        self.scene.addPixmap(pixmap)
        self.invalidateScene()
        self.setScene(self.scene)
        self.fitInView(self.image_rectangle, Qt.AspectRatioMode.KeepAspectRatio)
        self.reset_rubberband()

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

    def mouseReleaseEvent(self, event):
        
        if not self.region_select:
            return

        self.cache_img_selection()
        
    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        if self.img is not None:
            self.fitInView(self.image_rectangle, Qt.AspectRatioMode.KeepAspectRatio)
        self.restore_img_selection()

    def show_region(self, region: Region):

        self.selection_cache = (region.x, region.y, region.x2, region.y2)
        self.restore_img_selection()
        return
        
    def restore_img_selection(self):
        
        if self.selection_cache == (0,0,0,0):
            return
        
        (scale, x_offset, y_offset) = self._get_scale_and_offsets()
                
        rubberband_x1 = int((self.selection_cache[0] * scale) + x_offset)
        rubberband_y1 = int((self.selection_cache[1] * scale) + y_offset)
        rubberband_width = int(((self.selection_cache[2] - self.selection_cache[0]) * scale))
        rubberband_height = int(((self.selection_cache[3] - self.selection_cache[1]) * scale))
        
        self.origin = QPoint(rubberband_x1, rubberband_y1)
        self.rubberBand.hide()
        self.rubberBand.setGeometry(QRect(QPoint(rubberband_x1, rubberband_y1), QSize(rubberband_width, rubberband_height)).normalized())
        self.rubberBand.show()

    def reset_rubberband(self):
        
        self.selection_cache = (0,0,0,0)
        self.rubberBand.setGeometry(QRect(0,0,0,0).normalized())
        self.rubberBand.hide()
        
    def cache_img_selection(self):
        
        (scale, x_offset, y_offset) = self._get_scale_and_offsets()
        
        (sel_x1,  sel_y1, sel_x2, sel_y2) = self.rubberBand.geometry().getCoords()
        page_x1 = (sel_x1 - x_offset) / scale
        page_x2 = (sel_x2 - x_offset) / scale
        page_y1 = (sel_y1 - y_offset) / scale
        page_y2 = (sel_y2 - y_offset) / scale

        if page_x1 < 0:
            page_x1 = 0
        if page_x2 > self.img.width:
            page_x2 = self.img.width
        if page_y1 < 0:
            page_y1 = 0
        if page_y2 > self.img.height:
            page_y2 = self.img.height
        
        if page_x1 > self.img.width or \
            page_y1 > self.img.height or \
            page_x2 < 0 or \
            page_y2 < 0:
            
            self.selection_cache = (0,0,0,0)

        self.selection_cache = (page_x1, page_y1, page_x2, page_y2)

    def _get_scale_and_offsets(self):

        graphics_view_geometry = self.geometry()
        
        scale_x = graphics_view_geometry.width() / self.img.width
        scale_y = graphics_view_geometry.height() / self.img.height

        scale = scale_x
        if scale_x > scale_y:
            scale = scale_y

        scaled_img_width = self.img.width * scale
        scaled_img_height = self.img.height * scale
        
        x_offset = int((self.geometry().width() - scaled_img_width) / 2)
        y_offset = int((self.geometry().height() - scaled_img_height) / 2)
        
        assert(x_offset == 0 or y_offset == 0)
        
        return (scale, x_offset, y_offset)

    def get_selected_region(self):
        
        x1 = int(self.selection_cache[0])
        y1 = int(self.selection_cache[1])
        x2 = int(self.selection_cache[2])
        y2 = int(self.selection_cache[3])
        width = x2 - x1
        height = y2 - y1
        return Region(x1, y1, width, height)
                
    image_rectangle = property(lambda self: QRectF(0, 0, self.img.width, self.img.height))

@singleton
class FehPreviewer(object):
    
    def __init__(self):
        
        self.feh = shutil.which("feh")
        
    def show(self, page: Page):
        
        img = page.get_final_image()
        tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".png")
        img.save(tmp_file, format="png")
        os.system("%s %s" % (self.feh, tmp_file.name))
        tmp_file.close()

    def is_working(self):
        
        return self.feh is not None

@singleton
class Window(QMainWindow):
    

    @inject
    def __init__(self,
                 project_service: ProjectService,
                 task_manager: TaskManager,
                 previewer: FehPreviewer):

        super().__init__()
        
        self.current_page_no = 0
        self.current_region_no = 0
        self.no_of_pages = 0
        self.no_of_regions = 0
        
        self.project_service = project_service
        self.task_manager = task_manager
        self.task_manager.message_function = self.show_job_status
        self.previewer = previewer
        
        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle("Scan-Kovertierer")
        self._create_widgets()
        self.project = None
        
        self.task_manager.message_function()
    
    def _create_widgets(self):

        self.statusBar().showMessage("Programm gestartet...")

        self._create_menu_bar()
        
        self.main_layout = QHBoxLayout()
        
        self.main_layout.addLayout(self._get_left_panel())
        self.main_layout.addLayout(self._get_right_panel())
        
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)

        self.setCentralWidget(central_widget)
        

    def _get_left_panel(self):
        
        left_panel = QVBoxLayout()
        
        label = QLabel("<b>Seiteneinstellungen</b>")
        left_panel.addWidget(label)
        label = QLabel("Navigation:")
        left_panel.addWidget(label)
        left_panel.addLayout(self._get_page_scroller())
        label = QLabel("Algorithmus:")
        left_panel.addWidget(label)
        left_panel.addLayout(self._get_page_params_layout())
        left_panel.addLayout(self._get_rotate_box())
        self.skip_page_checkbox = QCheckBox("Seite überspringen")
        self.skip_page_checkbox.clicked.connect(self._toggle_skip_page)
        left_panel.addWidget(self.skip_page_checkbox)
        if self.previewer.is_working():
            preview_button = QPushButton("Vorschau")
            preview_button.clicked.connect(self._show_current_page)
            left_panel.addWidget(preview_button)
            
        label = QLabel("<b>Regioneneinstellungen</b>")
        left_panel.addWidget(label)
        label = QLabel("Navigation:")
        left_panel.addWidget(label)
        left_panel.addLayout(self._get_region_scroller())
        label = QLabel("Algorithmus:")
        left_panel.addWidget(label)
        left_panel.addLayout(self._get_region_params_layout())
        
        self.task_label = QLabel("Nicht initalisiert")
        left_panel.addWidget(self.task_label)
        
        left_panel.addStretch(10)
        return left_panel
    
    def _toggle_skip_page(self):
        
        if self.current_page_no is None:
            return
        self.current_page.skip_page = self.skip_page_checkbox.isChecked()
        
    def _get_page_params_layout(self):
        
        page_params = QVBoxLayout()
        self.main_algo_select = self._get_algorithm_combobox()
        self.main_algo_select.currentIndexChanged.connect(self._main_algo_changed)
        page_params.addWidget(self.main_algo_select)
        return page_params

    def _get_rotate_box(self):
        
        complete_box = QVBoxLayout()
                    
        rotate_box = QGroupBox("Drehen")
        rotate_layout = QHBoxLayout()
        rotate_group = QButtonGroup(self)
        self.rotate_0 = QRadioButton("0°", self)
        self.rotate_0.setChecked(True)
        self.rotate_0.toggled.connect(self._change_rotation)
        self.rotate_90 = QRadioButton("90°", self)
        self.rotate_90.clicked.connect(self._change_rotation)
        self.rotate_180 = QRadioButton("180°", self)
        self.rotate_180.clicked.connect(self._change_rotation)
        self.rotate_270 = QRadioButton("270°", self)
        self.rotate_270.clicked.connect(self._change_rotation)
        rotate_layout.addWidget(self.rotate_0)
        rotate_layout.addWidget(self.rotate_90)
        rotate_layout.addWidget(self.rotate_180)
        rotate_layout.addWidget(self.rotate_270)
        rotate_group.addButton(self.rotate_0)
        rotate_group.addButton(self.rotate_90)
        rotate_group.addButton(self.rotate_180)
        rotate_group.addButton(self.rotate_270)
        rotate_box.setLayout(rotate_layout)
        complete_box.addWidget(rotate_box)
    
        return complete_box

    def _change_rotation(self):
        
        print("Hallo Welt!")
        if self._get_rotation() != self.current_page.additional_rotation_angle:
            self.current_page.additional_rotation_angle = self._get_rotation()
            self.show_page()

    def _get_rotation(self):

        if self.rotate_0.isChecked():
            return 0
        if self.rotate_90.isChecked():
            return 90
        if self.rotate_180.isChecked():
            return 180
        if self.rotate_270.isChecked():
            return 270

    def _set_rotation(self, angle):

        if angle == 0:
            self.rotate_0.setChecked(True)
            return
        if angle == 90:
            self.rotate_90.setChecked(True)
            return
        if angle == 180:
            self.rotate_180.setChecked(True)
            return
        if angle == 270:
            self.rotate_270.setChecked(True)
        return
    
    def _get_region_params_layout(self):

        region_params = QVBoxLayout()
        self.region_algo_select = self._get_algorithm_combobox()
        self.region_algo_select.currentIndexChanged.connect(self._region_algo_changed)
        region_params.addWidget(self.region_algo_select)
        return region_params
    
    def _get_algorithm_combobox(self):
        
        algo_select = QComboBox()
        for algo, algo_text in ALGORITHM_TEXTS.items():
            algo_select.addItem(algo_text)
        return algo_select
        
    def _main_algo_changed(self):
        
        if self.current_page_no is None:
            return
        combo_box = self.sender()
        for value, text in ALGORITHM_TEXTS.items():
            if combo_box.currentText() == text:
                self.project.pages[self.current_page_no-1].main_region.mode_algorithm = value

    def _region_algo_changed(self):
        
        if self.current_page_no is None:
            return
        if self.current_region_no is None:
            return
        combo_box = self.sender()
        for value, text in ALGORITHM_TEXTS.items():
            if combo_box.currentText() == text:
                self.project.pages[self.current_page_no-1].sub_regions[self.current_region_no-1].mode_algorithm = value

    def _get_right_panel(self):

        right_panel_layout = QVBoxLayout()
        page_view_buttons_layout = QHBoxLayout()
        self.new_region_button = QPushButton(text="Region anlegen")
        self.new_region_button.clicked.connect(self.create_save_region)
        self.delete_region_button = QPushButton(text="Region löschen")
        self.delete_region_button.clicked.connect(self.delete_cancel_region)
        page_view_buttons_layout.addWidget(self.new_region_button)
        page_view_buttons_layout.addWidget(self.delete_region_button)
        right_panel_layout.addLayout(page_view_buttons_layout)
        self.graphics_view = PageView()
        right_panel_layout.addWidget(self.graphics_view)
        return right_panel_layout
        
    def _create_menu_bar(self):
                
        new_project_action = QAction(QIcon('start.png'), '&Neues Projekt', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.setStatusTip('Neues Projekt')
        new_project_action.triggered.connect(self._start_new_project)

        exit_action = QAction(QIcon('exit.png'), '&Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Programm beenden')
        exit_action.triggered.connect(QApplication.quit)

        save_action = QAction(QIcon('save.png'), '&Speichern', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Project speichern')
        save_action.triggered.connect(self._save_project)

        load_action = QAction(QIcon('load.png'), '&Laden', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Projekt laden')
        load_action.triggered.connect(self._load_project)

        pdf_export_action = QAction(QIcon('file.png'), '&Pdf exportieren', self)
        pdf_export_action.setShortcut('Ctrl+P')
        pdf_export_action.setStatusTip('Das Projekt als pdf-Datei exportieren')
        pdf_export_action.triggered.connect(self._export_pdf)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(new_project_action)
        fileMenu.addAction(save_action)
        fileMenu.addAction(load_action)
        fileMenu.addAction(exit_action)
        exportMenu = menubar.addMenu("&Export")
        exportMenu.addAction(pdf_export_action)
    
    def _show_current_page(self):
        
        self.previewer.show(self.project.pages[self.current_page_no-1])
        
    def _save_project(self):
        
        file_selection = QFileDialog.getSaveFileName(parent=self,
                                                caption="ScanConvert2-Datei für das Speichern angeben",
                                                filter="ScanConvert2-Dateien (*.scp)")
        new_file_name = file_selection[0]
        if new_file_name == "":
            return
        
        if new_file_name[-4:] != '.scp':
            new_file_name += ".scp"
        file = open(new_file_name, "wb")
        pickle.dump(self.project, file)
        file.close()
    
    def _load_project(self):
        
        file_selection = QFileDialog.getOpenFileName(parent=self,
                                                caption="ScanConvert2-Datei für das Laden auswählen",
                                                filter="ScanConvert2-Dateien (*.scp)")
        if file_selection[0] != "":
            file = open(file_selection[0], "rb")
            project = pickle.load(file)
            file.close()
            self._init_from_project(project)
        
    def _export_pdf(self):
        
        file_base = QFileDialog.getSaveFileName(parent=self,
                                                caption="Pdf-Datei für das Speichern angeben",
                                                filter="Pdf-Dateien (*.pdf)")

        if file_base[0] != "":
            job = JobDefinition(self.project, file_base[0], ExportTarget.PDF_EXPORT)
            self.task_manager.add_task(job)
            
    def show_job_status(self):
        
        total = len(self.task_manager.finished_tasks) + len(self.task_manager.unfinished_tasks)
        unfinished = len(self.task_manager.unfinished_tasks)
        self.task_label.setText("<b>Status:</b><br/>Unvollendete Aufgaben: %d<br/>Aufgaben ingesamt: %d" % (unfinished, total))
                    
    def _get_page_scroller(self):
        
        page_scroller = QHBoxLayout()
        previous_button = QPushButton("Zurück")
        previous_button.clicked.connect(self.previous_page)
        self.page_number_label = QLabel("0/0")
        self.page_number_label.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
        self.page_number_label.setFixedWidth(65)
        next_button = QPushButton("Vor")
        next_button.clicked.connect(self.next_page)
        page_scroller.addWidget(previous_button)
        page_scroller.addWidget(self.page_number_label)
        page_scroller.addWidget(next_button)
        return page_scroller

    def _get_region_scroller(self):
        
        region_scroller = QHBoxLayout()
        previous_button = QPushButton("Zurück")
        previous_button.clicked.connect(self.previous_region)
        self.region_number_label = QLabel("0/0")
        self.region_number_label.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
        self.region_number_label.setFixedWidth(65)
        next_button = QPushButton("Vor")
        next_button.clicked.connect(self.next_region)
        region_scroller.addWidget(previous_button)
        region_scroller.addWidget(self.region_number_label)
        region_scroller.addWidget(next_button)
        return region_scroller
        
    def previous_page(self):
        
        if self.no_of_pages == 0:
            return
        
        self.current_page_no -= 1
        if self.current_page_no == 0:
            self.current_page_no = self.no_of_pages
        self.show_page()
    
    def next_page(self):

        if self.no_of_pages == 0:
            return
        
        self.current_page_no += 1
        if self.current_page_no == self.no_of_pages + 1:
            self.current_page_no = 1
        
        self.show_page()
        
    def next_region(self):

        if self.no_of_regions == 0:
            return
        
        self.current_region_no += 1
        if self.current_region_no == self.no_of_regions + 1:
            self.current_region_no = 1

        self.show_region()

    def previous_region(self):

        if self.no_of_regions == 0:
            return
        
        self.current_region_no -= 1
        if self.current_region_no == 0:
            self.current_region_no = self.no_of_regions
        
        self.show_region()    

    def create_save_region(self):
        
        if self.new_region_button.text() == CREATE_REGION:
            self.new_region_button.setText(APPLY_REGION)
            self.delete_region_button.setText(CANCEL_REGION)
            self.create_region()
        else:
            self.new_region_button.setText(CREATE_REGION)
            self.delete_region_button.setText(DELETE_REGION)
            self.apply_region()

            
    def create_region(self):
        """
        Reset selection an wait for selection
        """
        self.graphics_view.region_select = True
        self.graphics_view.reset_rubberband()
    
    
    def apply_region(self):
        """
        Selection is finished and we add the selected region to the
        sub regions of the page
        """
        self.graphics_view.region_select = False

        new_region = self.graphics_view.get_selected_region()
        new_region.mode_algorithm = self.project.pages[self.current_page_no-1].main_algorithm
        self.project.pages[self.current_page_no-1].sub_regions.append(new_region)
        # TODO: Check if something is selected at all
        self.no_of_regions = len(self.project.pages[self.current_page_no-1].sub_regions)
        self.current_region_no = self.no_of_regions
        self.show_region()
    
    def delete_cancel_region(self):
        
        if self.delete_region_button.text() == DELETE_REGION:
            self.delete_region()
        else:
            self.delete_region_button.setText(DELETE_REGION)
            self.new_region_button.setText(CREATE_REGION)
            self.cancel_region()
    
    def delete_region(self):
        
        if self.current_region_no == 0:
            return
        del(self.project.pages[self.current_page_no-1].sub_regions[self.current_region_no-1])
        self.reset_region()
        
    def reset_region(self):

        self.no_of_regions = len(self.project.pages[self.current_page_no-1].sub_regions)
        if self.no_of_regions == 0:
            self.current_region_no = 0
        else:
            self.current_region_no = 1
            
        self.show_region()
    
    def cancel_region(self):
        
        self.show_region()
        self.graphics_view.region_select = False
        
    def show_region(self):

        self.region_number_label.setText("%d/%d" % (self.current_region_no, self.no_of_regions))
        self.graphics_view.reset_rubberband()
        if self.no_of_regions > 0:
            self.graphics_view.show_region(self.project.pages[self.current_page_no-1].sub_regions[self.current_region_no-1])
            region = self.project.pages[self.current_page_no-1].sub_regions[self.current_region_no-1]
            self.region_algo_select.setEnabled(True)
            for idx in range(0, self.main_algo_select.count()):
                if self.region_algo_select.itemText(idx) == ALGORITHM_TEXTS[region.mode_algorithm]:
                    self.region_algo_select.setCurrentIndex(idx)
                    break
        else:
            self.region_algo_select.setEnabled(False)

    def show_page(self):

        self.page_number_label.setText("%d/%d" % (self.current_page_no, self.no_of_pages))
        self.skip_page_checkbox.setChecked(self.current_page.skip_page)
        if self.current_page.additional_rotation_angle != self._get_rotation():
            self._set_rotation(self.current_page.additional_rotation_angle)
        self.graphics_view.set_page(self.current_page.get_base_image())

        self.main_algo_select.setEnabled(True)
        for idx in range(0, self.main_algo_select.count()):
            if self.main_algo_select.itemText(idx) == ALGORITHM_TEXTS[self.current_page.main_region.mode_algorithm]:
                self.main_algo_select.setCurrentIndex(idx)
                break

        self.reset_region()
        
    def _start_new_project(self):
        
        wizard = ExpertProjectWizard()
        if wizard.exec():
            project = self.project_service.create_project(wizard.scans,
                                                          wizard.pages_per_scan,
                                                          wizard.sort_type,
                                                          wizard.scan_rotation,
                                                          wizard.rotation_alternating,
                                                          wizard.pdf_algorithm)
            project.metadata = wizard.metadata
            self._init_from_project(project)
        
    def _init_from_project(self, project: Project):
        
        self.project = project
        self.no_of_pages = len(self.project.pages)
        self.current_page_no = 0
        self.next_page()
        
    current_page = property(lambda self: self.project.pages[self.current_page_no-1])
        
            
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector()
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec())
