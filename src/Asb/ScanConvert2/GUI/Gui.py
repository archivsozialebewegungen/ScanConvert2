'''
Created on 06.11.2022

@author: michael
'''
import os
import shutil
import sys
import tempfile

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import \
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, \
    QMainWindow, \
    QWidget, QApplication, QComboBox, QFileDialog, QGroupBox, \
    QButtonGroup, QRadioButton, QCheckBox
from injector import inject, Injector, singleton
from networkx.algorithms.bipartite.projection import project

from Asb.ScanConvert2.Algorithms import Algorithm, AlgorithmModule
from Asb.ScanConvert2.GUI.Dialogs import MetadataDialog, PropertiesDialog
from Asb.ScanConvert2.GUI.PageView import PageView
from Asb.ScanConvert2.GUI.ProjectWizard import ProjectWizard
from Asb.ScanConvert2.GUI.TaskRunner import TaskManager, JobDefinition
from Asb.ScanConvert2.PictureDetector import PictureDetector
from Asb.ScanConvert2.ScanConvertDomain import Project, \
    Region, Page, NoPagesInProjectException, \
    NoRegionsOnPageException, MetaData
from Asb.ScanConvert2.ScanConvertServices import ProjectService, \
    FinishingService


CREATE_REGION = "Region anlegen"
APPLY_REGION = "Auswahl übernehmen"
DELETE_REGION = "Region löschen"
CANCEL_REGION = "Auswahl abbrechen"

@singleton
class FehPreviewer(object):
    
    @inject
    def __init__(self, finishing_service: FinishingService):
        
        self.feh = shutil.which("feh")
        self.finishing_service = finishing_service
        
    def show(self, page: Page, resolution: int):
        
        img, bg_color = self.finishing_service.create_final_image(page, [], resolution)
        tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".png")
        img.save(tmp_file, format="png")
        os.system("%s %s" % (self.feh, tmp_file.name))
        tmp_file.close()

    def is_working(self):
        
        return self.feh is not None

class PhotoDetectionThread(QThread):
    
    def __init__(self, parent, photo_detector: PictureDetector, project: Project):
        
        super().__init__(parent)

        self.photo_detector = photo_detector
        self.project = project
        
    def run(self):
        
        current_page = self.project.current_page
        photo_bboxes = self.photo_detector.find_photos(current_page.get_raw_image(self.project.project_properties.pdf_resolution))
        if len(photo_bboxes) == 0:
            return
        
        for bbox in photo_bboxes:
            current_page.add_region(Region(bbox[0], bbox[1],
                                           bbox[2] - bbox[0], bbox[3] - bbox[1],
                                           Algorithm.FLOYD_STEINBERG))
        current_page.current_sub_region_no = current_page.no_of_sub_regions
        
        
