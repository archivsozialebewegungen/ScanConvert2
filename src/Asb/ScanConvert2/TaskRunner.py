'''
Created on 31.12.2022

This module separates the running of export tasks into a
worker thread so the user can work on and create more tasks
while the current tasks are running.

@author: michael
'''
from enum import Enum
import threading
import traceback

from injector import singleton, inject

from Asb.ScanConvert2.PictureDetector import PictureDetector
from Asb.ScanConvert2.ScanConvertDomain import Project
from Asb.ScanConvert2.ScanConvertServices import ProjectService


class TaskType(Enum):
    
    PDF_EXPORT = 0
    TIFF_EXPORT = 1
    PHOTO_DETECTION = 2

class JobDefinition():
    '''
    A simple container class wrapping the project, the output file / directory
    and the task type at hand
    '''
    
    def __init__(self, project: Project, task_type: TaskType,
                 pre_job_method=None,
                 post_job_method=None,
                 file_base: str=None):
        
        self.project = project
        self.task_type = task_type
        self.pre_job_method = pre_job_method
        self.post_job_method = post_job_method
        self.file_base = file_base
        
@singleton
class TaskManager():
    

    @inject
    def __init__(self, project_service: ProjectService,
                 photo_detector: PictureDetector):
        
        self.project_service = project_service
        self.photo_detector = photo_detector
        
        self.message_function = None
        
        self.unfinished_tasks = []
        self.finished_tasks = []
        self.worker_thread_running = False
    
    def add_task(self, job: JobDefinition):
        
        self.unfinished_tasks.append(job)
        self.message_function()
        if self.worker_thread_running:
            return
        thread = threading.Thread(target=self.run_jobs)
        thread.start()
            
    def run_job(self, job: JobDefinition):
        
        try:
            if job.pre_job_method is not None:
                job.pre_job_method()
            
            if job.task_type == TaskType.PDF_EXPORT:
                self.convert_to_pdf(job)
            if job.task_type == TaskType.TIFF_EXPORT:
                self.convert_to_tif(job)
            if job.task_type == TaskType.PHOTO_DETECTION:
                self.run_photo_detection(job)
            
            if job.post_job_method is not None:
                job.post_job_method()
        except Exception as e:
            # TODO: Show error somewhere
            print(e)
            print(traceback.format_exc())
        
    def run_jobs(self):
        
        self.worker_thread_running = True
        
        while len(self.unfinished_tasks) > 0:
            
            self.run_job(self.unfinished_tasks[0])
            self.finished_tasks.append(self.unfinished_tasks[0])
            del(self.unfinished_tasks[0])
            self.message_function()
        
        self.worker_thread_running = False
    
    def run_photo_detection(self, job: JobDefinition):
        
        pass
    
    def convert_to_tif(self, job: JobDefinition):
        
        raise Exception("Not yet implemented")
    
    def convert_to_pdf(self, job: JobDefinition):
        
        self.project_service.export_pdf(job.project, job.file_base)
