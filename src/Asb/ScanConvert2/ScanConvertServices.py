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

from PIL import Image, ImageColor
from PIL.TiffImagePlugin import ImageFileDirectory_v2
from injector import singleton, inject
import ocrmypdf
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from Asb.ScanConvert2.Algorithms import AlgorithmImplementations, Algorithm, \
    AlgorithmHelper
from Asb.ScanConvert2.OCR import OcrRunner, OCRLine, OCRPage, OCRWord
from Asb.ScanConvert2.ProjectGenerator import ProjectGenerator, SortType
from Asb.ScanConvert2.ScanConvertDomain import Project, Page, Region, DDFFile,\
    DDFFileType, ScanPart
from fitz.fitz import Document as PdfDocument
from exiftool.helper import ExifToolHelper
from Asb.ScanConvert2.CroppingService import CroppingService
from xml.dom.minidom import parseString, Document
import re

INVISIBLE = 3

class XMLGenerator(object):
    
    def write_document(self, doc, output_file_name):
        
        with open(output_file_name, "w") as output:
            output.write(doc.toprettyxml(indent="  "))


@singleton
class METSService(XMLGenerator):
    
    archive_file_offset = int((400.0 / 2.54) * 0.5)
    
    def export_mets_data(self, file_type: DDFFileType, project: Project, projectfiles, output_file_name):
        
        doc = self._create_mets_document(file_type, project, projectfiles)
        
        self._write_document(doc, output_file_name)
        
        ddf_file =  DDFFile(DDFFileType.METS, "00001", output_file_name)
        ddf_file.directory = file_type.directory()
        
        return ddf_file
    
    def _create_mets_document(self, file_type: DDFFileType, project: Project, projectfiles):

        doc = Document()
        mets_root = self._create_root_element(doc)
        doc.appendChild(mets_root)
        
        descriptive_metadata_element = self._create_descriptive_metadata_section(doc, project)
        mets_root.appendChild(descriptive_metadata_element)
        
        file_section = self._create_file_section(doc, file_type, projectfiles)
        mets_root.appendChild(file_section)
        
        structural_map = self._create_structural_map(doc, file_type, projectfiles, project)
        mets_root.appendChild(structural_map)
        
        return doc
        
    def _create_descriptive_metadata_section(self, document, project):
        
        # Boilerplate stuff
        dms_section = document.createElement("mets:dmdSec")
        dms_section.setAttribute("ID", "%s_dmds" % project.metadata.ddf_prefix)
        
        mdwrap_element = document.createElement("mets:mdWrap")
        mdwrap_element.setAttribute("MIMETYPE", "text/xml")
        mdwrap_element.setAttribute("MDTYPE", "MODS")
        dms_section.appendChild(mdwrap_element)
        
        xmldata_element = document.createElement("mets:xmlData")
        mdwrap_element.appendChild(xmldata_element)
        
        mods_element = document.createElement("mods:mods")
        mods_element.setAttribute("version", "2.3.1")
        xmldata_element.appendChild(mods_element)
        
        if project.metadata.title != "":
            title_info_element = document.createElement("mods:titleInfo")
            mods_element.appendChild(title_info_element)
            title_element = document.createElement("mods:title")
            title_info_element.appendChild(title_element)
            title_text_node = document.createTextNode(project.metadata.title)
            title_element.appendChild(title_text_node)
        
        if project.metadata.author != "":
            name_element = document.createElement("mods:name")
            name_element.setAttribute("type", "personal")
            mods_element.appendChild(name_element)
            name_part_element = document.createElement("mods:namePart")
            name_element.appendChild(name_part_element)
            name_text_node = document.createTextNode(project.metadata.author)
            name_part_element.appendChild(name_text_node)
            
        #resource_type_element = document.createElement("mods:typeOfResource")
        #xmldata_element.appendChild(resource_type_element)
        #resource_type_element.appendChild(document.createTextNode("text"))
        
        return dms_section
        
    def _create_structural_map(self, document, file_type, projectfiles, project, use_pointers=True):
        
        structural_map = document.createElement("mets:structMap")
        structural_map.setAttribute("TYPE", "PHYSICAL")
        document_div = document.createElement("mets:div")
        document_div.setAttribute("TYPE", project.metadata.mets_type)
        document_div.setAttribute("LABEL", project.metadata.title)
        structural_map.appendChild(document_div)

        page_divs = []
        no_of_pages = len(project.pages)
        for i in range(0, no_of_pages):
            page_div = document.createElement("mets:div")
            page_div.setAttribute("TYPE", "page")
            page_div.setAttribute("LABEL", "Seite %d von %d." % ((i + 1), no_of_pages))
            page_divs.append(page_div)
        
        self._add_file_pointers(document, page_divs, projectfiles, for_scans=file_type == DDFFileType.ARCHIVE)

        for page_div in page_divs:
            document_div.appendChild(page_div)
            
        return structural_map
    
    def _add_file_pointers(self, document, page_divs, projectfiles, for_scans=False):
        
        display_files = self._get_projectfiles_by_type(projectfiles, DDFFileType.DISPLAY)
        assert(len(display_files) == len(page_divs))
        
        for idx in range(0, len(page_divs)):
            page_div = page_divs[idx]
            display_file = display_files[idx]
            if for_scans:
                archive_file = self._get_archive_file_for_scan(display_file.img_object.scan, projectfiles)
            else:
                archive_file = None
            page_div.appendChild(self._create_file_pointer(document, display_file, archive_file))
                
    def _get_archive_file_for_scan(self, scan, projectfiles):
        
        for file in projectfiles:
            
            if file.file_type != DDFFileType.ARCHIVE:
                continue
            if file.img_object == scan:
                return file
               
    def _create_file_pointer(self, document, display_file, archive_file=None):

        file_pointer = document.createElement("mets:fptr")
        if archive_file is None:
            file_pointer.setAttribute("FILEID", display_file.file_id)
        else:
            file_pointer.appendChild(self._create_sequence_element(document, display_file, archive_file))
        
        return file_pointer
                
    def _create_sequence_element(self, document, display_file, archive_file):

        sequence = document.createElement("mets:seq")
        sequence.appendChild(self._create_area_element(document, display_file, archive_file))
        
        return sequence

    def _create_area_element(self, document, display_file, archive_file):

        area_coordinates = self._calculate_area_coordinates(display_file.img_object)
        area = document.createElement("mets:area")
        area.setAttribute("FILEID", archive_file.file_id)
        area.setAttribute("SHAPE", "RECT")
        area.setAttribute("COORDS", "(%d,%d,%d,%d)" % area_coordinates)
        
        return area
                
    def _calculate_area_coordinates(self, page):
        
        if page.scan_part == ScanPart.WHOLE:
            return (METSService.archive_file_offset,
                    METSService.archive_file_offset,
                    METSService.archive_file_offset + int(page.scan.width * (400.0 / page.scan.source_resolution)),
                    METSService.archive_file_offset + int(page.scan.height * (400.0 / page.scan.source_resolution)))
        elif page.scan_part == ScanPart.LEFT:
            return (METSService.archive_file_offset,
                    METSService.archive_file_offset,
                    METSService.archive_file_offset + int((page.scan.width / 2.0) * (400.0 / page.scan.source_resolution)),
                    METSService.archive_file_offset + int(page.scan.height * (400.0 / page.scan.source_resolution)))
        elif page.scan_part == ScanPart.RIGHT:
            return (METSService.archive_file_offset + int(page.scan.width / 2.0) + 1,
                    METSService.archive_file_offset,
                    METSService.archive_file_offset + int(page.scan.width * (400.0 / page.scan.source_resolution)),
                    METSService.archive_file_offset + int(page.scan.height * (400.0 / page.scan.source_resolution)))
        else:
            raise Exception("Unknown scan part %s " % page.scan_part.name)
    
    def _get_projectfiles_by_type(self, projectfiles, file_type):
        
        filtered = []
        for projectfile in projectfiles:
            if projectfile.file_type == file_type:
                filtered.append(projectfile)
        return filtered
        
    def _create_file_section(self, document, file_type, projectfiles):
        
        file_section = document.createElement("mets:fileSec")
        
        file_section.appendChild(self._create_file_group(document, file_type, projectfiles))
        
        return file_section
    
    def _create_file_group(self, document, file_type, projectfiles):
        
        group_element = document.createElement("mets:fileGrp")
        group_element.setAttribute("USE", file_type.description())
        
        for ddf_file in projectfiles:
            
            if ddf_file.file_type != file_type:
                continue
            
            file_element = document.createElement("mets:file")
            file_element.setAttribute("ID", ddf_file.file_id)
            file_element.setAttribute("MIMETYPE", ddf_file.mime_type)
            group_element.appendChild(file_element)
            
            location_element = document.createElement("mets:FLocat")
            location_element.setAttribute("xlink:href", ddf_file.basename)
            location_element.setAttribute("LOCTYPE", "URL")
            file_element.appendChild(location_element)

            file_element = document.createElement("mets:file")
            file_element.setAttribute("ID", ddf_file.alto_file_id)
            file_element.setAttribute("MIMETYPE", "application/xml")
            group_element.appendChild(file_element)
            
            location_element = document.createElement("mets:FLocat")
            location_element.setAttribute("xlink:href", ddf_file.alto_basename)
            location_element.setAttribute("LOCTYPE", "URL")
            file_element.appendChild(location_element)
        
        return group_element
    
                    
    def _create_root_element(self, document):
        
        mets_root = document.createElement("mets:mets")
        mets_root.setAttributeNS("mets:mets", "xmlns:mets", "http://www.loc.gov/METS/")
        mets_root.setAttributeNS("mets:mets", "xmlns:mods", "http://www.loc.gov/mods/v3")
        mets_root.setAttributeNS("mets:mets", "xmlns:xlink", "http://www.w3.org/1999/xlink")
        mets_root.setAttributeNS("mets:mets", "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        mets_root.setAttributeNS("mets:mets", "xsi:schemaLocation", "http://www.loc.gov/METS/\nhttp://www.loc.gov/standards/mets/mets.xsd http://www.loc.gov/mods/v3\nhttp://www.loc.gov/mods/v3/mods-3-1.xsd")

        return mets_root
    
    def _write_document(self, doc, output_file_name):
        
        with open(output_file_name, "w") as output:
            output.write(doc.toprettyxml(indent="  "))

@singleton
class IPTCService(object):
    
    SOURCE = "1IPTC:Source"
    CITY = "1IPTC:City"
    SPECIAL_INSTRUCTIONS = "1IPTC:SpecialInstructions"
    CATALOG_SETS = "1IPTC:CatalogSets"
    
    def write_iptc_tags(self, filename, tags):
        
        with ExifToolHelper() as exif_tool:
            exif_tool.set_tags([filename], tags, ["-P", "-overwrite_original"])
            
    def read_iptc_tags(self, filename):
        
        with ExifToolHelper() as exif_tool:
            meta_data = exif_tool.get_meatadata(filename)
            
        return meta_data            


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
            bbox_new = (line.bbox[3], -1 * line.bbox[2], line.bbox[1], -1 * line.bbox[0])
            line.bbox = bbox_new
            pdf.rotate(90)
            
        for word in line.words:
            pdf = self._write_word(word, pdf, line, page)
        
        if line.textangle == 90:
            pdf.rotate(270)
            
        return pdf
    
    def _write_word(self, word: OCRWord, pdf: Canvas, line: OCRLine, page: OCRPage) -> Canvas:

        if line.textangle == 90:
            bbox_new = (word.bbox[3], -1 * word.bbox[2], word.bbox[1], -1 * word.bbox[0])
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
        # rotation_angle = round(math.degrees(math.atan(abs(line.baseline_coefficients[0]))))
        # if line.baseline_coefficients[0] > 0:
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
class FinishingService(object):
    
    @inject
    def __init__(self, algorithm_implementations: AlgorithmImplementations,
                 algorithm_helper: AlgorithmHelper):
        
        self.algorithm_implementations = algorithm_implementations
        self.algorithm_helper = algorithm_helper
        
    def create_scaled_image(self, scan_or_page, target_resolution: int) -> Image:

        img = scan_or_page.get_raw_image()

        if scan_or_page.source_resolution != target_resolution:
            img = self.change_resolution(img, target_resolution / scan_or_page.source_resolution)
            img.info['dpi'] = (target_resolution, target_resolution)
    
        return img
    
    def create_final_image(self, page: Page, bg_colors: [], target_resolution: int) -> Image:
        
        img = page.get_raw_image()

        target_source_ratio = 1.0        
        if page.source_resolution != target_resolution:
            target_source_ratio = target_resolution / page.source_resolution
            img = self.change_resolution(img, target_source_ratio)
        
        bg_img = img.convert("RGB")
        bg_img, bg_color = self.algorithm_implementations[page.main_region.mode_algorithm].transform(bg_img, None)
        if bg_color is not None:
            # We might have had a page with similar colors already
            bg_img, bg_color, bg_colors = self._substitute_bg_color(bg_img, bg_color, bg_colors)
        final_img = self._apply_regions(page.sub_regions, bg_img, img, bg_color, target_source_ratio)
        return final_img, bg_colors

    def create_pdf_image(self, page: Page, target_resolution: int) -> Image:
        
        img = page.get_raw_image()

        target_source_ratio = 1.0        
        if page.source_resolution != target_resolution:
            target_source_ratio = target_resolution / page.source_resolution
            img = self.change_resolution(img, target_source_ratio)
        
        bg_img = img.convert("RGB")
        bg_img, bg_color = self.algorithm_implementations[Algorithm.OTSU].transform(bg_img, None)
        return bg_img

    def _substitute_bg_color(self, bg_img, bg_color, bg_colors):
        
        for color in bg_colors:
            if color == bg_color:
                return bg_img, bg_color, bg_colors
            if self.algorithm_helper.colors_are_similar(color, bg_color):
                return self.algorithm_helper.replace_color_with_color(bg_img, bg_color, color), color, bg_colors
        # There is a new background color that differs sufficiently from all the other background colors
        bg_colors.append(bg_color)
        return bg_img, bg_color, bg_colors

    def change_resolution(self, img: Image, target_source_ratio: float) -> Image:

        current_width, current_height = img.size
        new_width = int(current_width * target_source_ratio)
        new_height = int(current_height * target_source_ratio)

        resized_img = img.resize((new_width, new_height))
        new_dpi = img.info['dpi'][0] * target_source_ratio
        resized_img.info['dpi'] = (new_dpi, new_dpi)
        return resized_img
        
    def _apply_regions(self, regions: [], bg_img: Image, original_img: Image, bg_color: (), target_source_ratio: float) -> Image:
        
        final_img = bg_img.copy()
        for idx in range(0, len(regions)):
            final_img = self._apply_region(regions[idx], final_img, original_img, bg_color, target_source_ratio)
    
        return final_img
    
    def _apply_region(self, region: Region, final_img: Image, img: Image, bg_color, target_source_ratio) -> Image:
        
        region_img = img.crop((round(region.x * target_source_ratio),
                               round(region.y * target_source_ratio),
                               round(region.x2 * target_source_ratio),
                               round(region.y2 * target_source_ratio)))
        region_img, bg_color = self._apply_algorithm(region_img, region.mode_algorithm, bg_color)
        if final_img.mode == "1":
            if region_img.mode in ("L", "RGB"):
                final_img = final_img.convert(region_img.mode)
        elif final_img.mode == "L":
            if region_img.mode == "RGB":
                final_img = final_img.convert(region_img.mode)
             
        final_img.paste(region_img, (round(region.x * target_source_ratio),
                                     round(region.y * target_source_ratio),
                                     round(region.x2 * target_source_ratio),
                                     round(region.y2 * target_source_ratio)))
        return final_img

    def _apply_algorithm(self, img: Image, algorithm: Algorithm, bg_color):
                
        return self.algorithm_implementations[algorithm].transform(img, bg_color)

    def _get_bg_color(self, algorithm: Algorithm, img: Image, mode):
                
        return self.algorithm_implementations[algorithm].get_bg_color(img, mode)


@singleton
class PdfService:
    
    @inject
    def __init__(self,
                 ocr_service: OCRService,
                 finishing_service: FinishingService,
                 algorithm_helper: AlgorithmHelper):

        self.ocr_service = ocr_service
        self.finishing_service = finishing_service
        self.algorithm_helper = algorithm_helper
    
    def create_pdf_file(self, project: Project, filebase: str, stupid_ddf_pdf: bool=False):
   
        bg_colors = []
   
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

                if stupid_ddf_pdf: 
                    image = page.get_raw_image()
                else:
                    image, new_bg_colors = self.finishing_service.create_final_image(page, bg_colors, project.project_properties.pdf_resolution)
                    if project.project_properties.normalize_background_colors:
                        bg_colors = new_bg_colors
                width_in_dots, height_in_dots = image.size
            
                page_width = width_in_dots * 72 / project.project_properties.pdf_resolution
                page_height = height_in_dots * 72 / project.project_properties.pdf_resolution
            
                pdf.setPageSize((width_in_dots * inch / project.project_properties.pdf_resolution,
                                 height_in_dots * inch / project.project_properties.pdf_resolution))

                img_stream = io.BytesIO()
                # if image.mode == "1":
                image.save(img_stream, format='png')
                # else:
                # image.save(img_stream, format='jpeg2000', quality=65, optimize=True)
                img_stream.seek(0)
                img_reader = ImageReader(img_stream)
                pdf.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
                if project.project_properties.run_ocr:
                    pdf = self.ocr_service.add_ocrresult_to_pdf(self.finishing_service.create_pdf_image(page, project.project_properties.pdf_resolution), pdf, project.project_properties.ocr_lang)
                pdf.showPage()
        
            pdf.save()
            # Convert to pdfa and optimize graphics
            if project.project_properties.create_pdfa:
                # ocrmypdf.configure_logging(verbosity=Verbosity.quiet)
                ocrmypdf_temp_file = os.path.join(temp_dir, "ocrmypdf_output.pdf")
                ocrmypdf.ocr(temp_file, ocrmypdf_temp_file, skip_text=True)
                #document = PdfDocument(ocrmypdf_temp_file)
                #document.set_metadata(project.metadata.as_pdf_metadata_dict())
                #document.save(self._get_file_name(filebase))
                shutil.copy(ocrmypdf_temp_file, self._get_file_name(filebase))
            else:
                shutil.copy(temp_file, self._get_file_name(filebase))
        
    def _get_file_name(self, filebase: str):
        
        if filebase[-4:] == ".pdf":
            return filebase
        return filebase + ".pdf"


class ExportService(object):

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
    
    def _get_file_name(self, filebase: str, suffix: str):
        
        if filebase[-4:] == ".%s" % suffix:
            return filebase
        return filebase + ".%s" % suffix

    def _build_tiff_metadata(self, project: Project):

        tiff_meta_data = ImageFileDirectory_v2()
        tiff_meta_data[self.artist_tag] = self.utf8_to_ascii(project.metadata.author)
        tiff_meta_data[self.document_name_tag] = self.utf8_to_ascii(project.metadata.title)
        tiff_meta_data[self.image_description] = self.utf8_to_ascii("%s\n\nSchlagworte: %s" % (project.metadata.subject, project.metadata.keywords))
        tiff_meta_data[self.x_resolution] = project.project_properties.tif_resolution
        tiff_meta_data[self.y_resolution] = project.project_properties.tif_resolution
        tiff_meta_data[self.resolution_unit] = self.inch_resolution_unit
        
        return tiff_meta_data
    
    def utf8_to_ascii(self, string: str):
        
        for utf8, ascii_string in self.replacements.items():
            string = string.replace(utf8, ascii_string)
        return string


@singleton
class TiffService(ExportService):
        
    @inject
    def __init__(self, finishing_service: FinishingService):
    
        self.finishing_service = finishing_service
        
    def create_tiff_file_archive(self, project: Project, filebase):
        
        zipfile = ZipFile(self._get_file_name(filebase, "zip"), mode='w')
        tiff_meta_data = self._build_tiff_metadata(project)
        
        with tempfile.TemporaryDirectory() as tempdir:

            no_of_pages = len(project.pages)
            
            counter = 0
            for page in project.pages:
                counter += 1
                tiff_meta_data[self.page_name_tag] = "Seite %d von %d des Dokuments" % (counter, no_of_pages)
                page_name = "Seite%04d.tif" % counter
                file_name = os.path.join(tempdir, page_name)
                img = self.finishing_service.create_scaled_image(page, project.project_properties.tif_resolution)
                img.save(file_name, tiffinfo=tiff_meta_data, compression="tiff_lzw")
                zipfile.write(file_name, page_name)
            
            readme_file = os.path.join(tempdir, "readme.txt")
            with open(readme_file, 'w') as readme:
                readme.write("Information zu diesem ZIP Archiv\n================================\n")
                readme.write("Titel: %s\n" % project.metadata.title)
                readme.write("Anzahl der Seiten/Dateien: %d\n" % no_of_pages)
                readme.write("Autor:in: %s\n\n" % project.metadata.author)
                readme.write("Sonstige Informationen:\n%s\n\n" % project.metadata.subject)
                readme.write("Schlagwor += te: %s\n\n" % project.metadata.keywords)
                readme.write("Dieses ZIP-Archiv enthält Digitalisatsdateien, die mit dem\n")
                readme.write("Scan Konvertierungsprogramm des Archivs Soziale Bewegungen e.V.\n")
                readme.write("Freiburg erstellt und zusammengepackt wurden.\n")
                readme.write("Das Programm kann hier heruntergeladen werden:\n")
                readme.write("https://github.com/archivsozialebewegungen/ScanConvert2\n")
            zipfile.write(readme_file, "readme.txt")
                
            zipfile.close()


@singleton
class DDFService(ExportService, XMLGenerator):
    
    @inject
    def __init__(self,
                 finishing_service: FinishingService,
                 iptc_service: IPTCService,
                 cropping_service: CroppingService,
                 ocr_runner: OcrRunner,
                 pdf_service: PdfService,
                 mets_service: METSService
                 ):
        
        self.finishing_service = finishing_service
        self.iptc_service = iptc_service
        self.cropping_service = cropping_service
        self.ocr_runner = ocr_runner
        self.pdf_service = pdf_service
        self.mets_service = mets_service
    
    def create_ddf_file_archive(self, project: Project, filebase):
        
        with tempfile.TemporaryDirectory() as tempdir:

            projectfiles = self._write_scans(project, tempdir)
            projectfiles += self._write_pages(project, tempdir)

            pdf_file = self._write_stupid_pdf(project, tempdir)
            self._join_alto_files(projectfiles, "%s.alto" % pdf_file.temp_file_name)
            projectfiles.append(pdf_file)
            
            mets_file_name = os.path.join(tempdir, "%s_display.mets" % project.metadata.ddf_prefix)
            mets_file = self.mets_service.export_mets_data(DDFFileType.DISPLAY, project, projectfiles, mets_file_name)
            projectfiles.append(mets_file)
            
            mets_file_name = os.path.join(tempdir, "%s_archive.mets" % project.metadata.ddf_prefix)
            mets_file = self.mets_service.export_mets_data(DDFFileType.ARCHIVE, project, projectfiles, mets_file_name)
            projectfiles.append(mets_file)
            
            ddf_xml_file_name = os.path.join(tempdir, "%s_ddf.xml" % project.metadata.ddf_prefix)
            ddf_xml_file = self._write_ddf_xml(project, ddf_xml_file_name)
            projectfiles.append(ddf_xml_file)

            self._create_zip_file(filebase, projectfiles)
    
    def _create_zip_file(self, filebase, projectfiles):

        zipfile = ZipFile(self._get_file_name(filebase, "zip"), mode='w')
        for ddf_file in projectfiles:
            zipfile.write(ddf_file.temp_file_name, "%s/%s" % (ddf_file.directory, os.path.basename(ddf_file.temp_file_name)))
            try:
                zipfile.write(ddf_file.alto_file_name, "%s/%s" % (ddf_file.directory, os.path.basename(ddf_file.alto_file_name)))
            except:
                pass
        zipfile.close()
        
    def _write_scans(self, project, tempdir):

            projectfiles = []        
            no_of_scans = len(project.pages)
            file_prefix = project.metadata.ddf_prefix
            
            tiff_meta_data = self._build_tiff_metadata(project)
            tiff_meta_data[self.x_resolution] = 400
            tiff_meta_data[self.y_resolution] = 400

            iptc_tags = self._build_iptc_metadata(project)
            
            counter = 0
            for scan in project.scans:
                
                counter += 1
                
                tiff_meta_data[self.page_name_tag] = "Scan %d von %d" % (counter, no_of_scans)
                
                if project.project_properties.sort_type == SortType.SHEET:
                    sequence_no = "%05d" % int(((counter - 1) / 2) + 1)
                    if counter % 2 == 0:
                        sequence_no += "verso"
                    else:
                        sequence_no += "recto"
                elif project.project_properties.sort_type == SortType.SHEET_ALL_FRONT_ALL_BACK:
                    sheet_no = counter
                    if counter > no_of_scans / 2:
                        sheet_no = counter - (no_of_scans / 2)
                        sequence_no = "%05verso" % sheet_no
                    else: 
                        sequence_no = "%05recto" % sheet_no
                else:
                    sequence_no = "%05d" % counter
                scan_file_name = "%s%s.tif" % (file_prefix, sequence_no)
                file_name = os.path.join(tempdir, scan_file_name)
                ddf_file = DDFFile(DDFFileType.ARCHIVE, sequence_no, file_name)
                ddf_file.img_object = scan
                projectfiles.append(ddf_file)

                img = self.finishing_service.create_scaled_image(scan, 400)
                transposition = self.get_transposition(project, counter)
                if transposition is not None:
                    img = img.transpose(transposition)
                if counter == 1:
                    img = self.add_color_card(img)
                img = self.add_black_border(img)
                img.save(file_name, tiffinfo=tiff_meta_data, compression=None)
                self._write_alto_file(img, ddf_file.alto_file_name, project.project_properties.ocr_lang)
                self.iptc_service.write_iptc_tags(file_name, iptc_tags)

            return projectfiles

    def _write_pages(self, project, tempdir):

            projectfiles = []
                    
            no_of_pages = len(project.pages)
            file_prefix = project.metadata.ddf_prefix
            # TODO: Create Metadata
            
            iptc_tags = self._build_iptc_metadata(project)
            
            counter = 0
            for page in project.pages:
                counter += 1
                
                scan_file_name = "%s%05d.jpg" % (file_prefix, counter)
                file_name = os.path.join(tempdir, scan_file_name)
                ddf_file = DDFFile(DDFFileType.DISPLAY, counter, file_name)
                ddf_file.img_object = page
                projectfiles.append(ddf_file)

                img = self.finishing_service.create_scaled_image(page, 300)
                self._write_alto_file(img, ddf_file.alto_file_name, project.project_properties.ocr_lang)
                img.save(file_name, quality=95, optimize=True)
                self.iptc_service.write_iptc_tags(file_name, iptc_tags)
    
            return projectfiles
        
    def _write_ddf_xml(self, project, output_file_name):
        
        doc = Document()
        
        freiburg_element = doc.createElement("freiburg")
        doc.appendChild(freiburg_element)

        datensatz_element = doc.createElement("datensatz")
        freiburg_element.appendChild(datensatz_element)
        
        format_element = doc.createElement("format")
        format_element_text = doc.createTextNode(project.metadata.ddf_type)
        format_element.appendChild(format_element_text)
        datensatz_element.appendChild(format_element)

        subformat_element = doc.createElement("unterangabe_zu_format")
        subformat_element_text = doc.createTextNode(project.metadata.ddf_subtype)
        subformat_element.appendChild(subformat_element_text)
        datensatz_element.appendChild(subformat_element)
        
        title_element = doc.createElement("titel")
        title_element_text = doc.createTextNode(project.metadata.title)
        title_element.appendChild(title_element_text)
        datensatz_element.appendChild(title_element)

        author_element = doc.createElement("author")
        author_element_text = doc.createTextNode(project.metadata.author)
        author_element.appendChild(author_element_text)
        datensatz_element.appendChild(author_element)

        publication_year_element = doc.createElement("displayPublishDate")
        publication_year_element_text = doc.createTextNode(project.metadata.publication_year)
        publication_year_element.appendChild(publication_year_element_text)
        datensatz_element.appendChild(publication_year_element)

        publication_city_element = doc.createElement("placeOfPublication")
        publication_city_element_text = doc.createTextNode(project.metadata.publication_city)
        publication_city_element.appendChild(publication_city_element_text)
        datensatz_element.appendChild(publication_city_element)

        publisher_element = doc.createElement("publisher")
        publisher_element_text = doc.createTextNode(project.metadata.publisher)
        publisher_element.appendChild(publisher_element_text)
        datensatz_element.appendChild(publisher_element)

        publication_language_element = doc.createElement("language")
        publication_language_element_text = doc.createTextNode(project.metadata.publication_language)
        publication_language_element.appendChild(publication_language_element_text)
        datensatz_element.appendChild(publication_language_element)

        keywords_element = doc.createElement("schlagwort")
        keywords_element_text = doc.createTextNode(project.metadata.keywords)
        keywords_element.appendChild(keywords_element_text)
        datensatz_element.appendChild(keywords_element)

        signature_element = doc.createElement("signatur")
        signature_element_text = doc.createTextNode(project.metadata.signatur)
        signature_element.appendChild(signature_element_text)
        signature_element.appendChild(signature_element)

        self.write_document(doc, output_file_name)

        return DDFFile(DDFFileType.DDFXML, None, output_file_name)
        
    def _write_alto_file(self, img, file_name, ocr_lang):
        
        alto_dom = self.ocr_runner.run_tesseract_for_alto(img, ocr_lang)
        file = open(file_name, "w")
        file.write(alto_dom.toprettyxml())
        file.close()

    def _join_alto_files(self, projectfiles, file_name):
        
        id_re = re.compile(r'ID="([a-z]+)_')
        
        output = open(file_name, "w")
        
        alto_files = self._fetch_page_alto_files(projectfiles)
        with open(alto_files[0], 'r') as file:
            alto1_as_string = file.read()
            main_dom = parseString(re.sub(id_re, r'ID="\1_1_', alto1_as_string))
        
        layouts = main_dom.getElementsByTagName("Layout")
        layout = layouts[0]
        
        counter = 1
        for alto_file in alto_files[1:]:
            counter += 1
            with open(alto_file, 'r') as file:
                alto_as_string = file.read()
                dom = parseString(re.sub(id_re, r'ID="\1_%d_' % counter, alto_as_string))
            pages = dom.getElementsByTagName("Page")
            layout.childNodes.append(pages[0])
        
        output.write(main_dom.toprettyxml())
        output.close()
        
        return file_name
        
    def _fetch_page_alto_files(self, projectfiles):
        
        page_alto_files = []
        for ddf_file in projectfiles:
            if ddf_file.file_type == DDFFileType.DISPLAY:
                page_alto_files.append(ddf_file.alto_file_name)
        return page_alto_files 
                
    def _write_stupid_pdf(self, project, tempdir):
        
        pdf_name = project.metadata.ddf_prefix + "00001.pdf"
        output_name = os.path.join(tempdir, pdf_name)
        self.pdf_service.create_pdf_file(project, output_name, stupid_ddf_pdf=True)
        
        return DDFFile(DDFFileType.PDF, 1, output_name)
    
    def _build_iptc_metadata(self, project: Project):

        return {self.iptc_service.SOURCE: project.metadata.source,
                self.iptc_service.CATALOG_SETS: project.metadata.signatur,
                self.iptc_service.CITY: project.metadata.city,
                self.iptc_service.SPECIAL_INSTRUCTIONS: project.metadata.special_instructions}
            
    def get_transposition(self, project, scan_no):
            
        if project.project_properties.rotation_alternating and scan_no % 2 == 1:
            if project.project_properties.scan_rotation == 0:
                return Image.ROTATE_180
            if project.project_properties.scan_rotation == 90:
                return Image.ROTATE_270
            if project.project_properties.scan_rotation == 180:
                return None
            if project.project_properties.scan_rotation == 270:
                return Image.ROTATE_90
        else:
            if project.project_properties.scan_rotation == 0:
                return None
            if project.project_properties.scan_rotation == 90:
                return Image.ROTATE_90
            if project.project_properties.scan_rotation == 180:
                return Image.ROTATE_180
            if project.project_properties.scan_rotation == 270:
                return Image.ROTATE_270
            
    def add_color_card(self, img):
        
        color_card_filename = os.path.join(os.path.dirname(__file__), "Data", "Farbkarte.tif")
        color_card = Image.open(color_card_filename)
        color_card = self.finishing_service.change_resolution(color_card, float(img.info['dpi'][0]) / float(color_card.info['dpi'][0]))
        
        new_width = img.width + color_card.width
        new_img = Image.new(img.mode, (new_width, img.height), ImageColor.getcolor("black", img.mode))
        new_img.info['dpi'] = img.info['dpi']
        new_img.paste(img, (0, 0))
        new_img.paste(color_card, (img.width + 1, 0))
        
        return new_img
            
    def add_black_border(self, img):
        
        additional_pixels = int(img.info['dpi'][0] / 2.54)
        new_width = img.width + additional_pixels
        new_height = img.height + additional_pixels
        new_img = Image.new(img.mode, (new_width, new_height), ImageColor.getcolor("black", img.mode))
        new_img.paste(img, (int(additional_pixels / 2), int(additional_pixels / 2)))
        return new_img


@singleton    
class ProjectService(object):
    
    @inject
    def __init__(self,
                 project_generator: ProjectGenerator,
                 pdf_service: PdfService,
                 ddf_service: DDFService,
                 tiff_service: TiffService,
                 cropping_service: CroppingService):
        
        self.project_generator = project_generator
        self.pdf_service = pdf_service
        self.ddf_service = ddf_service
        self.tiff_service = tiff_service
        self.cropping_service = cropping_service
        
    def create_project(self,
                    scans: [],
                    pages_per_scan: int,
                    sort_type: SortType,
                    scan_rotation: int,
                    rotation_alternating: bool,
                    cropping: bool) -> Project:
        
        if cropping:
            for scan in scans:
                scan.add_cropping_information(self.cropping_service.get_cropping_information(scan.filename))

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

    def export_ddf(self, project: Project, filename: str):
        
        self.ddf_service.create_ddf_file_archive(project, filename)
