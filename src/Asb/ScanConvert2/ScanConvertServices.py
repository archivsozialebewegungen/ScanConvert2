'''
Created on 02.11.2022

@author: michael
'''
import io
import os
import pickle
import shutil
import tempfile
from zipfile import ZipFile

from PIL import Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2
from injector import singleton, inject
import ocrmypdf
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from Asb.ScanConvert2.Algorithms import AlgorithmImplementations, Algorithm
from Asb.ScanConvert2.OCR import OcrRunner, OCRLine, OCRPage, OCRWord
from Asb.ScanConvert2.ProjectGenerator import ProjectGenerator, SortType
from Asb.ScanConvert2.ScanConvertDomain import Project, Page, Region


INVISIBLE = 3

@singleton
class OCRService(object):
    '''
    This class performs ocr on the page image and adds the
    words in an invisible font to the canvas.
    '''
    
    @inject
    def __init__(self, ocr_runner: OcrRunner):
        
        self.ocr_runner = ocr_runner
    
    def add_ocrresult_to_pdf(self, img: Image, pdf: Canvas, lang: str) -> Canvas:
        
        page = self.ocr_runner.run_tesseract(img, lang)
        
        for line in page.lines:
            pdf = self._write_line(line, pdf, page)

        return pdf
    
    def _write_line(self, line: OCRLine, pdf: Canvas, page: OCRPage) -> Canvas:

        if line.textangle == 90:
            bbox_new = (line.bbox[3], -1*line.bbox[2], line.bbox[1], -1*line.bbox[0])
            line.bbox = bbox_new
            pdf.rotate(90)
            
        for word in line.words:
            pdf = self._write_word(word, pdf, line, page)
        
        if line.textangle == 90:
            pdf.rotate(270)
            
        return pdf
    
    def _write_word(self, word: OCRWord, pdf: Canvas, line: OCRLine, page: OCRPage) -> Canvas:

        if line.textangle == 90:
            bbox_new = (word.bbox[3], -1*word.bbox[2], word.bbox[1], -1*word.bbox[0])
            word.bbox = bbox_new

        text_origin = self._calculate_text_origin(word, line, page)
        
        text = pdf.beginText()
        
        text.setTextRenderMode(INVISIBLE)
        text.setFont('Times-Roman', line.font_size)
        text.setTextOrigin(text_origin[0], text_origin[1])
        # Text an bounding box anpassen
        text_width = pdf.stringWidth(word.text, 'Times-Roman', line.font_size)
        if text_width != 0:
            text_width = pdf.stringWidth(word.text, 'Times-Roman', line.font_size)
            bbox_width = (word.bbox[2] - word.bbox[0]) * 72.0 / page.dpi
            text.setHorizScale(100.0 * bbox_width / text_width)
        
        text.textLine(word.text)

        # TODO: Textrotation. Ist aber schwierig. rotate() auf der canvas
        # aufzurufen ist nicht das Ding zu tun. Hier wird um die linke untere
        # Ecke der Canvas rotiert. Und die Syntax von text.transform() versteht
        # kein Mensch.
        # Falls das implementiert wird, dann sollte oben die baseline-
        # Abweichung nicht mehr für den Wortmittelpunkt, sondern für die linke
        # Seite der bounding box berechnet werden.
        #
        #rotation_angle = round(math.degrees(math.atan(abs(line.baseline_coefficients[0]))))
        #if line.baseline_coefficients[0] > 0:
        #    rotation_angle *= -1

        pdf.drawText(text)
                
        return pdf

    def _calculate_text_origin(self, word, line, page):

        text_origin_x = word.bbox[0] * 72.0 / page.dpi
        text_origin_y = word.bbox[1] * 72.0 / page.dpi
        if not(line.baseline_coefficients[0] == 1.0 and line.baseline_coefficients[1] == 0.0):
            # Wir nutzen die Baseline-Informationen von tesseract
            # Die beiden Koeffizienten definieren eine lineare Gleichung für
            # die Baseline der Zeile        
            wortmittelpunkt_x_absolut = (word.bbox[0] + word.bbox[2]) / 2
            wortmittelpunkt_x_relativ = wortmittelpunkt_x_absolut - line.bbox[0]
            baseline_abweichung = wortmittelpunkt_x_relativ * line.baseline_coefficients[0] + line.baseline_coefficients[1]
            text_origin_y = (line.bbox[3] - baseline_abweichung) * 72.0 / page.dpi
        
        return (text_origin_x, text_origin_y)
        
