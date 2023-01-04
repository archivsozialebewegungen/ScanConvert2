'''
Created on 02.11.2022

@author: michael
'''
import io

from PIL import Image
from injector import singleton, inject
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from Asb.ScanConvert2.OCR import OcrRunner, OCRLine, OCRPage, OCRWord
from Asb.ScanConvert2.ScanConvertDomain import Project, Algorithm, \
    SortType
from Asb.ScanConvert2.ProjectGenerator import ProjectGenerator
from reportlab.platypus.paragraph import Paragraph


INVISIBLE = 3

class VerticalParagraph(Paragraph):
    """Paragraph that is printed vertically"""

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.horizontal_position = -self.style.leading

    def draw(self):
        """ Draw text """
        canvas = self.canv
        canvas.rotate(90)
        canvas.translate(1, self.horizontal_position)
        super().draw()

    def wrap(self, available_width, _):
        """ Wrap text in table """
        string_width = self.canv.stringWidth(
            self.getPlainText(), self.style.fontName, self.style.fontSize
        )
        self.horizontal_position = - (available_width + self.style.leading) / 2
        height, _ = super().wrap(availWidth=1 + string_width, availHeight=available_width)
        return self.style.leading, height
    
@singleton
class OCRService(object):
    '''
    This class performs ocr on the page image and adds the
    words in an invisible font to the canvas.
    '''
    
    @inject
    def __init__(self, ocr_runner: OcrRunner):
        
        self.ocr_runner = ocr_runner
    
    def add_ocrresult_to_pdf(self, img: Image, pdf: Canvas) -> Canvas:
        
        page = self.ocr_runner.run_tesseract(img)
        
        for line in page.lines:
            pdf = self._write_line(line, pdf, page)

        return pdf
    
    def _write_line(self, line: OCRLine, pdf: Canvas, page: OCRPage) -> Canvas:

            
        for word in line.words:
            pdf = self._write_word(word, pdf, line, page)
        
        return pdf
    
    def _write_word(self, word: OCRWord, pdf: Canvas, line: OCRLine, page: OCRPage) -> Canvas:

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

        offset = page.height
        if line.textangle == 90:
            offset = page.width
        text_origin_x = word.bbox[0] * 72.0 / page.dpi
        text_origin_y = offset - word.bbox[1] * 72.0 / page.dpi
        if line.baseline_coefficients[0] != 1.0 and line.baseline_coefficients[1] != 0.0:
            # Wir nutzen die Baseline-Informationen von tesseract
            # Die beiden Koeffizienten definieren eine lineare Gleichung für
            # die Baseline der Zeile        
            wortmittelpunkt_x_absolut = (word.bbox[0] + word.bbox[2]) / 2
            wortmittelpunkt_x_relativ = wortmittelpunkt_x_absolut - line.bbox[0]
            baseline_abweichung = wortmittelpunkt_x_relativ * line.baseline_coefficients[0] + line.baseline_coefficients[1]
            text_origin_y = (offset - line.bbox[3] - baseline_abweichung) * 72.0 / page.dpi
        
        return (text_origin_x, text_origin_y)
        
@singleton
class PdfService:
    
    @inject
    def __init__(self, ocr_service: OCRService):

        self.ocr_service = ocr_service
        self.run_ocr = True
    
    def create_pdf_file(self, project: Project, filebase: str, resolution: int = 300):
        
   
   
        pdf = Canvas(self._get_file_name(filebase), pageCompression=1)
        pdf.setAuthor(project.metadata.author)
        pdf.setCreator('Scan-Convert 2')
        pdf.setTitle(project.metadata.title)
        pdf.setKeywords(project.metadata.keywords)
        pdf.setSubject(project.metadata.subject)
        
        page_counter = 0
        for page in project.pages:
            page_counter += 1
            print("Processing page %d" % page_counter)
            image = page.get_final_image(resolution)
            width_in_dots, height_in_dots = image.size
            
            page_width = width_in_dots * 72 / resolution
            page_height = height_in_dots * 72 / resolution
            
            pdf.setPageSize((width_in_dots * inch / resolution, height_in_dots * inch / resolution))

            img_stream = io.BytesIO()
            image.save(img_stream, format='png')
            img_stream.seek(0)
            img_reader = ImageReader(img_stream)
            pdf.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
            if self.run_ocr:
                pdf = self.ocr_service.add_ocrresult_to_pdf(image, pdf)
            pdf.showPage()
        
        pdf.save()
        
    def _get_file_name(self, filebase: str):
        
        if filebase[-4:] == ".pdf":
            return filebase
        return filebase + ".pdf"

@singleton
class TiffService(object):
    
    def create_tiff_files(self, project: Project, resolution: int = 400):
        
        raise Exception("Not yet implemented")

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
                    rotation_alternating: bool,
                    pdf_algorithm: Algorithm) -> Project:

        print("Scan rotation is now: %d" % scan_rotation)
        return self.project_generator.scans_to_project(scans,
                    pages_per_scan,
                    sort_type,
                    scan_rotation,
                    rotation_alternating,
                    pdf_algorithm)

    def export_pdf(self, project: Project, filename: str):
        
        self.pdf_service.create_pdf_file(project, filename)
