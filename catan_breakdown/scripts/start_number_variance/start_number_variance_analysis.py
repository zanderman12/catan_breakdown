# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 16:17:25 2022

@author: alext
"""

import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

def calc_total_pips(numbers, pip_dict = {2:1,12:1,
                                         3:2,11:2,
                                         4:3,10:3,
                                         5:4,9:4,
                                         6:5,8:5}):
    total_pips = 0
    for n in numbers:
        total_pips += pip_dict[n]
    
    return total_pips

def count_doubles(numbers):
    u, c = np.unique(numbers, return_counts = True)
    
    return np.sum(c==2)

if __name__ == '__main__': 
    
    dfs = []
    for i in range(10):
        sdf = pickle.load(open(f'start_combo_sig_counts_{i}.pickle', 'rb'))
        dfs.append(sdf)
        
    df = pd.concat(dfs).reset_index()
    
    ddf = df.groupby('numbers').sum().reset_index()
    
    ddf['twos'] = ddf.numbers.apply(lambda x: x.count(2))
    ddf['twelves'] = ddf.numbers.apply(lambda x: x.count(12))
    
    ddf = ddf[(ddf.twos != 2) & (ddf.twelves != 2)]
    
    
    
    ddf['total_pips'] = ddf.numbers.apply(lambda x: calc_total_pips(x))
    ddf['num_doubles'] = ddf.numbers.apply(lambda x: count_doubles(x))
    ddf['full_outlier_odds'] = ddf.z_full_resources_gained/1000000
    ddf['half_outlier_odds'] = ddf.z_half_resources_gained/1000000
    
    
    
    #%%
    plt.figure()
    for g, gdf in ddf.groupby('num_doubles'):
        sns.regplot(x = 'total_pips', y = 'full_outlier_odds', data = gdf, order = 4, label = g)
        
    plt.legend(title = 'Count of Number Pairs')
    plt.title('Odds of 2 sigma outlier in resources across full game')
    
    plt.figure()
    for g, gdf in ddf.groupby('num_doubles'):
        sns.regplot(x = 'total_pips', y = 'half_outlier_odds', data = gdf, order = 4, label = g)
        
    plt.legend(title = 'Count of Number Pairs')
    plt.title('Odds of 2 sigma outlier in resources across half game')
    
    