'''
Created on 06.11.2022

@author: michael
'''
import os
import shutil
import sys
import tempfile

from PIL import Image
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import \
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, \
    QMainWindow, \
    QWidget, QApplication, QComboBox, QFileDialog, QGroupBox, \
    QButtonGroup, QRadioButton, QCheckBox
from injector import inject, Injector, singleton

from Asb.ScanConvert2.Algorithms import Algorithm, AlgorithmModule
from Asb.ScanConvert2.GUI.Dialogs import MetadataDialog, PropertiesDialog, \
    DDFMetadataDialog
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
CROP_REGION = "Freistellen"
UNCROP_REGION = "Freistellung aufheben"
REGION_SELECT_MODE = True

Image.MAX_IMAGE_PIXELS = None 


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

class BaseWindow(QMainWindow):

    def __init__(self):
        
        super().__init__()

        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle("Scan-Kovertierer")
        self._create_widgets()
        
    def _create_widgets(self):

        self.statusBar().showMessage("Programm gestartet...")

        self._create_menu_bar()
        
        self.main_layout = QHBoxLayout()
        
        self.main_layout.addLayout(self._create_left_panel())
        self.main_layout.addLayout(self._create_right_panel())
        
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)

        self.setCentralWidget(central_widget)

    def _create_menu_bar(self):
                
        self.new_project_action = QAction(QIcon('start.png'), '&Neues Projekt', self)
        self.new_project_action.setShortcut('Ctrl+N')
        self.new_project_action.setStatusTip('Neues Projekt')

        self.exit_action = QAction(QIcon('exit.png'), '&Beenden', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Programm beenden')

        self.save_action = QAction(QIcon('save.png'), '&Speichern', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.setStatusTip('Project speichern')

        self.load_action = QAction(QIcon('load.png'), '&Laden', self)
        self.load_action.setShortcut('Ctrl+L')
        self.load_action.setStatusTip('Projekt laden')

        self.pdf_export_action = QAction(QIcon('file.png'), '&Pdf exportieren', self)
        self.pdf_export_action.setShortcut('Ctrl+P')
        self.pdf_export_action.setStatusTip('Das Projekt als pdf-Datei exportieren')

        self.ddf_export_action = QAction(QIcon('file.png'), '&DDF-Export', self)
        self.ddf_export_action.setShortcut('Ctrl+D')
        self.ddf_export_action.setStatusTip('Das Projekt als pdf-Datei exportieren')

        self.tif_export_action = QAction(QIcon('file.png'), '&Tiff-Archiv exportieren', self)
        self.tif_export_action.setShortcut('Ctrl+T')
        self.tif_export_action.setStatusTip('Das Projekt als Tiff-Archiv exportieren')

        self.edit_metadata_action = QAction(QIcon('file.png'), '&Metadaten', self)
        self.edit_metadata_action.setShortcut('Ctrl+M')
        self.edit_metadata_action.setStatusTip('Metadaten bearbeiten')

        self.edit_properties_action = QAction(QIcon('file.png'), '&Einstellungen', self)
        self.edit_properties_action.setShortcut('Ctrl+E')
        self.edit_properties_action.setStatusTip('Projekteinstellungen bearbeiten')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(self.new_project_action)
        fileMenu.addAction(self.save_action)
        fileMenu.addAction(self.load_action)
        fileMenu.addAction(self.exit_action)
        exportMenu = menubar.addMenu("&Export")
        exportMenu.addAction(self.pdf_export_action)
        exportMenu.addAction(self.tif_export_action)
        exportMenu.addAction(self.ddf_export_action)
        exportMenu.addAction(self.edit_metadata_action)
        exportMenu.addAction(self.edit_properties_action)
        
    def _create_left_panel(self):
        
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
        left_panel.addWidget(self.skip_page_checkbox)

        self.preview_button = QPushButton("Vorschau")
        left_panel.addWidget(self.preview_button)
            
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

    def _get_page_scroller(self):
        
        page_scroller = QHBoxLayout()
        self.previous_page_button = QPushButton("Zurück")
        self.page_number_label = QLabel("0/0")
        self.page_number_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.page_number_label.setFixedWidth(65)
        self.next_page_button = QPushButton("Vor")
        page_scroller.addWidget(self.previous_page_button)
        page_scroller.addWidget(self.page_number_label)
        page_scroller.addWidget(self.next_page_button)
        
        return page_scroller

    def _get_region_scroller(self):
        
        region_scroller = QHBoxLayout()
        self.previous_region_button = QPushButton("Zurück")
        self.region_number_label = QLabel("0/0")
        self.region_number_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.region_number_label.setFixedWidth(65)
        self.next_region_button = QPushButton("Vor")
        region_scroller.addWidget(self.previous_region_button)
        region_scroller.addWidget(self.region_number_label)
        region_scroller.addWidget(self.next_region_button)
        return region_scroller
    
    def _get_page_params_layout(self):
        
        page_params = QVBoxLayout()
        self.main_algo_select = self._get_algorithm_combobox()
        page_params.addWidget(self.main_algo_select)
        return page_params
    
    def _get_algorithm_combobox(self):
        
        algo_select = QComboBox()
        for algo in Algorithm:
            algo_select.addItem("%s" % algo)
        return algo_select
        
    def _get_rotate_box(self):
        
        complete_box = QVBoxLayout()
                    
        rotate_box = QGroupBox("Drehen")
        rotate_layout = QHBoxLayout()
        rotate_group = QButtonGroup(self)
        self.rotate_0 = QRadioButton("0°", self)
        self.rotate_0.setChecked(True)
        self.rotate_0.toggled.connect(self.cb_change_rotation)
        self.rotate_90 = QRadioButton("90°", self)
        self.rotate_90.clicked.connect(self.cb_change_rotation)
        self.rotate_180 = QRadioButton("180°", self)
        self.rotate_180.clicked.connect(self.cb_change_rotation)
        self.rotate_270 = QRadioButton("270°", self)
        self.rotate_270.clicked.connect(self.cb_change_rotation)
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

    def _get_region_params_layout(self):

        region_params = QVBoxLayout()
        self.region_algo_select = self._get_algorithm_combobox()
        region_params.addWidget(self.region_algo_select)
        return region_params
    
    def _create_right_panel(self):

        right_panel_layout = QVBoxLayout()
        page_view_buttons_layout = QHBoxLayout()
        self.new_region_button = QPushButton()
        self.delete_region_button = QPushButton()
        self.crop_region_button = QPushButton()
        page_view_buttons_layout.addWidget(self.new_region_button)
        page_view_buttons_layout.addWidget(self.delete_region_button)
        page_view_buttons_layout.addWidget(self.crop_region_button)
        right_panel_layout.addLayout(page_view_buttons_layout)
        self.graphics_view = PageView()
        right_panel_layout.addWidget(self.graphics_view)

        return right_panel_layout

    def show_page_counter(self, page_no: int, number_of_pages: int):
        
        self.page_number_label.setText("%d/%d" % (page_no, number_of_pages))
    
    def show_region_counter(self, region_no: int, number_of_regions: int):
        
        self.region_number_label.setText("%d/%d" % (region_no, number_of_regions))

    def set_enabled(self, status: bool, *widgets):
        
        for widget in widgets:
            widget.setEnabled(status)

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
    
    rotation = property(_get_rotation, _set_rotation)
    

    
@singleton
class Window(BaseWindow):

    @inject
    def __init__(self,
                 project_service: ProjectService,
                 task_manager: TaskManager,
                 previewer: FehPreviewer):

        super().__init__()
        
        self.project = None
        self.region_mode = not REGION_SELECT_MODE
        self.project_service = project_service
        self.task_manager = task_manager
        self.task_manager.message_function = self.show_job_status
        self.previewer = previewer
        self.metadata_dialog = MetadataDialog(self)
        self.ddf_metadata_dialog = DDFMetadataDialog(self)
        self.properties_dialog = PropertiesDialog(self)
        
        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle("Scan-Kovertierer")
        self._attach_callbacks()
        
        self.task_manager.message_function()
        
        self.update_gui()
        
    def _attach_callbacks(self):
        
        # Menu bar        
        self.new_project_action.triggered.connect(self.cb_new_project)
        self.exit_action.triggered.connect(QApplication.quit)
        self.save_action.triggered.connect(self.cb_save_project)
        self.load_action.triggered.connect(self.cb_load_project)
        self.pdf_export_action.triggered.connect(self.cb_export_pdf)
        self.ddf_export_action.triggered.connect(self.cb_export_ddf)
        self.tif_export_action.triggered.connect(self.cb_export_tif)
        self.edit_metadata_action.triggered.connect(self.cb_edit_metadata)
        self.edit_properties_action.triggered.connect(self.cb_edit_properties)

        # Left panel main
        self.skip_page_checkbox.clicked.connect(self.cb_toggle_skip_page)
        self.preview_button.clicked.connect(self.cb_preview_current_page)
            
        # Left panel, page scroller
        self.previous_page_button.clicked.connect(self.cb_set_previous_as_current_page)
        self.next_page_button.clicked.connect(self.cb_set_next_as_current_page)

        # Left panel, page parameters
        self.main_algo_select.currentIndexChanged.connect(self.cb_main_algo_changed)

        # Left panel, rotation box
        self.rotate_0.toggled.connect(self.cb_change_rotation)
        self.rotate_90.clicked.connect(self.cb_change_rotation)
        self.rotate_180.clicked.connect(self.cb_change_rotation)
        self.rotate_270.clicked.connect(self.cb_change_rotation)

        # Left panel, region scroller
        self.previous_region_button.clicked.connect(self.cb_set_previous_as_current_region)
        self.next_region_button.clicked.connect(self.cb_set_next_as_current_region)
        

        # Left panel, region parameters
        self.region_algo_select.currentIndexChanged.connect(self.cb_region_algo_changed)

        # Right panel
        self.new_region_button.clicked.connect(self.cb_create_save_region)
        self.delete_region_button.clicked.connect(self.cb_delete_cancel_region)
        self.crop_region_button.clicked.connect(self.cb_crop_uncrop_region)

    def cb_new_project(self):
        
        wizard = ProjectWizard()
        if wizard.exec():
            project = self.project_service.create_project(wizard.scans,
                                                          wizard.pages_per_scan,
                                                          wizard.sort_type,
                                                          wizard.scan_rotation,
                                                          wizard.rotation_alternating,
                                                          wizard.cropping)
            project.metadata = MetaData()
            project.metadata.subject = "Alle Rechte an diesem Digitalisat liegen beim\nArchiv Soziale Bewegungen e.V., Freiburg"

            self._init_from_project(project)
            
            self.update_gui()
    
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
        
        self.update_gui()
        
    def _init_from_project(self, project: Project):
        
        self.project = project
        self.project.first_page()

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
            
    def cb_export_ddf(self):
        
        self.cb_edit_ddf_metadata()
        
        file_name = QFileDialog.getSaveFileName(parent=self,
                                                dir=self.project.proposed_zip_file,
                                                caption="Zip-Datei für das Speichern angeben",
                                                filter="Zip-Dateien (*.zip)")

        if file_name[0] != "":
            job = JobDefinition(
                self,
                lambda: self.project_service.export_ddf(self.project, file_name[0])
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
    
    def cb_edit_metadata(self):
        
        self.metadata_dialog.metadata = self.project.metadata
        if self.metadata_dialog.exec():
            self.project.metadata = self.metadata_dialog.metadata

    def cb_edit_ddf_metadata(self):
        
        self.ddf_metadata_dialog.metadata = self.project.metadata
        if self.ddf_metadata_dialog.exec():
            self.project.metadata = self.ddf_metadata_dialog.metadata
    
    def cb_edit_properties(self):
        
        if self.project is None:
            return
        
        self.properties_dialog.project_properties = self.project.project_properties
        if self.properties_dialog.exec():
            self.project.project_properties = self.properties_dialog.project_properties

    def cb_toggle_skip_page(self):
        
        if self.project is None:
            return
        self.current_page.skip_page = self.skip_page_checkbox.isChecked()

    def cb_preview_current_page(self):
        
        try:
            self.previewer.show(self.project.current_page, self.project.project_properties.pdf_resolution)
        except NoPagesInProjectException:
            pass
        
    def cb_set_previous_as_current_page(self):
        
        try:
            self.project.previous_page()
        except NoPagesInProjectException:
            return

        self.update_gui()
    
    def cb_set_next_as_current_page(self):

        try:
            self.project.next_page()
        except NoPagesInProjectException:
            return
        
        self.update_gui()
                
    def cb_main_algo_changed(self):
        
        try:
            current_page = self.current_page
        except NoPagesInProjectException:
            return
        combo_box = self.sender()
        for algo in Algorithm:
            if combo_box.currentText() == "%s" % algo:
                current_page.main_region.mode_algorithm = algo

    def cb_change_rotation(self):
        
        if self.rotation != self.current_page.additional_rotation_angle:
            self.current_page.additional_rotation_angle = self.rotation
            self.update_gui()

    def cb_set_next_as_current_region(self):

        try:
            self.current_page.set_next_as_current_region()
        except NoPagesInProjectException:
            return
        except NoRegionsOnPageException:
            return

        self.show_region()

    def cb_set_previous_as_current_region(self):

        try:
            self.current_page.set_previous_as_current_region()
        except NoPagesInProjectException:
            return
        except NoRegionsOnPageException:
            return

        self.show_region()
        
    def cb_region_algo_changed(self):
        
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
    
    def cb_create_save_region(self):
        
        if self.region_mode == REGION_SELECT_MODE:
            self._apply_region()
        else:
            self.graphics_view.region_select = True
        
        self.region_mode = not self.region_mode

        self.update_gui()
        
        if self.region_mode == REGION_SELECT_MODE:
            self.graphics_view.reset_rubberband()
            
    def _apply_region(self):
        """
        Selection is finished and we add the selected region to the
        sub regions of the page
        """

        new_region = self.graphics_view.get_selected_region()
        new_region.mode_algorithm = self.current_page.main_algorithm
        self.current_page.sub_regions.append(new_region)
        # TODO: Check if something is selected at all
        self.current_page.set_last_as_current_region()
    
    def cb_delete_cancel_region(self):
        
        if self.region_mode != REGION_SELECT_MODE:
            self._delete_region()
            try:
                self.current_page.set_first_as_current_region()
            except NoRegionsOnPageException:
                pass
        else:
            self.region_mode = not REGION_SELECT_MODE
            try:
                self.current_page.set_last_as_current_region()
            except NoRegionsOnPageException:
                pass
        
        self.update_gui()
        
    def _delete_region(self):
        
        del(self.current_page.sub_regions[self.current_page.current_sub_region_no - 1])
        self.current_page.current_sub_region_no -= 1
        
    def cb_crop_uncrop_region(self):
    
        if self.region_mode == REGION_SELECT_MODE:
            self._crop_region()
        else:
            self._uncrop_region()
        
        self.region_mode = not REGION_SELECT_MODE
        
        self.update_gui()
        
    def _crop_region(self):
        
        self.graphics_view.get_selected_region()
        self.current_page.crop_page(self.graphics_view.get_selected_region())
        self.graphics_view.reset_rubberband()
        
    def _uncrop_region(self):
        
        self.current_page.uncrop_page()
        
    def show_job_status(self):
        
        total = len(self.task_manager.finished_tasks) + len(self.task_manager.unfinished_tasks)
        unfinished = len(self.task_manager.unfinished_tasks)
        self.task_label.setText("<b>Status:</b><br/>Unvollendete Aufgaben: %d<br/>Aufgaben ingesamt: %d" % (unfinished, total))
        
    def reset_region(self):
        
        self.current_page.reset_region()
        self.graphics_view.reset_rubberband()
    
    def show_region(self):

        self.graphics_view.reset_rubberband()
        try:
            region = self.current_page.current_sub_region
        except NoRegionsOnPageException:
            return

        self.show_region_counter(self.current_page.current_sub_region_no,
                                 self.current_page.no_of_sub_regions)
        
        for idx in range(0, self.main_algo_select.count()):
            if self.region_algo_select.itemText(idx) == "%s" % region.mode_algorithm:
                self.region_algo_select.setCurrentIndex(idx)
                break
            
        self.graphics_view.show_region(region)
        
    def show_page(self):
        
        self.skip_page_checkbox.setChecked(self.current_page.skip_page)
        
        if self.current_page.additional_rotation_angle != self._get_rotation():
            self._set_rotation(self.current_page.additional_rotation_angle)
        
        self.graphics_view.set_page(self.current_page.get_raw_image())

        for idx in range(0, self.main_algo_select.count()):
            if self.main_algo_select.itemText(idx) == "%s" % self.current_page.main_region.mode_algorithm:
                self.main_algo_select.setCurrentIndex(idx)
                break

    def update_gui(self):

        if self.project is None:
                self.set_widget_state_no_project()
        else:
                self.set_widget_state_with_project()
                self.graphics_view.region_select = self.region_mode
        
        self.show_job_status()

    def set_widget_state_no_project(self):
        
        self.set_enabled(False,
                        self.save_action, self.pdf_export_action,
                        self.ddf_export_action, self.tif_export_action,
                        self.edit_metadata_action, self.edit_properties_action,
                        self.skip_page_checkbox, self.preview_button,
                        self.previous_page_button, self.next_page_button,
                        self.main_algo_select, self.rotate_0, self.rotate_90,
                        self.rotate_180, self.rotate_270, self.previous_region_button,
                        self.next_region_button, self.region_algo_select,
                        self.new_region_button, self.delete_region_button,
                        self.crop_region_button
                        )
        self.set_enabled(True,
                        self.new_project_action, self.exit_action,
                        self.load_action)
        
        self.set_label_texts()
        
    def set_label_texts(self):
        
        if self.project is None or len(self.project.pages) == 0:
            self.show_page_counter(0, 0)
            self.show_region_counter(0, 0)
        else:
            try:
                self.show_page_counter(self.project.current_page_no, len(self.project.pages))
            except NoPagesInProjectException:
                self.show_page_counter(0, 0)
            try:
                self.show_region_counter(self.current_page.current_sub_region_no,
                                         len(self.current_page.sub_regions))
            except NoRegionsOnPageException:
                self.show_region_counter(0, 0)
            
        if self.region_mode == REGION_SELECT_MODE:
            self.new_region_button.setText("Region übernehmen")
            self.delete_region_button.setText("Abbrechen")
            self.crop_region_button.setText("Freistellen")
        else:
            self.new_region_button.setText("Region anlegen")
            self.delete_region_button.setText("Region löschen")
            self.crop_region_button.setText("Freistellung aufheben")
            
    def set_widget_state_with_project(self):
        
        self.set_label_texts()
        self.show_page()
        self.show_region()
        
        if self.region_mode == REGION_SELECT_MODE:
            self.set_widget_state_region_select()
        else:
            self.set_widget_state_no_region_select()
        
        
    def set_widget_state_region_select(self):
        
        self.set_enabled(False,
                        self.save_action, self.pdf_export_action,
                        self.ddf_export_action, self.tif_export_action,
                        self.edit_metadata_action, self.edit_properties_action,
                        self.skip_page_checkbox, self.preview_button,
                        self.previous_page_button, self.next_page_button,
                        self.main_algo_select, self.rotate_0, self.rotate_90,
                        self.rotate_180, self.rotate_270, self.previous_region_button,
                        self.next_region_button, self.region_algo_select,
                        self.new_project_action,
                        self.exit_action, self.load_action

                        )
        self.set_enabled(True,
                        self.new_region_button, self.delete_region_button, self.crop_region_button
                        )
        
        
    def set_widget_state_no_region_select(self):
        
        self.set_enabled(True,
                        self.save_action, self.pdf_export_action,
                        self.ddf_export_action, self.tif_export_action,
                        self.edit_metadata_action, self.edit_properties_action,
                        self.skip_page_checkbox, self.preview_button,
                        self.main_algo_select, self.rotate_0, self.rotate_90,
                        self.rotate_180, self.rotate_270, 
                        self.new_project_action,
                        self.exit_action, self.load_action,
                        self.new_region_button,
                        )
        self.set_enabled(False,
                        self.previous_page_button, self.next_page_button,
                        self.crop_region_button, self.previous_region_button,
                        self.next_region_button, self.region_algo_select,
                        self.delete_region_button
                        )
        if len(self.project.pages) > 0:
            if len(self.current_page.sub_regions) > 0:
                self.set_enabled(True,
                                self.region_algo_select,
                                self.delete_region_button)
            if len(self.current_page.sub_regions) > 1:
                self.set_enabled(True,
                                self.previous_region_button,
                                self.next_region_button)
            if self.current_page.is_cropped():
                self.set_enabled(True, self.crop_region_button)
            if len(self.project.pages) > 1:
                self.set_enabled(True, self.next_page_button, self.previous_page_button)

    current_page = property(lambda self: self.project.current_page)
        
            
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector(AlgorithmModule)
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec())
