'''
Created on 09.01.2023

@author: michael
'''
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, \
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QCheckBox, QComboBox

from Asb.ScanConvert2.ScanConvertDomain import MetaData, ProjectProperties
from PySide6.QtCore import QRect
import pytesseract


class MetadataDialog(QDialog):
    '''
    Dialog zum Erfassen der Metadaten
    '''


    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Metadaten für das Projekt")
        self.setGeometry(40, 40, 600, 400)
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        line_inputs = QHBoxLayout()
        layout.addLayout(line_inputs)
        label_column = QVBoxLayout()
        line_inputs.addLayout(label_column)
        input_column = QVBoxLayout()
        line_inputs.addLayout(input_column)
        
        label = QLabel("Titel:")
        label_column.addWidget(label)
        self.title_input = QLineEdit(self)
        input_column.addWidget(self.title_input)
        
        label = QLabel("Autor:in:")
        label_column.addWidget(label)
        self.author_input = QLineEdit(self)
        input_column.addWidget(self.author_input)
        
        label = QLabel("Schlagworte:")
        label_column.addWidget(label)
        self.keywords_input = QLineEdit(self)
        input_column.addWidget(self.keywords_input)
        
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
        metadata.reviewed = True
        return metadata
        
    def _set_metadata(self, metadata: MetaData):
        
        self.title_input.setText(metadata.title)
        self.author_input.setText(metadata.author)
        self.keywords_input.setText(metadata.keywords)
        self.description_input.setPlainText(metadata.subject)

    metadata = property(_get_metadata, _set_metadata)

class PropertiesDialog(QDialog):
    '''
    Dialog zum Erfassen der Properties
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Metadaten für das Projekt")
        self.setGeometry(40, 40, 500, 200)
        
        self.available_languages = pytesseract.get_languages(config='')
        self.available_languages.remove("osd")
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        label = QLabel('<font size="+2"><b>Projekteigenschaften:</b></font>')
        layout.addWidget(label)
        line_inputs = QHBoxLayout()
        layout.addLayout(line_inputs)
        label_column = QVBoxLayout()
        line_inputs.addLayout(label_column)
        input_column = QVBoxLayout()
        line_inputs.addLayout(input_column)
        
        label = QLabel("Auflösung pdf:")
        label_column.addWidget(label)
        self.pdf_resolution_input = QLineEdit(self)
        input_column.addWidget(self.pdf_resolution_input)
        
        label = QLabel("Auflösung tif:")
        label_column.addWidget(label)
        self.tif_resolution_input = QLineEdit(self)
        input_column.addWidget(self.tif_resolution_input)
        
        label = QLabel("Texterkennung ausführen:")
        label_column.addWidget(label)
        self.run_ocr_checkbox = QCheckBox(self)
        input_column.addWidget(self.run_ocr_checkbox)
        
        label = QLabel("Sprache für die Texterkennung:")
        label_column.addWidget(label)
        self.ocr_lang_select = QComboBox()
        self.ocr_lang_select.addItems(self.available_languages)
        input_column.addWidget(self.ocr_lang_select)
        
        label = QLabel("PDF/A-Datei erstellen und Graphiken optimieren:")
        label_column.addWidget(label)
        self.create_pdfa_checkbox = QCheckBox(self)
        input_column.addWidget(self.create_pdfa_checkbox)
        
        label = QLabel("Farbhintergründe vereinheitlichen:")
        label_column.addWidget(label)
        self.color_normalization_checkbox = QCheckBox(self)
        input_column.addWidget(self.color_normalization_checkbox)

        layout.addWidget(buttonBox)
        
        self.setLayout(layout)

    def _get_properties(self):
        
        properties = ProjectProperties()
        try:
            properties.pdf_resolution = int(self.pdf_resolution_input.text())
        except:
            pass
        try:
            properties.tif_resolution = int(self.tif_resolution_input.text())
        except:
            pass
        properties.run_ocr = self.run_ocr_checkbox.isChecked()
        properties.ocr_lang = self.ocr_lang_select.currentText()
        properties.create_pdfa = self.create_pdfa_checkbox.isChecked()
        properties.normalize_background_colors = self.color_normalization_checkbox.isChecked()
        return properties
        
    def _set_properties(self, properties: ProjectProperties):
        
        self.pdf_resolution_input.setText("%s" % properties.pdf_resolution)
        self.tif_resolution_input.setText("%s" % properties.tif_resolution)
        self.run_ocr_checkbox.setChecked(properties.run_ocr)
        for idx in range(0, len(self.available_languages)):
            if self.ocr_lang_select.itemText(idx) == "%s" % properties.ocr_lang:
                self.ocr_lang_select.setCurrentIndex(idx)
                break
        self.create_pdfa_checkbox.setChecked(properties.create_pdfa)
        self.color_normalization_checkbox.setChecked(properties.normalize_background_colors)

    project_properties = property(_get_properties, _set_properties)
