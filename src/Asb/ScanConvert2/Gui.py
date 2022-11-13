'''
Created on 06.11.2022

@author: michael
'''
import sys

from PyQt5.Qt import QMainWindow, QAction, QIcon, qApp, QWizard, QWizardPage,\
    QLabel, QRadioButton, QVBoxLayout, QPushButton, QHBoxLayout, QTableWidget,\
    QAbstractItemView, QFileDialog, QTableWidgetItem, QCheckBox
from PyQt5.QtWidgets import QApplication
from injector import inject, Injector, singleton

from Asb.ScanConvert2.PageGenerators import PageGeneratorsModule
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Asb.ScanConvert2.ScanConvertDomain import Projecttype, Scan, Project,\
    Scannertype, Scantype
import os

class ProjectWizard(QWizard):
    
    PROJECT_TYPE_PAGE = 0
    SCANNER_TYPE_PAGE = 1
    PAGE_PER_SCAN_PAGE = 2
    SCANS_PAGE = 3
    SCAN_ROTATION_PAGE = 4
        
    def __init__(self):
        
        super().__init__()
        self.pages = {
            self.PROJECT_TYPE_PAGE: ProjectWizardPageProjectType(self),
            self.SCANNER_TYPE_PAGE: ProjectWizardPageScannerType(self),
            self.PAGE_PER_SCAN_PAGE: ProjectWizardPagePagesPerScan(self),
            self.SCANS_PAGE: ProjectWizardPageScans(self),
            self.SCAN_ROTATION_PAGE: ProjectWizardPageRotation(self)
            }
        for page_id in self.pages.keys():
            self.setPage(page_id, self.pages[page_id])
             
        self.setWindowTitle("Neues Projekt anlegen")
        
    def _get_scan_type(self):
        
        if self.pages_per_scan == 1:
            return self._single_page_scan_type()
        else:
            return self._double_page_scan_type()
    
    def _single_page_scan_type(self):
        
        if self.scanner_type == Scannertype.OVERHEAD:
            # For Overhead-Scanner we assume no rotation
            return Scantype.SINGLE
    
    scan_type = property(_get_scan_type)
    scans = property(lambda self: self.pages[self.SCANS_PAGE].scans)
    scanner_type = property(lambda self: self.pages[self.SCANNER_TYPE_PAGE].scanner_type)
    pages_per_scan = property(lambda self: self.pages[self.PAGE_PER_SCAN_PAGE].pages_per_scan)
    project_type = property(lambda self: self.pages[self.PROJECT_TYPE_PAGE].project_type)
    scan_rotation = property(lambda self: self.pages[self.SCAN_ROTATION_PAGE].scan_rotation)
        
