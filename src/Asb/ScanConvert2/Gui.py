'''
Created on 06.11.2022

@author: michael
'''
import sys

from PyQt5.Qt import QMainWindow, QAction, QIcon, qApp
from PyQt5.QtWidgets import QApplication
from injector import inject, Injector, singleton

from Asb.ScanConvert2.PageGenerators import PageGeneratorsModule
from Asb.ScanConvert2.ScanConvertServices import ProjectService


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
        
        pass
if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    injector = Injector(PageGeneratorsModule())
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