@singleton
class TiffService(object):

    replacements = {'Ä': 'Ae',
                    'Ö': 'Oe',
                    'Ü': 'Ue',
                    'ß': 'ss',
                    'ä': 'ae',
                    'ö': 'oe',
                    'ü': 'ue'
                    }
    
        
    document_name_tag = 269
    page_name_tag = 285
    artist_tag = 315
    x_resolution = 282
    y_resolution = 283
    resolution_unit = 296
    inch_resolution_unit = 2
    image_description = 270
        
    
    def create_tiff_file_archive(self, project: Project, filebase):
        
        zipfile = ZipFile(self._get_file_name(filebase), mode='w')
        
        meta_data = ImageFileDirectory_v2()
        meta_data[self.artist_tag] = self.utf8_to_ascii(project.metadata.author)
        meta_data[self.document_name_tag] = self.utf8_to_ascii(project.metadata.title)
        meta_data[self.image_description] = self.utf8_to_ascii("%s\n\nSchlagworte: %s" % (project.metadata.subject, project.metadata.keywords))
        meta_data[self.x_resolution] = project.project_properties.tif_resolution
        meta_data[self.y_resolution] = project.project_properties.tif_resolution
        meta_data[self.resolution_unit] = self.inch_resolution_unit
        
        with tempfile.TemporaryDirectory() as tempdir:

            no_of_pages = len(project.pages)
            
            counter = 0
            for page in project.pages:
                counter += 1
                meta_data[self.page_name_tag] = "Seite %d von %d des Dokuments" % (counter, no_of_pages)
                page_name = "Seite%04d.tif" % counter
                file_name = os.path.join(tempdir, page_name)
                img = page.get_base_image(project.project_properties.tif_resolution)
                img.save(file_name, tiffinfo=meta_data, compression="tiff_lzw")
                zipfile.write(file_name, page_name)
            
            readme_file = os.path.join(tempdir, "readme.txt")
            with open(readme_file, 'w') as readme:
                readme.write("Information zu diesem ZIP Archiv\n================================\n")
                readme.write("Titel: %s\n" % project.metadata.title)
                readme.write("Anzahl der Seiten/Dateien: %d\n" % no_of_pages)
                readme.write("Autor:in: %s\n\n" % project.metadata.author)
                readme.write("Sonstige Informationen:\n%s\n\n" % project.metadata.subject)
                readme.write("Schlagworte: %s\n\n" % project.metadata.keywords)
                readme.write("Dieses ZIP-Archiv enthält Digitalisatsdateien, die mit dem\n")
                readme.write("Scan Konvertierungsprogramm des Archivs Soziale Bewegungen e.V.\n")
                readme.write("Freiburg erstellt und zusammengepackt wurden.\n")
                readme.write("Das Programm kann hier heruntergeladen werden:\n")
                readme.write("https://github.com/archivsozialebewegungen/ScanConvert2\n")
            zipfile.write(readme_file, "readme.txt")
                
            zipfile.close()

    def _get_file_name(self, filebase: str):
        
        if filebase[-4:] == ".zip":
            return filebase
        return filebase + ".zip"
    
    def utf8_to_ascii(self, string: str):
        
        for utf8, ascii_string in self.replacements.items():
            string = string.replace(utf8, ascii_string)
        return string

@singleton
class FinishingService(object):
    
    @inject
    def __init__(self, algorithm_implementations: AlgorithmImplementations):
        
        self.algorithm_implementations = algorithm_implementations
    
    def create_finale_image(self, page: Page, target_resolution: int) -> Image:
        
        img = final_img = page.get_raw_image()

        target_source_ratio = 1.0        
        if page.source_resolution != target_resolution:
            target_source_ratio = target_resolution / page.source_resolution
            img = self._change_resolution(img, target_source_ratio)
        
        if page.main_region.mode_algorithm != Algorithm.NONE:
            final_img = self._apply_algorithm(img, page.main_region.mode_algorithm)
            
        return self._apply_regions(page.sub_regions, final_img, img, target_source_ratio)

    def _change_resolution(self, img: Image, target_source_ratio: float) -> Image:

        current_width, current_height = img.size
        new_width = int(current_width * target_source_ratio)
        new_height = int(current_height * target_source_ratio)

        return img.resize((new_width, new_height))
        
    def _apply_regions(self, regions: [],final_img: Image, img: Image, target_source_ratio: float) -> Image:
        
        if len(regions) == 0:
            return final_img
        
        for region in regions:
            final_img = self._apply_region(region, final_img, img, target_source_ratio)
    
        return final_img
    
    def _apply_region(self, region: Region, final_img: Image, img: Image, target_source_ratio) -> Image:
        
        region_img = img.crop((round(region.x * target_source_ratio),
                               round(region.y * target_source_ratio),
                               round(region.x2 * target_source_ratio),
                               round(region.y2 * target_source_ratio)))
        region_img = self._apply_algorithm(region_img, region.mode_algorithm)
        if region_img.mode == "RGBA" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGBA")
        if region_img.mode == "RGB" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGB")
        if region_img.mode == "L" and final_img.mode == "1":
            final_img = final_img.convert("L")
        final_img.paste(region_img, (round(region.x * target_source_ratio),
                                     round(region.y * target_source_ratio),
                                     round(region.x2 * target_source_ratio),
                                     round(region.y2 * target_source_ratio)))
        return final_img

    def _apply_algorithm(self, img: Image, algorithm: Algorithm):
        
        return self.algorithm_implementations[algorithm].transform(img)

