# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 19:01:26 2022

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
        sdf = pickle.load(open('start_combo_odds_0.pickle', 'rb'))
        dfs.append(sdf)
        
    df = pd.concat(dfs).reset_index()
    
    df.fillna(0, inplace = True)
    
    df['twos'] = df.numbers.apply(lambda x: x.count(2))
    df['twelves'] = df.numbers.apply(lambda x: x.count(12))
    
    df = df[(df.twos != 2) & (df.twelves != 2)]
    
    df['total_pips'] = df.numbers.apply(lambda x: calc_total_pips(x))
    df['Number Of Doubles'] = df.numbers.apply(lambda x: count_doubles(x))
    
    for i in ['over_2_std_rate', 'over_mean_rate', 'below_neg1std_rate']:
        df[i] = df[i]*100
    
    df['above_neg1std_rate'] = 100 - df.below_neg1std_rate
    #%%
    
    plt.figure()
    sns.pointplot(x = 'total_pips', y ='over_2_std_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips > 12])
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Significantly More Resources')
    plt.title('Significanlty More Resources')
    
    plt.figure()
    sns.pointplot(x = 'total_pips', y ='over_mean_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips > 7])
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Above Average Resources')
    plt.title('Above Average Resources')

    
    plt.figure()
    sns.pointplot(x = 'total_pips', y ='below_neg1std_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips < 22])
    
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Significantly Fewer Resources')
    plt.title('Significantly Fewer Resources')
    
    #%%
    
    fig, axs = plt.subplots(1,3)
    sns.pointplot(ax = axs[0], x = 'total_pips', y ='over_2_std_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips.between(17,22)])
    axs[0].set_xlabel('Total Pips')
    axs[0].set_ylabel('Odds of Significantly More Resources')
    axs[0].set_title('Significanlty More Resources')
    
    sns.pointplot(ax = axs[1], x = 'total_pips', y ='over_mean_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips.between(17,22)])
    axs[1].set_xlabel('Total Pips')
    axs[1].set_ylabel('Odds of Above Average Resources')
    axs[1].set_title('Above Average Resources')

    
    sns.pointplot(ax = axs[2], x = 'total_pips', y ='below_neg1std_rate', hue = 'Number Of Doubles', 
                  data = df[df.total_pips.between(17,22)])
    
    axs[2].set_xlabel('Total Pips')
    axs[2].set_ylabel('Odds of Significantly Fewer Resources')
    axs[2].set_title('Significantly Fewer Resources')
    
    plt.tight_layout()
    
    #%%
    
    df['Total Hexes'] = df.total_numbers.copy()
    
    plt.figure()
    sns.pointplot(x = 'total_pips', y ='over_2_std_rate', hue = 'Total Hexes', 
                  data = df[(df.total_pips > 10) & (df.total_numbers > 3)])
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Significantly More Resources')
    plt.title('Significanlty More Resources')
    
    plt.figure()
    sns.pointplot(x = 'total_pips', y ='over_mean_rate', hue = 'Total Hexes',
                  data = df[(df.total_pips > 6) & (df.total_numbers > 3)])
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Above Average Resources')
    plt.title('Above Average Resources')
    
    plt.figure()
    sns.pointplot( x = 'total_pips', y ='below_neg1std_rate', hue = 'Total Hexes', 
                  data = df[(df.total_pips < 22) & (df.total_numbers > 3)])
    plt.xlabel('Total Pips')
    plt.ylabel('Odds of Significantly Fewer Resources')
    plt.title('Significantly Fewer Resources')
    
    
    #%%
    
    fig, axs = plt.subplots(1,3)
    sns.pointplot(ax = axs[0], x = 'total_pips', y ='over_2_std_rate', hue = 'Total Hexes', 
                  data = df[df.total_pips.between(17,22)])
    axs[0].set_xlabel('Total Pips')
    axs[0].set_ylabel('Odds of Significantly More Resources')
    axs[0].set_title('Significanlty More Resources')
    
    sns.pointplot(ax = axs[1], x = 'total_pips', y ='over_mean_rate', hue = 'Total Hexes', 
                  data = df[df.total_pips.between(17,22)])
    axs[1].set_xlabel('Total Pips')
    axs[1].set_ylabel('Odds of Above Average Resources')
    axs[1].set_title('Above Average Resources')

    
    sns.pointplot(ax = axs[2], x = 'total_pips', y ='below_neg1std_rate', hue = 'Total Hexes', 
                  data = df[df.total_pips.between(17,22)])
    
    axs[2].set_xlabel('Total Pips')
    axs[2].set_ylabel('Odds of Significantly Fewer Resources')
    axs[2].set_title('Significantly Fewer Resources')
    
    plt.tight_layout()
    
    
    
    
    
    
    
    
    
    
    
    