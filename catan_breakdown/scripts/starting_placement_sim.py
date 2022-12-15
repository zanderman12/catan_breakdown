# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 15:56:16 2022

@author: alext
"""

import numpy as np
import pandas as pd
import random
import itertools

def create_board():
    tile_types = ['desert', 'sheep', 'sheep', 'sheep', 'sheep',
                  'wood', 'wood', 'wood', 'wood', 'wheat',
                  'wheat', 'wheat', 'wheat', 'brick', 'brick',
                  'brick', 'ore', 'ore', 'ore']
    tile_nums = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
    
    random.shuffle(tile_types)
    random.shuffle(tile_nums)
    
    tile_dict = {}
    num_dict = {}
    
    num_counter = 0
    for i, t in enumerate(tile_types):
        
        if t != 'desert':
            tile_num = tile_nums[num_counter]
            num_counter += 1
        else:
            tile_num = 0
        
        tile_dict[i] = {}
        tile_dict[i]['resource'] = t
        tile_dict[i]['num'] = tile_num
        
        if tile_num not in num_dict.keys():
            num_dict[tile_num] = [i]
        else:
            num_dict[tile_num].append(i)
            
    return tile_dict, num_dict

def res_availability(tile_dict, pipdict):
    res_availability_dict = {'wood': 0,
                             'brick': 0,
                             'ore': 0,
                             'sheep': 0,
                             'wheat': 0}
    
    for t in tile_dict.values():
        if t['resource'] != 'desert':
            res_availability_dict[t['resource']] += pipdict[t['num']]
            
    return res_availability_dict
        

def play_one_game():
    
    settlement_dict = {1: {'tiles':[0],
                           'port': None},
                       2: {'tiles':[0],
                           'port': None},
                       3: {'tiles':[0,1],
                           'port': None},
                       4: {'tiles':[1],
                           'port': None},
                       5: {'tiles':[1,2],
                           'port': None},
                       6: {'tiles':[2],
                           'port': None},
                       7: {'tiles':[2],
                           'port': None}, #end of row 1
                       8: {'tiles':[3],
                           'port': None}, 
                       9: {'tiles':[0,3],
                           'port': None},
                       10: {'tiles':[0,3,4],
                            'port': None},
                       11: {'tiles':[0,1,4],
                            'port': None},
                       12: {'tiles':[1,4,5],
                            'port': None},
                       13: {'tiles':[1,2,5],
                            'port': None},
                       14: {'tiles':[2,5,6],
                            'port': None},
                       15: {'tiles':[2,6],
                            'port': None},
                       16: {'tiles':[6],
                            'port': None}, #end of row 2
                       17: {'tiles':[7],
                            'port': None},
                       18: {'tiles':[3,7],
                            'port': None},
                       19: {'tiles':[3,7,8],
                            'port': None},
                       20: {'tiles':[3,4,8],
                            'port': None},
                       21: {'tiles':[4,8,9],
                            'port': None},
                       22: {'tiles':[4,5,9],
                            'port': None},
                       23: {'tiles':[5,9,10],
                            'port': None},
                       24: {'tiles':[5,6,10],
                            'port': None},
                       25: {'tiles':[6,10,11],
                            'port': None},
                       26: {'tiles':[6,11],
                            'port': None},
                       27: {'tiles':[11],
                            'port': None}, #end of row 3
                       28: {'tiles':[7],
                            'port': None},
                       29: {'tiles':[7,12],
                            'port': None},
                       30: {'tiles':[7,8,12],
                            'port': None},
                       31: {'tiles':[8,12,13],
                            'port': None},
                       32: {'tiles':[8,9,13],
                            'port': None},
                       33: {'tiles':[9,13,14],
                            'port': None},
                       34: {'tiles':[9,10,14],
                            'port': None},
                       35: {'tiles':[10,14,15],
                            'port': None},
                       36: {'tiles':[10,11,15],
                            'port': None},
                       37: {'tiles':[11,15],
                            'port': None},
                       38: {'tiles':[11],
                            'port': None}, #end of row 4
                       39: {'tiles':[12],
                            'port': None},
                       40: {'tiles':[12,16],
                            'port': None},
                       41: {'tiles':[12,13,16],
                            'port': None},
                       42: {'tiles':[13,16,17],
                            'port': None},
                       43: {'tiles':[13,14,17],
                            'port': None},
                       44: {'tiles':[14,17,18],
                            'port': None},
                       45: {'tiles':[14,15,18],
                            'port': None},
                       46: {'tiles':[15,18],
                            'port': None},
                       47: {'tiles':[15],
                            'port': None}, #end of row 5
                       48: {'tiles':[16],
                            'port': None},
                       49: {'tiles':[16],
                            'port': None},
                       50: {'tiles':[16,17],
                            'port': None},
                       51: {'tiles':[17],
                            'port': None},
                       52: {'tiles':[17,18],
                            'port': None},
                       53: {'tiles':[18],
                            'port': None},
                       54: {'tiles':[18],
                            'port': None}}
            
    #port num: [settlement_locs]
    port_locs = {0: [1,2],
                 1: [4,5],
                 2: [15,16],
                 3: [27,38],
                 4: [46,47],
                 5: [51,52],
                 6: [48,49],
                 7: [29,39],
                 8: [8,18]}
    
    port_types = ['brick', 'sheep', 'wood', 'wheat', 'ore', 'any', 'any', 'any', 'any']
    
    random.shuffle(port_types)
    
    for i, p in enumerate(port_types):
        for s in port_locs[i]:
            settlement_dict[s]['port'] = p
            
    
    
    tile_dict, num_dict = create_board()
    
    pipdict = {0: 0, 2:1, 3:2, 4:3, 5:4, 6:5,
               12:1, 11:2, 10:3, 9:4, 8:5}
    
    res_availability_dict = res_availability(tile_dict, pipdict)
    
    resvalue_dict = {'wood': 3.86-0.178*res_availability_dict['wood'],
                     'brick': 3.72-0.18*res_availability_dict['brick'],
                     'sheep': 3.22-0.19*res_availability_dict['sheep'],
                     'wheat': 3.75-0.15*res_availability_dict['wheat'],
                     'ore': 2.98-0.12*res_availability_dict['ore']}
    
    port_value_dict = {}
    fourone_values = []
    threeone_values = []
    
    for i in itertools.combinations(list(resvalue_dict.keys()),4):
        val = 0
        for j in i:
            val += resvalue_dict[j]
        fourone_values.append(val/16) #divide by 4 for the mean, divide by 4 for the cost
        threeone_values.append(val/12) #divide by 4 for the mean, divide by 3 for the cost
        
        if 'wood' not in i:
            port_value_dict['wood'] = val/8 #divide by 4 for mean, divide by 2 for cost
        elif 'brick' not in i:
            port_value_dict['brick'] = val/8 #divide by 4 for mean, divide by 2 for cost
        elif 'sheep' not in i:
            port_value_dict['sheep'] = val/8 #divide by 4 for mean, divide by 2 for cost
        elif 'wheat' not in i:
            port_value_dict['wheat'] = val/8 #divide by 4 for mean, divide by 2 for cost
        elif 'ore' not in i:
            port_value_dict['ore'] = val/8 #divide by 4 for mean, divide by 2 for cost
            
    port_value_dict[None] = np.mean(fourone_values)
    port_value_dict['any'] = np.mean(threeone_values)
            
    
    game_len = 72
    rolls = np.array([2,3,4,5,6,8,9,10,11,12])
    full_rolls = np.append(rolls, np.sum(np.random.randint(1,7,(game_len,2)), axis = 1))
    
    full_roll_unique, full_roll_counts = np.unique(full_rolls, return_counts = True)
    full_roll_counts = full_roll_counts - 1
    
    
        
    for s in settlement_dict.keys():
        
        settlement_dict[s]['resources'] = {'wood': 0,
                                           'sheep': 0,
                                           'brick': 0,
                                           'wheat': 0,
                                           'ore': 0}
        settlement_dict[s]['numres'] = []
        settlement_dict[s]['port_value'] = port_value_dict[settlement_dict[s]['port']]
        
        
        for t in settlement_dict[s]['tiles']:
            res = tile_dict[t]['resource']
            num = tile_dict[t]['num']
            settlement_dict[s]['numres'].append((num,res))
            
            if num != 0:
                num_count = full_roll_counts[np.argwhere(full_roll_unique == num)][0,0]

                settlement_dict[s]['resources'][res] += num_count
                
    return settlement_dict, pipdict, resvalue_dict, res_availability_dict

def calculate_resource_score(resdict, resvalue_dict):
    return np.sum([resdict['wood']*resvalue_dict['wood'],
                   resdict['brick']*resvalue_dict['brick'],
                   resdict['sheep']*resvalue_dict['sheep'],
                   resdict['wheat']*resvalue_dict['wheat'],
                   resdict['ore']*resvalue_dict['ore']])

def calculate_total_pips(numres, pipdict):
    pips = 0
    for num, res in numres:
        pips += pipdict[num]
        
    return pips
        

if __name__ == '__main__':
    
    
    
    #settlement num: list of tile nums
    settlement_dict, pipdict, resvalue_dict, res_availability_dict = play_one_game()
    
    
    
    
    
    df = pd.DataFrame.from_dict(settlement_dict, orient='index')
    
    df['rescore'] = df.resources.apply(lambda x: calculate_resource_score(x, resvalue_dict))
    df['restotal'] = df.resources.apply(lambda x: np.sum(list(x.values())))
    df['piptotal'] = df.numres.apply(lambda x: calculate_total_pips(x, pipdict))
    
    
    
    
    
        
        
        
