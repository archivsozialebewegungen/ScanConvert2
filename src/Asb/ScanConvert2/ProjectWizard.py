'''
Created on 03.12.2022

@author: michael
'''
import os

from PySide6.QtWidgets import QVBoxLayout, QLabel, QRadioButton, QCheckBox, \
    QWizardPage, QAbstractItemView, QTableWidget, QTableWidgetItem, QFileDialog, \
    QHBoxLayout, QPushButton, QWizard, QLineEdit, QPlainTextEdit

from Asb.ScanConvert2.ScanConvertDomain import Scan, \
    SortType, MetaData

SCANS_PAGE = 1
PAGE_PER_SCAN_PAGE = 2
SINGLE_SORT_TYPE_PAGE = 3
DOUBLE_SORT_TYPE_PAGE = 4
SCAN_ROTATION_PAGE = 5

class ProjectWizard(QWizard):
        
    def __init__(self):
        
        super().__init__()
        self.pages = {
            PAGE_PER_SCAN_PAGE: ProjectWizardPagePagesPerScan(self),
            SCANS_PAGE: ProjectWizardPageScans(self),
            SCAN_ROTATION_PAGE: ProjectWizardScanRotation(self),
            SINGLE_SORT_TYPE_PAGE: ProjectWizardPageSingleSortType(self),
            DOUBLE_SORT_TYPE_PAGE: ProjectWizardPageDoubleSortType(self),
            }
        for page_id in self.pages.keys():
            self.setPage(page_id, self.pages[page_id])
             
        self.setWindowTitle("Neues Projekt anlegen")

    def _get_sort_type(self):
        
        if self.pages_per_scan == 1:
            return self.pages[SINGLE_SORT_TYPE_PAGE].result
        else:
            return self.pages[DOUBLE_SORT_TYPE_PAGE].result
                     
    pages_per_scan = property(lambda self: self.pages[PAGE_PER_SCAN_PAGE].result)
    scans = property(lambda self: self.pages[SCANS_PAGE].scans)
    scan_rotation = property(lambda self: self.pages[SCAN_ROTATION_PAGE].result)
    rotation_alternating = property(lambda self: self.pages[SCAN_ROTATION_PAGE].alternating)
    sort_type = property(_get_sort_type)
    

class AbstractRadioButtonProjectWizardPage(QWizardPage):
    
    def __init__(self, parent, title, subtitle, subsubtitle, buttons):
        
        super().__init__(parent)
        self.wizard = parent
        self.result = None
        
        self.setTitle(title)
        self.setSubTitle(subtitle)
        self.buttons = buttons
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(subsubtitle))
        checked = False
        for button_text in self.buttons.keys(): 
            radiobutton = QRadioButton(button_text)
            radiobutton.toggled.connect(self.on_click)
            if not checked:
                radiobutton.setChecked(True)
                checked = True
            self.layout.addWidget(radiobutton)

        self.setLayout(self.layout)
        
    def on_click(self):

        radiobutton = self.sender()
        print("Radio button text: %s" % radiobutton.text())
        self.result = self.buttons[radiobutton.text()]
        print("Result value: %s" % self.result)        


class ProjectWizardPageSingleSortType(AbstractRadioButtonProjectWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent,
            "Wie sind die Seiten angeordnet?",
            "Je nach Scanner m??ssen die Seiten in den Scans unterschiedlich " + 
                "in die richtige Reihenfolge gebracht werden.",
            'Bitte die Seitenanordnung ausw??hlen:',
            {
                "Sortierung in bestehender Reihenfolge": SortType.STRAIGHT,
                'Erst alle Vorder-, dann alle R??ckseiten': SortType.SINGLE_ALL_FRONT_ALL_BACK,
            })
        
    def nextId(self, *args, **kwargs):
        
        return SCAN_ROTATION_PAGE

class ProjectWizardPageDoubleSortType(AbstractRadioButtonProjectWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent,
            "Wie sind die Seiten angeordnet?",
            "Je nach Scanner m??ssen die Seiten in den Scans unterschiedlich " + 
                "in die richtige Reihenfolge gebracht werden.",
            'Bitte die Seitenanordnung ausw??hlen:',
            {
                "Sortierung in bestehender Reihenfolge": SortType.STRAIGHT,
                'Nach B??gen': SortType.SHEET,
                'Nach B??gen, erst alle Vorder- dann alle R??ckseiten': SortType.SHEET_ALL_FRONT_ALL_BACK 
            })

    def nextId(self, *args, **kwargs):
        
        return SCAN_ROTATION_PAGE

class ProjectWizardPagePagesPerScan(AbstractRadioButtonProjectWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent,
            "Auswahl der Seiten pro Scan",
            "\"Gemischt\" bedeutet, dass Titel und R??ckseite " + 
            "auch Einzelscans sein k??nnen.",
            'Wie viele Seiten sind auf jedem Scan?',
            {
                "1 Seite pro Scan": 1,
                "2 Seiten pro Scan oder gemischt": 2
            })

    def nextId(self, *args, **kwargs):
        
        if self.result == 1:
            return SINGLE_SORT_TYPE_PAGE
        else:
            return DOUBLE_SORT_TYPE_PAGE

class ProjectWizardScanRotation(AbstractRadioButtonProjectWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent,
        "Wie sind die Scans gedreht?",
        "Das ist sowohl f??r die Zerlegung wie auch die richtige " +
        "Seitenausrichtung wichtig.",
        "Drehung ausw??hlen:",
        {
            "Sie sind schon korrekt ausgerichtet": 0,
            "Um 90?? im Uhrzeigersinn": 90,
            "Stehen auf dem Kopf": 180,
            "Um 90?? gegen den Uhrzeigersinn": 270
        })

        self.alternating_checkbutton = QCheckBox("Drehung ist alternierend")
        self.layout.addWidget(self.alternating_checkbutton)

    alternating = property(lambda self: self.alternating_checkbutton.isChecked())

class ProjectWizardPageScans(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        self.wizard = parent
        
        self.setTitle("Scans zum Projekt hinzuf??gen")
        self.setSubTitle("Die Scans m??ssen in der richtigen Reihenfolge angegeben werden. " + 
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
        
        filenames = QFileDialog.getOpenFileNames(filter="Graphikdateien (*.jpg *.jpeg *.tif *.tiff *.gif *.png)")
        for filename in filenames[0]:
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
        self.filename_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for row in selected_rows:
            self.filename_table.selectRow(row)
        self.filename_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

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
        self.filename_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for row in selected_rows:
            self.filename_table.selectRow(row)
        self.filename_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

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
        self.filename_table.setColumnWidth(0, 500)
        self.filename_table.setHorizontalHeaderLabels(["Datei"])
        self.filename_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        return self.filename_table