@singleton
class Window(QMainWindow):
    

    @inject
    def __init__(self,
                 project_service: ProjectService,
                 task_manager: TaskManager,
                 previewer: FehPreviewer):

        super().__init__()
        
        self.project_service = project_service
        self.task_manager = task_manager
        self.task_manager.message_function = self.show_job_status
        self.previewer = previewer
        self.metadata_dialog = MetadataDialog(self)
        self.properties_dialog = PropertiesDialog(self)
        
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
            preview_button.clicked.connect(self.cb_preview_current_page)
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
        
        if self.project is None:
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
        for algo in Algorithm:
            algo_select.addItem("%s" % algo)
        return algo_select
        
    def _main_algo_changed(self):
        
        try:
            current_page = self.current_page
        except NoPagesInProjectException:
            return
        combo_box = self.sender()
        for algo in Algorithm:
            if combo_box.currentText() == "%s" % algo:
                current_page.main_region.mode_algorithm = algo

    def _region_algo_changed(self):
        
        try:
            region = self.current_page.current_sub_region
        except NoPagesInProjectException:
            return
        except NoRegionsOnPageException:
            return
            
        combo_box = self.sender()
        for algo in Algorithm:
            if combo_box.currentText() == "%s" % algo:
                region.mode_algorithm = algo

    def _get_right_panel(self):

        right_panel_layout = QVBoxLayout()
        page_view_buttons_layout = QHBoxLayout()
        self.new_region_button = QPushButton(text="Region anlegen")
        self.new_region_button.clicked.connect(self.create_save_region)
        self.delete_region_button = QPushButton(text="Region löschen")
        self.delete_region_button.clicked.connect(self.delete_cancel_region)
        #self.mark_photos_button = QPushButton(text="Photos markieren")
        #self.mark_photos_button.clicked.connect(self.mark_photos)
        page_view_buttons_layout.addWidget(self.new_region_button)
        page_view_buttons_layout.addWidget(self.delete_region_button)
        #page_view_buttons_layout.addWidget(self.mark_photos_button)
        right_panel_layout.addLayout(page_view_buttons_layout)
        self.graphics_view = PageView()
        right_panel_layout.addWidget(self.graphics_view)
        return right_panel_layout
        
    def _create_menu_bar(self):
                
        new_project_action = QAction(QIcon('start.png'), '&Neues Projekt', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.setStatusTip('Neues Projekt')
        new_project_action.triggered.connect(self.cb_new_project)

        exit_action = QAction(QIcon('exit.png'), '&Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Programm beenden')
        exit_action.triggered.connect(QApplication.quit)

        save_action = QAction(QIcon('save.png'), '&Speichern', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Project speichern')
        save_action.triggered.connect(self.cb_save_project)

        load_action = QAction(QIcon('load.png'), '&Laden', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Projekt laden')
        load_action.triggered.connect(self.cb_load_project)

        pdf_export_action = QAction(QIcon('file.png'), '&Pdf exportieren', self)
        pdf_export_action.setShortcut('Ctrl+P')
        pdf_export_action.setStatusTip('Das Projekt als pdf-Datei exportieren')
        pdf_export_action.triggered.connect(self.cb_export_pdf)

        auto_pdf_export_action = QAction('&Automatischer Pdf Export', self)
        auto_pdf_export_action.setShortcut('Ctrl+A')
        auto_pdf_export_action.setStatusTip('Das Projekt mit eigener Segmentierung als pdf-Datei exportieren')
        auto_pdf_export_action.triggered.connect(self.cb_auto_export_pdf)

        tif_export_action = QAction(QIcon('file.png'), '&Tiff-Archiv exportieren', self)
        tif_export_action.setShortcut('Ctrl+T')
        tif_export_action.setStatusTip('Das Projekt als Tiff-Archiv exportieren')
        tif_export_action.triggered.connect(self.cb_export_tif)

        edit_metadata_action = QAction(QIcon('file.png'), '&Metadaten', self)
        edit_metadata_action.setShortcut('Ctrl+M')
        edit_metadata_action.setStatusTip('Metadaten bearbeiten')
        edit_metadata_action.triggered.connect(self.cb_edit_metadata)

        edit_properties_action = QAction(QIcon('file.png'), '&Einstellungen', self)
        edit_properties_action.setShortcut('Ctrl+E')
        edit_properties_action.setStatusTip('Projekteinstellungen bearbeiten')
        edit_properties_action.triggered.connect(self.cb_edit_properties)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(new_project_action)
        fileMenu.addAction(save_action)
        fileMenu.addAction(load_action)
        fileMenu.addAction(exit_action)
        exportMenu = menubar.addMenu("&Export")
        exportMenu.addAction(pdf_export_action)
        exportMenu.addAction(auto_pdf_export_action)
        exportMenu.addAction(tif_export_action)
        exportMenu.addAction(edit_metadata_action)
        exportMenu.addAction(edit_properties_action)
    
    def cb_edit_metadata(self):
        
        self.metadata_dialog.metadata = self.project.metadata
        if self.metadata_dialog.exec():
            self.project.metadata = self.metadata_dialog.metadata
    
    def cb_edit_properties(self):
        
        if self.project is None:
            return
        
        self.properties_dialog.project_properties = self.project.project_properties
        if self.properties_dialog.exec():
            self.project.project_properties = self.properties_dialog.project_properties
            
    def cb_detect_photos(self):
        
        if self.project is None:
            return
        counter = 0
        for page in self.project.pages:
            counter += 1
            print("Seite %d" % counter)
            self.run_photo_detection(page)
            

    def cb_preview_current_page(self):
        
        try:
            self.previewer.show(self.project.current_page, self.project.project_properties.pdf_resolution)
        except NoPagesInProjectException:
            pass
        
    def cb_save_project(self):
        
        file_selection = QFileDialog.getSaveFileName(parent=self,
                                                caption="ScanConvert2-Datei für das Speichern angeben",
                                                filter="ScanConvert2-Dateien (*.scp)")
        new_file_name = file_selection[0]
        if new_file_name == "":
            return
        
        self.project_service.save_project(new_file_name, self.project)
    
    def cb_load_project(self):
        
        file_selection = QFileDialog.getOpenFileName(parent=self,
                                                caption="ScanConvert2-Datei für das Laden auswählen",
                                                filter="ScanConvert2-Dateien (*.scp)")
        if file_selection[0] == "":
            return
        
        project = self.project_service.load_project(file_selection[0])
        self._init_from_project(project)
        
    def cb_export_pdf(self):
        
        if not self.project.metadata.reviewed:
            self.cb_edit_metadata()
        
        file_name = QFileDialog.getSaveFileName(parent=self,
                                                dir=self.project.proposed_pdf_file,
                                                caption="Pdf-Datei für das Speichern angeben",
                                                filter="Pdf-Dateien (*.pdf)")

        if file_name[0] != "":
            job = JobDefinition(
                self,
                lambda: self.project_service.export_pdf(self.project, file_name[0])
            )
            self.task_manager.add_task(job)
            
    def cb_auto_export_pdf(self):
        
        if not self.project.metadata.reviewed:
            self.cb_edit_metadata()
        
        file_name = QFileDialog.getSaveFileName(parent=self,
                                                dir=self.project.proposed_pdf_file,
                                                caption="Pdf-Datei für das Speichern angeben",
                                                filter="Pdf-Dateien (*.pdf)")

        if file_name[0] != "":
            job = JobDefinition(
                self,
                lambda: self.project_service.auto_export_pdf(self.project, file_name[0])
            )
            self.task_manager.add_task(job)
            
    def cb_export_tif(self):
        
        if not self.project.metadata.reviewed:
            self.cb_edit_metadata()
        

        
        file_name = QFileDialog.getSaveFileName(parent=self,
                                                dir=self.project.proposed_zip_file,
                                                caption="Zip-Datei für das Speichern angeben",
                                                filter="Zip-Dateien (*.zip)")

        if file_name[0] != "":
            job = JobDefinition(
                self,
                lambda: self.project_service.export_tif(self.project, file_name[0])
            )
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
        
        try:
            self.project.previous_page()
        except NoPagesInProjectException:
            return

        self.show_page()
    
    def next_page(self):

        try:
            self.project.next_page()
        except NoPagesInProjectException:
            return

        self.show_page()
        
    def next_region(self):

        try:
            self.current_page.next_region()
        except NoPagesInProjectException:
            return
        except NoRegionsOnPageException:
            return

        self.show_region()

    def previous_region(self):

        try:
            self.current_page.previous_region()
        except NoPagesInProjectException:
            return
        except NoRegionsOnPageException:
            return

        self.show_region()    

    def create_save_region(self):
        
        if self.new_region_button.text() == CREATE_REGION:
            self.new_region_button.setText(APPLY_REGION)
            self.delete_region_button.setText(CANCEL_REGION)
            self.create_region()
        else:
            self.new_region_button.setText(CREATE_REGION)
            self.delete_region_button.setText(DELETE_REGION)
            self._apply_region()

            
    def create_region(self):
        """
        Reset selection an wait for selection
        """
        self.graphics_view.region_select = True
        self.graphics_view.reset_rubberband()
    
    
    def _apply_region(self):
        """
        Selection is finished and we add the selected region to the
        sub regions of the page
        """
        self.graphics_view.region_select = False

        new_region = self.graphics_view.get_selected_region()
        new_region.mode_algorithm = self.current_page.main_algorithm
        self.current_page.sub_regions.append(new_region)
        # TODO: Check if something is selected at all
        self.current_page.last_region()
        self.show_region()
    
    def delete_cancel_region(self):
        
        if self.delete_region_button.text() == DELETE_REGION:
            self.delete_region()
        else:
            self.delete_region_button.setText(DELETE_REGION)
            self.new_region_button.setText(CREATE_REGION)
            self.cancel_region()
    
    def delete_region(self):
        
        del(self.current_page.sub_regions[self.current_page.current_sub_region_no-1])
        self.graphics_view.reset_rubberband()
        try:
            self.current_page.first_region()
        except NoRegionsOnPageException:
            pass
        self.show_region()
        
    def cancel_region(self):
        
        self.show_region()
        self.graphics_view.region_select = False

    def run_photo_detection(self, page: Page):

        regions = self.photo_detector.find_photos(page.get_raw_image())
        if len(regions) == 0:
            return
        
        for region in regions:
            region.mode_algorithm = Algorithm.FLOYD_STEINBERG
            page.add_region(region)
        if page == self.current_page:
            self.show_page()
    
    def mark_photos(self):
        
        job_definition = JobDefinition(
            self,
            lambda: self.run_photo_detection(self.current_page)
        )
        self.task_manager.add_task(job_definition)
        
    def reset_region(self):
        
        self.current_page.reset_region()
        self.graphics_view.reset_rubberband()
        
    def show_region(self):

        self.graphics_view.reset_rubberband()
        try:
            self.region_number_label.setText("%d/%d" % (self.current_page.current_sub_region_no, self.current_page.no_of_sub_regions))
        except NoRegionsOnPageException:
            self.region_number_label.setText("0/0")
            self.region_algo_select.setEnabled(False)
            return
        
        region = self.current_page.current_sub_region
        self.graphics_view.show_region(region)
        self.region_algo_select.setEnabled(True)
        for idx in range(0, self.main_algo_select.count()):
            if self.region_algo_select.itemText(idx) == "%s" % region.mode_algorithm:
                self.region_algo_select.setCurrentIndex(idx)
                break

    def show_page(self):

        try:
            self.page_number_label.setText("%d/%d" % (self.project.current_page_no, self.project.no_of_pages))
        except NoPagesInProjectException():
            self.page_number_label.setText("0/0")
            return
        
        self.skip_page_checkbox.setChecked(self.current_page.skip_page)
        if self.current_page.additional_rotation_angle != self._get_rotation():
            self._set_rotation(self.current_page.additional_rotation_angle)
        self.graphics_view.set_page(self.current_page.get_raw_image())

        self.main_algo_select.setEnabled(True)
        for idx in range(0, self.main_algo_select.count()):
            if self.main_algo_select.itemText(idx) == "%s" % self.current_page.main_region.mode_algorithm:
                self.main_algo_select.setCurrentIndex(idx)
                break

        try:
            self.current_page.first_region()
        except NoRegionsOnPageException:
            pass
        self.show_region()

    def cb_new_project(self):
        
        wizard = ProjectWizard()
        if wizard.exec():
            project = self.project_service.create_project(wizard.scans,
                                                          wizard.pages_per_scan,
                                                          wizard.sort_type,
                                                          wizard.scan_rotation,
                                                          wizard.rotation_alternating)
            project.metadata = MetaData()
            project.metadata.subject= "Alle Rechte an diesem Digitalisat liegen beim\nArchiv Soziale Bewegungen e.V., Freiburg"
            self._init_from_project(project)
        
    def _init_from_project(self, project: Project):
        
        self.project = project
        self.project.first_page()
        self.show_page()
        
    current_page = property(lambda self: self.project.current_page)

            
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector(AlgorithmModule)
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec())
