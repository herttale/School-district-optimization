
    
# the main optimization function

def main(districts_orig, blocks_dict_orig):    

    import numpy as np
    import statistics as st
    import random
    from classes import Block, SchoolDistr
    from copy import deepcopy
        
    current_best_cumul_zvalue = None
    current_best_distr_division = None
    current_best_curve = None
    all_optimization_curves = []
        
    for iteration in range(0,100): 
        
        print(iteration)
        districts = deepcopy(districts_orig)
        blocks_dict = deepcopy(blocks_dict_orig)
        
        # create a list for tracking the change in cumulative z-value
        cumulative_zvalues_list = []        
        # create a variable for tracking the iterations inside while-loop
        main_iteration = 0 
        # set the ceiling value for probability calculation (now it ranges from
            # 50 to 124 adding 0.75 on every iteration
        ceil = np.floor(0.075 * iteration * 10 + 50)
        
        # calculate the global mean and standard deviation for original 
            # districts' optimization values
        districts_values_list = []
        for key, item in districts.items():
            districts_values_list.append(item.optimization_value)
        global_mean = sum(districts_values_list)/len(districts)
        global_st_dev = np.std(districts_values_list, ddof = 0)
        
        while True:
            
            # calculate the current cumulative z-value
            cumulative_zvalue = 0
            for key, distr in districts.items():
                cumulative_zvalue += abs((distr.optimization_value - 
                                          global_mean)/global_st_dev)            
            cumulative_zvalues_list.append(cumulative_zvalue)
            
            # test whether the optimization can be terminated - if yes, return
                # optimized district division and corresponding optimization curve
            if main_iteration >= 12:   
                checkvalue = st.mean([cumulative_zvalues_list[main_iteration], 
                                      cumulative_zvalues_list[main_iteration-1], 
                                      cumulative_zvalues_list[main_iteration-2], 
                                      cumulative_zvalues_list[main_iteration-3]]) \
                                        - cumulative_zvalues_list[main_iteration]
                
                if round(checkvalue, 5) == 0 or main_iteration > 40:
                    break   
                              
            # increase iteration
            main_iteration += 1
            print("main_iteration round:", main_iteration, 
                  ', current cumulative z-value:', cumulative_zvalue)            
           
            # iterate the districts
            for key in list(districts.keys()):                
                # generate a random number for defining whether a best or a random 
                    # block will be chosen on this turn
                if ceil >= 50:
                    random_int = random.randint(0, ceil)
                else: 
                    random_int = 0
                    
                # check what blocks the district in turn touches
                neighbors = districts[key].touches_which(blocks_dict)
                # select best or random block based on random_int
                if random_int > 50:     
                    block_to_add = districts[key].select_random_block(neighbors, 
                                            districts)
                else:                    
                    block_to_add = districts[key].select_best_block(neighbors, 
                                            districts, global_mean, global_st_dev)    
                
                if block_to_add != None:
                    # remove block from its previous owner and update values
                    districts[block_to_add.school_id].remove_block(block_to_add)
                    districts[block_to_add.school_id].update_distr()
                
                    # add block to the new district
                    block_to_add.school_id = key
                    districts[key].add_block(block_to_add)
                    districts[key].update_distr()
            
            # decrease ceiling value
            ceil -= 5
    
        all_optimization_curves.append(cumulative_zvalues_list)
        
        if (current_best_cumul_zvalue == None or 
            cumulative_zvalue < current_best_cumul_zvalue): 
            current_best_cumul_zvalue = cumulative_zvalue
            current_best_distr_division = districts
            current_best_curve = cumulative_zvalues_list
    
    return({"current_best_distr_division":current_best_distr_division, 
                            "current_best_curve":current_best_curve}) 
    

