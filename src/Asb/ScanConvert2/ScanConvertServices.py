'''
Created on 02.11.2022

@author: michael
'''
import io

from PIL import Image, ImageFilter
from injector import singleton, inject
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from skimage.filters.thresholding import threshold_otsu, threshold_sauvola, \
    threshold_niblack

from Asb.ScanConvert2.OCR import OcrRunner, OCRLine, OCRPage, OCRWord
from Asb.ScanConvert2.ProjectGenerator import ProjectGenerator
from Asb.ScanConvert2.ScanConvertDomain import Project, \
    SortType, Page, Region, get_image_resolution, Algorithm
import numpy as np
import cv2


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
    
    def add_ocrresult_to_pdf(self, img: Image, pdf: Canvas) -> Canvas:
        
        page = self.ocr_runner.run_tesseract(img)
        
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
        if line.baseline_coefficients[0] != 1.0 and line.baseline_coefficients[1] != 0.0:
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
    
    def create_tiff_files(self, project: Project, resolution: int = 400):
        
        raise Exception("Not yet implemented")

@singleton
class FinishingService(object):
    
    def __init__(self):
        
        self.runners = {
        
            Algorithm.GRAY: lambda self, img: self._apply_algorithm_gray(img),
            Algorithm.GRAY_WHITE: lambda self, img: self._apply_algorithm_gray_on_white_text(img),
            Algorithm.OTSU: lambda self, img: self._apply_threshold_algorithm(img, Algorithm.OTSU),
            Algorithm.SAUVOLA: lambda self, img: self._apply_threshold_algorithm(img, Algorithm.SAUVOLA),
            Algorithm.NIBLACK: lambda self, img: self._apply_threshold_algorithm(img, Algorithm.NIBLACK),
            Algorithm.FLOYD_STEINBERG: lambda self, img: self._apply_algorithm_floyd_steinberg(img),
            Algorithm.COLOR_PAPER_QUANTIZATION: lambda self, img: self._apply_algorithm_color_paper(img),
            Algorithm.COLOR_TEXT_QUANTIZATION: lambda self, img: self._apply_algorithm_color_text_quantization(img),
            Algorithm.TWO_COLOR_QUANTIZATION: lambda self, img: self._apply_algorithm_quantization(img),
            Algorithm.BW_QUANTIZATION: lambda self, img: self._apply_algorithm_bw_quantization(img),
            Algorithm.WEISS: lambda self, img: self._apply_algorithm_white(img)
        }
        
    
    def create_finale_image(self, page: Page, target_resolution: int = 300) -> Image:
        
        img = final_img = page.get_base_image(target_resolution)
        
        if page.main_region.mode_algorithm != Algorithm.NONE:
            final_img = self.apply_algorithm(img, page.main_region.mode_algorithm)
            
        return self.apply_regions(page.sub_regions, final_img, img, target_resolution)
        
    def apply_regions(self, regions: [],final_img: Image, img: Image, target_resolution) -> Image:
        
        if len(regions) == 0:
            return final_img
        
        for region in regions:
            final_img = self.apply_region(region, final_img, img, target_resolution)
    
        return final_img
    
    def apply_region(self, region: Region, final_img: Image, img: Image, target_resolution) -> Image:
        
        region_img = img.crop((region.x, region.y, region.x2, region.y2))
        region_img = self._apply_algorithm(region_img, region.mode_algorithm)
        if region_img.mode == "RGBA" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGBA")
        if region_img.mode == "RGB" and (final_img.mode == "L" or final_img.mode == "1"):
            final_img = final_img.convert("RGB")
        if region_img.mode == "L" and final_img.mode == "1":
            final_img = final_img.convert("L")
        final_img.paste(region_img, (region.x, region.y, region.x2, region.y2))
        return final_img

    def apply_algorithm(self, img: Image, algorithm: Algorithm):
        
        if algorithm == Algorithm.NONE:
            return img
        else:
            return self.runners[algorithm](self, img)

    def _apply_algorithm_gray(self, img: Image):
        '''
        TODO: The default algorithm is probably optimized for
        photo images. This might not be the best option for
        scanned papers. Do more research.
        '''
        if img.mode == "1" or img.mode == "L":
            return img
        
        return img.convert("L")

    def _apply_algorithm_floyd_steinberg(self, img: Image):
        '''
        Floyd-Steinberg is the default for PIL
        '''
        if img.mode == "1":
            return img
        
        return img.convert("1")

    def _apply_threshold_algorithm(self, img: Image, algorithm: Algorithm):

        resolution = get_image_resolution(img)
        in_array = np.asarray(self._apply_algorithm_gray(img))
        if algorithm == Algorithm.OTSU:
            mask = threshold_otsu(in_array)
        elif algorithm == Algorithm.SAUVOLA:
            mask = threshold_sauvola(in_array, window_size=11)
        elif algorithm == Algorithm.NIBLACK:
            mask = threshold_niblack(in_array, window_size=11)
        else:
            raise Exception("Unknown threshold algorithm")
        out_array = in_array > mask
        img = Image.fromarray(out_array)
        img.info['dpi'] = (resolution, resolution)
        img.convert("1")
        return img
    
    def _apply_algorithm_quantization(self, img: Image) -> Image:
        """
        Uses the k-means algorithm to quantize the image
        """
        
        if img.mode != "RGB":
            img = img.convert("RGB")
        np_array = np.array(img)
        flattend = np.float32(np_array).reshape(-1,3)
        condition = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,20,1.0)
        ret,label,center = cv2.kmeans(flattend, 2 , None, condition,10,cv2.KMEANS_RANDOM_CENTERS)
        center = np.uint8(center)
        final_flattend = center[label.flatten()]
        final_img_array = final_flattend.reshape(np_array.shape)
        new_img = Image.fromarray(final_img_array)
        new_img.info['dpi'] = img.info['dpi']
        return new_img
    
    def _apply_algorithm_gray_on_white_text(self, img: Image) -> Image:

        if img.mode != "RGB":
            img = img.convert("RGB")

        mask = self._apply_algorithm_bw_quantization(img)
        mask = mask.convert("RGB")
        mask = mask.filter(ImageFilter.BLUR)

        np_img = np.array(img)
        np_mask = np.array(mask)
        red, green, blue = np_mask.T

        white_areas = (red == 255) & (green == 255) & (blue == 255)
        np_img[white_areas.T] = (255, 255, 255)

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img.convert("L")
    
    def _apply_algorithm_bw_quantization(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            white = colors[0][1] 
            black = colors[1][1]
        else: 
            white = colors[1][1] 
            black = colors[0][1]
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 3 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        white_areas = (red == white[0]) & (green == white[1]) & (blue == white[2])
        np_img[white_areas.T] = (255, 255, 255) # Transpose back needed
        black_areas = (red == black[0]) & (green == black[1]) & (blue == black[2])
        np_img[black_areas.T] = (0, 0, 0) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img.convert("1")
    
    def _apply_algorithm_color_paper(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            black = colors[1][1]
        else: 
            black = colors[0][1]
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 3 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        black_areas = (red == black[0]) & (green == black[1]) & (blue == black[2])
        np_img[black_areas.T] = (0, 0, 0) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img
    
    def _apply_algorithm_color_text_quantization(self, img: Image):
        
        quantized_img = self._apply_algorithm_quantization(img)
        colors = quantized_img.getcolors()
        sum0 = colors[0][1][0] + colors[0][1][1] + colors[0][1][2] 
        sum1 = colors[1][1][0] + colors[1][1][1] + colors[1][1][2]
        if sum1 < sum0:
            white = colors[0][1] 
        else: 
            white = colors[1][1] 
        
        assert(quantized_img.mode == "RGB")
        np_img = np.array(quantized_img)   # "data" is a height x width x 4 numpy array
        red, green, blue = np_img.T # Temporarily unpack the bands for readability

        # Replace white with red... (leaves alpha values alone...)
        white_areas = (red == white[0]) & (green == white[1]) & (blue == white[2])
        np_img[white_areas.T] = (255, 255, 255) # Transpose back needed

        final_img = Image.fromarray(np_img)
        final_img.info['dpi'] = img.info['dpi']
        
        return final_img

    def _apply_algorithm_white(self, img):
        
        return Image.new("1", img.size, 1)

@singleton
class PdfService:
    
    @inject
    def __init__(self, ocr_service: OCRService, finishing_service: FinishingService):

        self.ocr_service = ocr_service
        self.finishing_service = finishing_service
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
            if page.skip_page:
                continue
            image = self.finishing_service.create_finale_image(page)
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

    def export_pdf(self, project: Project, filename: str):
        
        self.pdf_service.create_pdf_file(project, filename)
