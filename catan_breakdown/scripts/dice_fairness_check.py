# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 07:27:52 2022

@author: alext
"""
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from catan import read_games
# simple code to implement Runs
# test of randomnes

import random
import math
import statistics
import scipy.stats


def runsTest(l, l_median):

	runs, n1, n2 = 0, 0, 0
	
	# Checking for start of new run
	for i in range(1,len(l)):
		
		# no. of runs
		if (l[i] >= l_median and l[i-1] < l_median) or (l[i] < l_median and l[i-1] >= l_median):
			runs += 1
		
		# no. of positive values
		if(l[i]) >= l_median:
			n1 += 1
		
		# no. of negative values
		else:
			n2 += 1

	runs_exp = ((2*n1*n2)/(n1+n2))+1
	stan_dev = math.sqrt((2*n1*n2*(2*n1*n2-n1-n2))/ \
					(((n1+n2)**2)*(n1+n2-1)))

	z = (runs-runs_exp)/stan_dev

	return z

#%%
if __name__ == '__main__': 
    
    games = read_games.read_all_games()
    
    #%%
    ddata = []
    data = []
    gcount = 0
    badgames = []
    for game in games:
        gcount += 1
        for turn in game.turns:
            turnnum = turn.turn
            roll = turn.roll
            
            if roll:
                row = [gcount, turnnum, roll]
                cols = ['gid', 'turnnum', 'roll']
                for i, p in enumerate(game.players.keys()):
                    if p == turn.player:
                        pturn = i
                        bot = game.players[p].isbot
                        
                   
                    row.append(turn.player_point_totals[p])
                    cols.append(f"{i}_points")
                    row.append(turn.player_resource_totals[p])
                    cols.append(f"{i}_total_res")

                        
                row.append(pturn)
                cols.append('pturn')
                row.append(bot)
                cols.append('bot')
                data.append(row)
            
    df = pd.DataFrame(data = data, columns = cols)
    # df = df[~df.gid.isin(badgames)]
            
    
        
    df['total_game_resources'] = df[['0_total_res', '1_total_res', '2_total_res', '3_total_res']].sum(axis = 1)
    df['rolled_seven'] = df.roll == 7
    df['pturn_total_res'] = df.apply(lambda x: x[f"{x.pturn}_total_res"], axis = 1)
    
    #%%
    
    plt.figure()
    sns.barplot(x = 'roll', y = '0_points', data = df.groupby('roll').count().reset_index())
    
    plt.figure()
    sns.barplot(x = 'roll', y = '0_points', data = df.groupby(['gid', 'roll']).count().reset_index())
    
    #%%
    
    
    sns.regplot(x = 'turnnum', y = 'rolled_seven', data = df)
    
    #%%
    Z = abs(runsTest(df.roll, df.roll.median()))
    print(Z)
    print(scipy.stats.norm.sf(Z))
    
    #%%
    data = []
    for g, gdf in df.groupby(['bot', 'gid']):
        row = [g[0], g[1], len(gdf[gdf.roll == 7]), len(gdf.pturn.unique()), len(gdf)]
        data.append(row)
        
    ddf = pd.DataFrame(data = data, columns = ['bot', 'gid', 'num_sevens', 'num_players', 'num_turns'])
    ddf['seven_rate'] = ddf.num_sevens/ddf.num_turns
    
    sns.boxplot(x = 'bot', y = 'seven_rate', data = ddf)
    
    #%%
    
    data = []
    for g, gdf in df.groupby('pturn_total_res'):
        if len(gdf) > 50:
            row = [g, gdf.rolled_seven.mean(), len(gdf)]
            data.append(row)
        
    gdf = pd.DataFrame(data = data, columns = ['pturn_total_res', 'rolled_seven', 'n'])
    sns.scatterplot(x = 'pturn_total_res', y = 'rolled_seven', data = gdf, size = 'n')
    sns.regplot(x = 'pturn_total_res', y = 'rolled_seven', data = df[df.pturn_total_res.isin(gdf.pturn_total_res)], scatter = False)
    plt.axhline(y = 1/6, color = 'r')
    
    
    
    #%%
    data = []
    for g, gdf in df.groupby('total_game_resources'):
        if len(gdf) > 50:
            row = [g, gdf.rolled_seven.mean(), len(gdf)]
            data.append(row)
        
    gdf = pd.DataFrame(data = data, columns = ['total_game_resources', 'rolled_seven', 'n'])
    sns.scatterplot(x = 'total_game_resources', y = 'rolled_seven', data = gdf, size = 'n')
    sns.regplot(x = 'total_game_resources', y = 'rolled_seven', data = df[df.total_game_resources.isin(gdf.total_game_resources)], scatter = False)
    plt.axhline(y = 1/6, color = 'r')