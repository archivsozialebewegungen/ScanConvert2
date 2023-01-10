'''
Created on 09.01.2023

@author: michael
'''
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout,\
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit
from Asb.ScanConvert2.ScanConvertDomain import MetaData

class MetadataDialog(QDialog):
    '''
    Dialog zum Erfassen der Metadaten
    '''


    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Metadaten für das Projekt")
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        title_layout = QHBoxLayout()
        label = QLabel("Titel:")
        title_layout.addWidget(label)
        self.title_input = QLineEdit(self)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        author_layout = QHBoxLayout()
        label = QLabel("Autor:in:")
        author_layout.addWidget(label)
        self.author_input = QLineEdit(self)
        author_layout.addWidget(self.author_input)
        layout.addLayout(author_layout)
        
        keywords_layout = QHBoxLayout()
        label = QLabel("Schlagworte:")
        keywords_layout.addWidget(label)
        self.keywords_input = QLineEdit(self)
        keywords_layout.addWidget(self.keywords_input)
        layout.addLayout(keywords_layout)
        
        label = QLabel("Beschreibung:")
        layout.addWidget(label)
        self.description_input = QPlainTextEdit(self)
        layout.addWidget(self.description_input)
        
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)

    def _get_metadata(self):
        
        metadata = MetaData()
        metadata.title = self.title_input.text()
        metadata.author = self.author_input.text()
        metadata.keywords = self.keywords_input.text()
        metadata.subject = self.description_input.toPlainText()
        return metadata
        
    def _set_metadata(self, metadata: MetaData):
        
        self.title_input.setText(metadata.title)
        self.author_input.setText(metadata.author)
        self.keywords_input.setText(metadata.keywords)
        self.description_input.setPlainText(metadata.subject)

    metadata = property(_get_metadata, _set_metadata)
