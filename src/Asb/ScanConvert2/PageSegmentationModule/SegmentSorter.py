'''
Created on 07.04.2023

@author: michael
'''
from Asb.ScanConvert2.PageSegmentationModule.Domain import ObjectWithBoundingBox,\
    Segment
from injector import singleton

class Block(ObjectWithBoundingBox):

    def __init__(self, bb_object):

        super().__init__(bb_object.bounding_box.copy())
        self.bb_objects = [bb_object]
        
    def add(self, bb_object):
        
        self.bb_objects.append(bb_object)
        self.bounding_box.merge(bb_object.bounding_box)

    def _get_segments(self):
        segments = []
        for bb_object in self.bb_objects:
            if isinstance(bb_object, Block):
                segments += bb_object._get_segments()
            else:
                assert(isinstance(bb_object, Segment))
                segments.append(bb_object)
        return segments

@singleton
class SegmentSorterService(object):

    def sort_segments(self, segments):
        
        blocks = self._merge_into_blocks(segments)
        no_of_blocks = len(blocks)

        blocks = self._merge_into_blocks(blocks)
        while len(blocks) != no_of_blocks:
            no_of_blocks = len(blocks)
            blocks = self._merge_into_blocks(blocks)
        
        return self._get_segments(blocks)
     
    def _get_segments(self, blocks):
        
        segments = []
        for block in blocks:
            if isinstance(block.bb_objects[0], Block):
                segments = segments + self._get_segments(block.bb_objects)
            else:
                segments = segments + block.bb_objects
    
        for segment in segments:
            assert(isinstance(segment, Segment))
     
        return segments


    def _merge_into_blocks(self, bb_objects):
    
        bb_objects.sort()
        blocks = []
        while len(bb_objects) > 0:
            current_block = Block(bb_objects.pop(0))
            blocks.append(current_block)
            mergable_bb_object = self.find_mergable_bb_object(current_block, blocks, bb_objects)
            while mergable_bb_object is not None:
                current_block.add(mergable_bb_object)
                bb_objects.remove(mergable_bb_object)
                mergable_bb_object = self.find_mergable_bb_object(current_block, blocks, bb_objects)
        
        return blocks

    def find_mergable_bb_object(self, current_block, blocks, bb_objects):
        
        for bb_object in bb_objects:
            if self.bb_object_can_be_added_to_block(current_block, bb_object, blocks + bb_objects):
                return bb_object
        return None
        
        
    def bb_object_can_be_added_to_block(self, block, bb_object, bb_objects):
        '''
        A bb_object may only be added to a block, if the resulting
        bounding box does not intersect with other bb_objects or the remaining
        bb_objects.
        '''
                
        merged_bounding_box = block.bounding_box.copy()
        merged_bounding_box.merge(bb_object.bounding_box)
        
        for other_bb_object in bb_objects:
            if other_bb_object.bounding_box == block.bounding_box or\
                other_bb_object.bounding_box == bb_object.bounding_box:
                # Obviously the two source bounding boxes intersect always
                continue
            if merged_bounding_box.intersects_with(other_bb_object.bounding_box):
                return False

        return True
