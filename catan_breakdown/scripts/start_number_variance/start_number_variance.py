# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 17:13:22 2022

@author: alext
"""

import numpy as np
from itertools import combinations_with_replacement
import pandas as pd
from scipy.stats import zscore
import pickle
import time
# from numba import jit, njit



if __name__ == '__main__':
    
    # s = time.perf_counter()
    dfs = []
    
    for k in range(10):
        for j in range(100):
            print(j)
            data = []
            for i in range(100):
                
                game_len = int(np.round(np.random.normal(71.4,13.4)))
                
                
                rolls = np.array([2,3,4,5,6,8,9,10,11,12])
                full_rolls = np.append(rolls, np.sum(np.random.randint(1,7,(game_len,2)), axis = 1))
                
                full_roll_unique, full_roll_counts = np.unique(full_rolls, return_counts = True)
                full_roll_counts = full_roll_counts - 1
                
                
                for h in range(1,7):
                    for numbers in combinations_with_replacement([2,3,4,5,6,8,9,10,11,12],h):
                        unique, counts = np.unique(numbers, return_counts = True)
                        if np.max(counts) <= 2:
                            full_rolled_numbers = np.in1d(full_roll_unique, numbers)
                            resource_total = np.sum(counts * full_roll_counts[full_rolled_numbers])
                            row = [numbers, resource_total]
                            data.append(row)
                        
                
                        
                    
                
                
            ddf = pd.DataFrame(data = data, columns = ['numbers', 'full_resources_gained'])
                
        
           
            ddf['z_full_resources_gained'] = zscore(ddf.full_resources_gained)
            
            a = ddf[ddf.z_full_resources_gained > 2].copy()
            b = a[['numbers', 'z_full_resources_gained']].groupby('numbers').count().reset_index()
            b.columns = ['numbers', 'num_games_over_2stds']
            b['over_2_std_rate'] = b.num_games_over_2stds/100
            
            
            c = ddf[ddf.z_full_resources_gained > 0].copy()
            d = c[['numbers', 'z_full_resources_gained']].groupby('numbers').count().reset_index()
            d.columns = ['numbers', 'num_games_over_mean']
            d['over_mean_rate'] = d.num_games_over_mean/100
            
            e = ddf[ddf.z_full_resources_gained < -1].copy()
            f = e[['numbers', 'z_full_resources_gained']].groupby('numbers').count().reset_index()
            f.columns = ['numbers', 'num_games_below_neg1stds']
            f['below_neg1std_rate'] = f.num_games_below_neg1stds/100
            
            g = pd.merge(b,d, on = 'numbers', how = 'outer')
            df = pd.merge(g,f, on = 'numbers', how = 'outer')
            df['total_numbers'] = df.numbers.apply(lambda x: len(x))
            df.fillna(0)
            
            dfs.append(df)
            
        df = pd.concat(dfs)
        pdf = df.groupby('numbers').mean()
        pickle.dump(pdf, open(f'start_combo_odds_{k}.pickle', 'wb'))
    
    
# 
    
    