@singleton
class PdfService:
    
    @inject
    def __init__(self, ocr_service: OCRService, finishing_service: FinishingService):

        self.ocr_service = ocr_service
        self.finishing_service = finishing_service
    
    def create_pdf_file(self, project: Project, filebase: str):
   
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "output.pdf")
            pdf = Canvas(temp_file, pageCompression=1)
            pdf.setAuthor(project.metadata.author)
            pdf.setCreator('Scan-Convert 2')
            pdf.setTitle(project.metadata.title)
            pdf.setKeywords(project.metadata.keywords)
            pdf.setSubject(project.metadata.subject)
        
            page_counter = 0
            for page in project.pages:
                page_counter += 1
                if page.skip_page:
                    continue
                image = self.finishing_service.create_finale_image(page, project.project_properties.pdf_resolution)
                width_in_dots, height_in_dots = image.size
            
                page_width = width_in_dots * 72 / project.project_properties.pdf_resolution
                page_height = height_in_dots * 72 / project.project_properties.pdf_resolution
            
                pdf.setPageSize((width_in_dots * inch / project.project_properties.pdf_resolution,
                                 height_in_dots * inch / project.project_properties.pdf_resolution))

                img_stream = io.BytesIO()
                image.save(img_stream, format='png')
                img_stream.seek(0)
                img_reader = ImageReader(img_stream)
                pdf.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
                if project.project_properties.run_ocr:
                    pdf = self.ocr_service.add_ocrresult_to_pdf(image, pdf, project.project_properties.ocr_lang)
                pdf.showPage()
        
            pdf.save()
            # Convert to pdfa and optimize graphics
            if project.project_properties.create_pdfa:
                #ocrmypdf.configure_logging(verbosity=Verbosity.quiet)
                ocrmypdf.ocr(temp_file, self._get_file_name(filebase), skip_text=True)
            else:
                shutil.copy(temp_file, self._get_file_name(filebase))
        
    def _get_file_name(self, filebase: str):
        
        if filebase[-4:] == ".pdf":
            return filebase
        return filebase + ".pdf"

@singleton    
class ProjectService(object):
    
    @inject
    def __init__(self,
                 project_generator: ProjectGenerator,
                 pdf_service: PdfService,
                 tiff_service: TiffService):
        
        self.project_generator = project_generator
        self.pdf_service = pdf_service
        self.tiff_service = tiff_service
        
    def create_project(self,
                    scans: [],
                    pages_per_scan: int,
                    sort_type: SortType,
                    scan_rotation: int,
                    rotation_alternating: bool) -> Project:

        return self.project_generator.scans_to_project(scans,
                    pages_per_scan,
                    sort_type,
                    scan_rotation,
                    rotation_alternating)
        
    def save_project(self, file_name: str, project: Project):
        
        if file_name[-4:] != '.scp':
            file_name += ".scp"
        file = open(file_name, "wb")
        pickle.dump(project, file)
        file.close()
        
    def load_project(self, file_name: str) -> Project:
        
        file = open(file_name, "rb")
        project = pickle.load(file)
        file.close()
        return project

    def export_pdf(self, project: Project, file_name: str):
        
        if file_name[-4:] == '.pdf':
            self.save_project(file_name.replace("pdf", "scp"), project)
        else:
            self.save_project(file_name + ".scp", project)
            
        self.pdf_service.create_pdf_file(project, file_name)

    def export_tif(self, project: Project, filename: str):
        
        self.tiff_service.create_tiff_file_archive(project, filename)
