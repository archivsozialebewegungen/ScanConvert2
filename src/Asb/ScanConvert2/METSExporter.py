'''
Created on 02.02.2024

@author: michael
'''
from Asb.ScanConvert2.ScanConvertDomain import Project
from zipfile import ZipFile

class METSZipExporter(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def exportProjectRawScans(self, project: Project, zipfilename:str=None):
        
        pass
    
    def exportProjectPages(self, project:Project,  zipfilename:str= None):
        
        pass
    
    def _create_zipfile(self, project:Project, zipfilename:str):
        
        if zipfilename is None:
            filename = project.proposed_zip_file
        else:
            filename = zipfilename
            
        return ZipFile(filename, mode='w')
        
    
        
        