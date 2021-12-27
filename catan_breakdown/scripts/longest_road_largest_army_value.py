# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 16:08:00 2021

@author: alext
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import catan.read_games as r

if __name__ == '__main__':
    
    games = r.read_all_games()
    
    #%%
    gcount = 0
    data = []
    for game in games:
        gcount += 1
        for p in game.players.values():
            win = p.name == game.winner
            longest_road = p.longest_road
            largest_army = p.largest_army
            gained_longest_road = p.gained_longest_road
            lost_longest_road = p.lost_longest_road
            gained_largest_army = p.gained_largest_army
            lost_largest_army = p.lost_largest_army
            
            row = [gcount, p.name, win, longest_road, largest_army, gained_longest_road,
                   lost_longest_road, gained_largest_army, lost_largest_army]
            data.append(row)
            
    df = pd.DataFrame(data = data, columns = ['gid', 'player', 'winner', 'longest_road', 'largest_army',
                                              'gained_lr', 'lost_lr', 'gained_la', 'lost_la'])
    
    #%%
    
    odds_with_lr = len(df[(df.longest_road) & (df.winner)])/len(df[df.longest_road])
    odds_with_la = len(df[(df.largest_army) & (df.winner)])/len(df[df.largest_army])
    
    #%%
    data = []
    for g, gdf in df.groupby('gid'):
        lr_options = []
        for gained_lr in gdf.gained_lr:
            for i in gained_lr:
                lr_options.append(i)
        if lr_options:
            first_gained_lr = np.min(lr_options)
        else:
            first_gained_lr = 0
        
        la_options = []
        for gained_la in gdf.gained_la:
            for i in gained_la:
                la_options.append(i)
        if la_options:
            first_gained_la = np.min(la_options)
        else:
            first_gained_la = 0
        
        for rrow in gdf.iterrows():
            fg_la = first_gained_la in rrow[1].gained_la
            fg_lr = first_gained_lr in rrow[1].gained_lr
            
            datarow = [g, rrow[1].player, rrow[1].winner, fg_la, fg_lr]
            data.append(datarow)
            
    ddf = pd.DataFrame(data = data, columns = ['gid', 'player', 'winner', 'fg_la', 'fg_lr'])
    
    
            
            