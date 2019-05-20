#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  7 10:51:21 2018
@author: hertta
"""
from shapely.ops import cascaded_union
from copy import deepcopy
import random
from shapely.geometry import LineString

class SchoolDistr: 
    """ The class representing the school districts """
       
    def __init__(self, school_id, blocks, td_matrix):
        
        # class attribute 1: the school id number
        self.school_id = school_id
        # class attribute 2: the blocks belonging to the district (as a dict, 
            # with keys corresponding to the td_matrix keys).
        self.blocks = blocks
        # class attribute 3: distance matrix (as a dict, with keys 
            # corresponding to the blocks keys).
        self.td_matrix = td_matrix        
        # class attribute 3: the geometry of the district (shapely polygon) 
        self.geometry = None
        # class attribute 4: the maximum allowed distance from block to the 
            # district's school
        self.max_distance = None
        # class attribute 5: the amount of 7-year-olds living inside the 
            # district
        self.students = None
        # class attribute 6: the maximum amount of 7-year-olds that the 
            # district can host
        self.student_limit = None
        # class attribute 7: the current value of the optimization parameter
        self.optimization_value = None
        # function call: initiate district attributes
        self.initiate_distr_attrs()

    # Method for initializing attributes 
    def initiate_distr_attrs(self):
        self.geometry = self.calculate_geometry()
        self.max_distance = self.calculate_max_distance()
        self.students = self.calculate_student_base()
        self.student_limit = self.students*1.20
        self.optimization_value = self.calculate_optimization_value()

    # Method for updating attributes
    def update_distr(self):
        self.geometry = self.calculate_geometry()       
        self.students = self.calculate_student_base()
        self.optimization_value = self.calculate_optimization_value()    

    # Method for calculating the district's geometry as cascaded union of the 
        # block geometries
    def calculate_geometry(self):
        geom_list = []
        for key, block in self.blocks.items():
            geom_list.append(block.geometry)
        return cascaded_union(geom_list)     
        
    # Method for calculating the district's maximum distance constraint. The 
        # travel time data must not include infinite distance values.
    def calculate_max_distance(self):
        maxt = 0
        for key, block in self.blocks.items(): 
            ttime = self.td_matrix[key]['walk_d']
            if ttime > maxt:
                maxt = ttime
        return maxt * 1.20
        
    # Method for calculating the current value of the optimization parameter
    def calculate_optimization_value(self):
        majority_pop = 0
        minority_pop = 0
        for key, block in self.blocks.items():
            majority_pop += block.lang_majority
            minority_pop += block.lang_other       
        return minority_pop/(minority_pop + majority_pop)      

    # Method for calculating the current amount of 7-year-olds living 
        # inside the district
    def calculate_student_base(self):
        student_sum = 0
        for key, block in self.blocks.items(): 
            student_sum += block.student_base
        return student_sum
              
    # Method for calculating the district's neighbourhood: which blocks
        # the district shares a line segment with
    def touches_which(self, blocks_dict):
        neighbors = []        
        for key, block in blocks_dict.items():
            if type(self.geometry.intersection(block.geometry)) == LineString:
                if key not in self.blocks:
                    neighbors.append(block)
        return neighbors
        
    # Method for calculating whether a block is too far for adoption
        # Returns True if the block is too far
    def is_too_far(self, block):
        dist = self.td_matrix[block.block_id]['walk_d']
        return dist > self.max_distance

    # Method for adopting a selected block 
    def add_block(self, block):
        if block == None:
            return
        else:
            block.school_id = self.school_id
            self.blocks[block.block_id] = block
                  
    # Method for removing an adopted block 
    def remove_block(self, block):
        if block == None:
            return
        else:
            del self.blocks[block.block_id]

    # A method for testing if adopting a block would break another district's 
        # contiguity. Returns True if contiguity would break.
    def break_contiguity(self, block):
        blocks_copy = deepcopy(self.blocks)
        
        geom_list = []
        for key, item in blocks_copy.items():
            geom_list.append(item.geometry)
        geom1 = cascaded_union(geom_list)
        del blocks_copy[block.block_id]
        
        geom_list = []
        for key, item in blocks_copy.items():
            geom_list.append(item.geometry)
        geom2 = cascaded_union(geom_list)
        
        return type(geom1) != type(geom2) 

    # A method for selecting the best block in neighbourhood
    def select_best_block(self, blockset, districts, global_mean, 
                          global_st_dev):
        majority_pop = 0
        minority_pop= 0
        
        for key, value in self.blocks.items(): 
            majority_pop += value.lang_majority
            minority_pop += value.lang_other
        
        best_block = None
        
        for block in blockset:
            # test for rule 2
            if block.contains_school == False:
               # test for rule 3
                if (block.student_base + self.students) <= self.student_limit:
                    # test for rule 4
                    if self.is_too_far(block) == False:
                        current_district = districts[block.school_id]
                        # test for rule 5
                        if current_district.break_contiguity(block) == False:
                            # calculate specs for the block's current district
                            current_district_majority_pop = 0
                            current_district_minority_pop= 0
                            
                            for key, value in current_district.blocks.items():
                                current_district_majority_pop += \
                                        value.lang_majority
                                current_district_minority_pop += \
                                        value.lang_other
                                
                            current_d_new_value = ((current_district_minority_pop 
                                                    - block.lang_other)/ 
                                                    (current_district_minority_pop 
                                                     - block.lang_other + 
                                                     current_district_majority_pop 
                                                     - block.lang_majority))
                            current_d_current_value = ((current_district_minority_pop)/
                                                       (current_district_minority_pop 
                                                       + current_district_majority_pop))
                            
                            # test the adoption outcome in relation to current state
                            if best_block == None:       
                                own_new_value1 = ((minority_pop + block.lang_other)/ 
                                                  (minority_pop + block.lang_other + 
                                                   majority_pop + block.lang_majority))
                                
                                # test for the rule 6
                                if (abs(current_d_new_value - global_mean) <= 
                                    abs(current_d_current_value - global_mean) or 
                                    abs((current_d_current_value - global_mean) - 
                                        (self.optimization_value - global_mean)) > 
                                        abs((current_d_new_value - global_mean) - 
                                            (own_new_value1 - global_mean))): 
                                     
                                     if (abs(own_new_value1 - global_mean) < 
                                         abs(self.optimization_value - global_mean)):
                                         best_block = block
                            
                            # test the adoption outcome in relation to the current best_block  
                            else:
                                
                                own_new_value2 = ((minority_pop + block.lang_other)/
                                                  (minority_pop + block.lang_other + 
                                                   majority_pop + block.lang_majority))
                                current_best = ((minority_pop + best_block.lang_other)/
                                                (minority_pop + best_block.lang_other +
                                                 majority_pop + best_block.lang_majority))
                    
                                # test for the rule 6                               
                                if (abs(current_d_new_value - global_mean) <= 
                                       abs(current_d_current_value - global_mean) or 
                                       abs((current_d_current_value - global_mean) -
                                           (self.optimization_value - global_mean)) > 
                                           abs((current_d_new_value - global_mean) - 
                                               (own_new_value1 - global_mean))):
                                    
                                    if (abs(own_new_value2 - global_mean) < 
                                        abs(current_best - global_mean)):       
                                        best_block = block 
        # return the best block
        return best_block                         

    # A method for selecting a random block in neighbourhood
    def select_random_block(self, blockset, districts): 
        blocklist = []
        for block in blockset: 
            # test for rule 2
            if block.contains_school == False:
                # test for rule 3
                if (block.student_base + self.students) <= self.student_limit:
                    # test for rule 4
                    if self.is_too_far(block) == False:
                        current_district = districts[block.school_id]
                        # test for rule 5
                        if current_district.break_contiguity(block) == False:
                            blocklist.append(block)
        
        if len(blocklist) > 0:
            # generate a random number for selecting a block               
            randomindx = random.randint(0,len(blocklist)-1)
            # return a random block according to the random number generated
            return blocklist[randomindx]

class Block:
    """ The class representing the residential blocks """    
    def __init__(self, geometry, block_id, lang_majority, lang_other, student_base, 
                 school_id, contains_school):

        # class attribute 1: the geometry of the block (shapely polygon)
        self.geometry = geometry
        # class attribute 2: block id
        self.block_id = block_id
        # class attribute 3: the amount of population with Finnish or Swedish as 
            # their mother tongue
        self.lang_majority = lang_majority
        # class attribute 4: the amount of population with other languages than Finnish 
            # or Swedish as their mother tongue
        self.lang_other = lang_other
        # class attribute 5: the amount of 7-year-olds living in the block
        self.student_base = student_base
        # class attribute 6: the id of the school district the block currently 
            # belongs to
        self.school_id = school_id
        # class attribute 7: True if the block contains a school, otherwise False
        self.contains_school = contains_school