'''
Created on 09.01.2023

@author: michael
'''
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, \
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QCheckBox, QComboBox
import pytesseract

from Asb.ScanConvert2.ScanConvertDomain import MetaData, ProjectProperties


class MetadataDialog(QDialog):
    '''
    Dialog zum Erfassen der Metadaten
    '''


    def __init__(self, parent):
        super().__init__(parent)
        self.object_type = MetaData
        self.setWindowTitle("Metadaten für das Projekt")
        self.setGeometry(40, 40, 600, 400)
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        line_inputs = QHBoxLayout()
        self.layout.addLayout(line_inputs)
        self.label_column = QVBoxLayout()
        line_inputs.addLayout(self.label_column)
        self.input_column = QVBoxLayout()
        line_inputs.addLayout(self.input_column)
        
        label = QLabel("Titel:")
        self.label_column.addWidget(label)
        self.title_input = QLineEdit(self)
        self.input_column.addWidget(self.title_input)
        
        label = QLabel("Autor:in:")
        self.label_column.addWidget(label)
        self.author_input = QLineEdit(self)
        self.input_column.addWidget(self.author_input)
        
        label = QLabel("Schlagworte:")
        self.label_column.addWidget(label)
        self.keywords_input = QLineEdit(self)
        self.input_column.addWidget(self.keywords_input)
        
        label = QLabel("Beschreibung:")
        self.layout.addWidget(label)
        self.description_input = QPlainTextEdit(self)
        self.layout.addWidget(self.description_input)
        
        self.layout.addWidget(buttonBox)
        
        self.setLayout(self.layout)

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

    metadata = property(lambda self: self._get_metadata(), lambda self, metadata: self._set_metadata(metadata))

class DDFMetadataDialog(MetadataDialog):
    '''
    Dialog zum Erfassen der Metadaten
    '''


    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Metadaten für den DDF-Export")
        self.setGeometry(40, 40, 600, 800)

        label = QLabel("Dateistamm:")
        self.label_column.addWidget(label)
        self.ddf_prefix_input = QLineEdit(self)
        self.input_column.addWidget(self.ddf_prefix_input)
        
        label = QLabel("Signatur:")
        self.label_column.addWidget(label)
        self.signature_input = QLineEdit(self)
        self.input_column.addWidget(self.signature_input)

        label = QLabel("Quelle:")
        self.label_column.addWidget(label)
        self.source_input = QLineEdit(self)
        self.input_column.addWidget(self.source_input)

        label = QLabel("Stadt:")
        self.label_column.addWidget(label)
        self.city_input = QLineEdit(self)
        self.input_column.addWidget(self.city_input)

        label = QLabel("Zusatzangabe:")
        self.label_column.addWidget(label)
        self.special_instructions_input = QLineEdit(self)
        self.input_column.addWidget(self.special_instructions_input)

        label = QLabel("Mets Dokumenttyp:")
        self.label_column.addWidget(label)
        self.mets_type_input = QLineEdit(self)
        self.input_column.addWidget(self.mets_type_input)

        label = QLabel("DDF Dokumenttyp:")
        self.label_column.addWidget(label)
        self.ddf_type_input = QLineEdit(self)
        self.input_column.addWidget(self.ddf_type_input)

        label = QLabel("DDF Untertyp:")
        self.label_column.addWidget(label)
        self.ddf_subtype_input = QLineEdit(self)
        self.input_column.addWidget(self.ddf_subtype_input)
        
        label = QLabel("Publikationsdatum:")
        self.label_column.addWidget(label)
        self.publication_year_input = QLineEdit(self)
        self.input_column.addWidget(self.publication_year_input)

        label = QLabel("Ort der Publikation:")
        self.label_column.addWidget(label)
        self.publication_city_input = QLineEdit(self)
        self.input_column.addWidget(self.publication_city_input)

        label = QLabel("Verlag:")
        self.label_column.addWidget(label)
        self.publisher_input = QLineEdit(self)
        self.input_column.addWidget(self.publisher_input)

        label = QLabel("Sprache der Publikation:")
        self.label_column.addWidget(label)
        self.publication_language_input = QLineEdit(self)
        self.input_column.addWidget(self.publication_language_input)


    def _get_metadata(self):
        
        metadata = super()._get_metadata()
        metadata.ddf_prefix = self.ddf_prefix_input.text()
        metadata.signatur = self.signature_input.text()
        metadata.source = self.source_input.text()
        metadata.city = self.city_input.text()
        metadata.special_instructions = self.special_instructions_input.text()
        metadata.mets_type = self.mets_type_input.text()
        metadata.ddf_type = self.ddf_type_input.text()
        metadata.ddf_subtype = self.ddf_subtype_input.text()

        metadata.publication_year = self.publication_year_input.text()
        metadata.publication_city = self.publication_city_input.text()
        metadata.publisher = self.publisher_input.text()
        metadata.publication_language = self.publication_language_input.text()


        return metadata

    def _set_metadata(self, metadata: MetaData):
        
        super()._set_metadata(metadata)
        self.ddf_prefix_input.setText(metadata.ddf_prefix)
        self.signature_input.setText(metadata.signatur)
        self.source_input.setText(metadata.source)
        self.city_input.setText(metadata.city)
        self.special_instructions_input.setText(metadata.special_instructions)
        self.mets_type_input.setText(metadata.mets_type)
        self.ddf_type_input.setText(metadata.ddf_type)
        self.ddf_subtype_input.setText(metadata.ddf_subtype)
        
        self.publication_year_input.setText(metadata.publication_year)
        self.publication_city_input.setText(metadata.publication_city)
        self.publisher_input.setText(metadata.publisher)
        self.publication_language_input.setText(metadata.publication_language)
        
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
