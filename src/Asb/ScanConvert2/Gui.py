'''
Created on 06.11.2022

@author: michael
'''
import sys

from PyQt5.Qt import QMainWindow, QAction, QIcon, qApp, QWizard, QWizardPage,\
    QLabel, QRadioButton, QVBoxLayout, QPushButton, QHBoxLayout, QTableWidget,\
    QAbstractItemView, QFileDialog, QTableWidgetItem
from PyQt5.QtWidgets import QApplication
from injector import inject, Injector, singleton

from Asb.ScanConvert2.PageGenerators import PageGeneratorsModule
from Asb.ScanConvert2.ScanConvertServices import ProjectService
from Asb.ScanConvert2.ScanConvertDomain import Projecttype, Scan
import os

class ProjectWizard(QWizard):
    
    def __init__(self):
        
        super().__init__()
        self.addPage(ProjectWizardPage1(self))
        self.addPage(ProjectWizardPage2(self))
        self.setWindowTitle("Neues Projekt anlegen")
        
class ProjectWizardPage1(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        
        self.button_texts = {
            "Pdf-Erstellung": Projecttype.PDF,
            'TIFF-Datei-Erstellung für Langzeitarchivierung': Projecttype.TIFF,
            'Pdf- und TIFF-Datei-Erstellung': Projecttype.BOTH
            }
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Bitte den Projekttyp auswählen:'))
        for button_text in self.button_texts.keys(): 
            radiobutton = QRadioButton(button_text)
            radiobutton.toggled.connect(self.on_click)
            layout.addWidget(radiobutton)

        self.setLayout(layout)
        
    def on_click(self):

        radiobutton = self.sender()
        self.project_type = self.button_texts[radiobutton.text()]        

class ProjectWizardPage2(QWizardPage):
    
    def __init__(self, parent):
        
        super().__init__(parent)
        
        self.scans = []
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Scans hinzufügen:'))
        
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
        
        self.project_wizard = ProjectWizard()
        
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
        
        self.project_wizard.show()
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector(PageGeneratorsModule())
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