class ProjectWizardPageProjectType(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        self.wizard = parent
        self.project_type = None
        
        
        self.setTitle("Was soll für die Archivierung erzeugt werden?")
        self.setSubTitle("Pdf-Dateien sind für den normalen Gebrauch, TIFF-Dateien " +
                         "für die Langzeitarchivierung.")
        
        self.button_texts = {
            "Pdf-Erstellung (300 dpi, Schwarz-Weiß)": Projecttype.PDF,
            'TIFF-Datei-Erstellung für Langzeitarchivierung (400 dpi)': Projecttype.TIFF,
            'Pdf- und TIFF-Datei-Erstellung': Projecttype.BOTH
            }
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Bitte den Projekttyp auswählen:'))
        for button_text in self.button_texts.keys(): 
            radiobutton = QRadioButton(button_text)
            radiobutton.toggled.connect(self.on_click)
            if self.button_texts[button_text] == Projecttype.PDF:
                radiobutton.setChecked(True)
            layout.addWidget(radiobutton)

        self.setLayout(layout)
        
    def on_click(self):

        radiobutton = self.sender()
        self.project_type = self.button_texts[radiobutton.text()]        


class ProjectWizardPageScans(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        self.wizard = parent
        
        print(self.wizard)
        self.setTitle("Scans zum Projekt hinzufügen")
        self.setSubTitle("Die Scans müssen in der richtigen Reihenfolge angegeben werden. " +
            "Das ist je nach Scannertyp unterschiedlich (siehe Handbuch).")
        
        self.scans = []
        
        layout = QVBoxLayout()
        
        layout.addLayout(self._get_file_button_layout())
        layout.addWidget(self._get_filename_table_widget())
        
        self.setLayout(layout)

    def _get_file_button_layout(self):

        file_selection_button = QPushButton("Laden")
        file_up_button = QPushButton("Hoch")
        file_down_button = QPushButton("Runter")
        file_remove_button = QPushButton("Entfernen")
        file_selection_button.clicked.connect(self.add_files)
        file_up_button.clicked.connect(self.files_up)
        file_down_button.clicked.connect(self.files_down)
        file_remove_button.clicked.connect(self.remove_files)

        button_layout = QHBoxLayout()
        button_layout.addWidget(file_selection_button)
        button_layout.addWidget(file_up_button)
        button_layout.addWidget(file_down_button)
        button_layout.addWidget(file_remove_button)
        
        return button_layout

    def add_files(self):
        
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Graphikdateien (*.jpg *.tif *.tiff *.gif *.png)")
        
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            for filename in filenames:
                self.append_fileinfo(filename)

    def append_fileinfo(self, filename):
        
        self.scans.append(Scan(filename))
        self.filename_table.setRowCount(len(self.scans))
        self.display_line(len(self.scans) - 1)
        
    def display_line(self, index):
        
        self.filename_table.setItem(index, 0, QTableWidgetItem(os.path.basename(self.scans[index].filename)))
        
    def files_up(self):
        
        selected_rows = []
        selection_model = self.filename_table.selectionModel()
        for index in self.filename_table.selectionModel().selectedRows():
            if index.row() == 0:
                continue
            selected_rows.append(index.row() - 1)
            self.flip_lines(index.row(), index.row() - 1)

        selection_model.clearSelection()
        self.filename_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for row in selected_rows:
            self.filename_table.selectRow(row)
        self.filename_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def files_down(self):
        
        selected_rows = []
        selection_model = self.filename_table.selectionModel()
        indices = self.filename_table.selectionModel().selectedRows()

        # Must delete in reverse order
        for index in reversed(sorted(indices)):
            if index.row() == len(self.scans) - 1:
                continue
            selected_rows.append(index.row() + 1)
            self.flip_lines(index.row(), index.row() + 1)

        selection_model.clearSelection()
        self.filename_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for row in selected_rows:
            self.filename_table.selectRow(row)
        self.filename_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def remove_files(self):
        
        indices = self.filename_table.selectionModel().selectedRows()

        # Must delete in reverse order
        for each_row in reversed(sorted(indices)):
            self.filename_table.removeRow(each_row.row())
            del self.scans[each_row.row()]
            
    def flip_lines(self, line1, line2):
        
        scan1 = self.scans[line1]
        self.scans[line1] = self.scans[line2]
        self.scans[line2] = scan1
        self.display_line(line1)
        self.display_line(line2)


    def _get_filename_table_widget(self):

        self.filename_table = QTableWidget()
        self.filename_table.setGeometry(400, 400, 600, 300)
        self.filename_table.setColumnCount(1)
        self.filename_table.setColumnWidth(0,500)
        self.filename_table.setHorizontalHeaderLabels(["Datei"])
        self.filename_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.filename_table.itemClicked.connect(self._file_clicked)
        
        return self.filename_table

    def nextId(self):
    
        if self.wizard.pages[self.wizard.SCANNER_TYPE_PAGE].scanner_type == Scannertype.FLATBED:
            return self.wizard.SCAN_ROTATION_PAGE
        
        return -1

class ProjectWizardPagePagesPerScan(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        self.wizard = parent

        self.setTitle("Auswahl der Seiten pro Scan")
        self.setSubTitle("\"Gemischt\" bedeutet, dass Titel und Rückseite " +
                         "auch Einzelscans sein können.")
        
        self.pages_per_scan = None

        self.labels = {"1 Seite pro Scan": 1,
                       "2 Seiten pro Scan oder gemischt": 2}

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Wie viele Seiten sind auf jedem Scan?'))
        for label in self.labels.keys():
            radiobutton = QRadioButton(label)
            radiobutton.toggled.connect(self.on_click)
            if self.labels[label] == 1:
                radiobutton.setChecked(True)
            layout.addWidget(radiobutton)

        self.setLayout(layout)
        
    def on_click(self):

        radiobutton = self.sender()
        self.pages_per_scan = self.labels[radiobutton.text()]

class ProjectWizardPageScannerType(QWizardPage):
    
    def __init__(self, parent):

        super().__init__(parent)
        
        self.setTitle("Scanner-Typ wählen")
        self.setSubTitle("Davon hängt ab, wie die Seitenanordnung interpretiert wird.")
 
        self.labels = {"Overheadscanner": Scannertype.OVERHEAD,
                       "Flachbettscanner": Scannertype.FLATBED,
                       "Einzug (Duplex)": Scannertype.FEEDER_DUPLEX,
                       "Einzug (Simplex)": Scannertype.FEEDER_SIMPLEX}
        self.scanner_type = None

        layout = QVBoxLayout()
        for label in self.labels.keys():
            radiobutton = QRadioButton(label)
            radiobutton.toggled.connect(self.on_click)
            if self.labels[label] == Scannertype.OVERHEAD:
                radiobutton.setChecked(True)
            layout.addWidget(radiobutton)

        self.setLayout(layout)

    def on_click(self):

        radiobutton = self.sender()
        self.scanner_type = self.labels[radiobutton.text()]

class ProjectWizardPageRotation(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        
        self.labels = {"Nein, sie sind nicht gedeht": 0,
                       "Um 90° im Uhrzeigersinn": 90,
                       "Stehen auf dem Kopf": 180,
                       "Um 90° gegen den Uhrzeigersinn": 270}
        self.scan_rotation = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Sind die Scans gedreht?'))
        for label in self.labels.keys():
            radiobutton = QRadioButton(label)
            radiobutton.toggled.connect(self.on_click)
            if self.labels[label] == 0:
                radiobutton.setChecked(True)
            layout.addWidget(radiobutton)
            
        self.alternating_checkbutton = QCheckBox("Drehung ist alternierend")
        layout.addWidget(self.alternating_checkbutton)

        self.setLayout(layout)
        
    def on_click(self):

        radiobutton = self.sender()
        self.scan_rotation = self.labels[radiobutton.text()]

    alternating = property(lambda self: self.alternating_checkbutton.isChecked())
    
@singleton
class Window(QMainWindow):
    

    @inject
    def __init__(self, project_service: ProjectService):

        super().__init__()
        
        self.project_service = project_service
        self._create_widgets()
        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle("Scan-Kovertierer")
    
    def _create_widgets(self):
        
        new_project_action = QAction(QIcon('start.png'), '&Neues Projekt', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.setStatusTip('Neues Projekt')
        new_project_action.triggered.connect(self._start_new_project)

        exit_action = QAction(QIcon('exit.png'), '&Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)

        self.statusBar().showMessage("Programm gestartet...")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(new_project_action)
        fileMenu.addAction(exit_action)

    def _start_new_project(self):
        
        wizard = ProjectWizard()
        if wizard.exec():
            project = self.project_service.create_project(wizard.scans,
                                                          wizard.scan_type,
                                                          wizard.project_type)
            self._init_from_project(project)
        
    def _init_from_project(self, project: Project):
        
        self.project = project
        
            
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector(PageGeneratorsModule())
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
