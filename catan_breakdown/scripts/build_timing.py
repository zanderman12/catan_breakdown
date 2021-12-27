# -*- coding: utf-8 -*-
"""
Created on Thu Dec  9 16:14:10 2021

@author: alext
"""
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import read_games
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression

def graph_win_odds(ddf, col, include_bots = True, order = 1):
    gdata = []
    for r, rdf in ddf.groupby(col):
        if include_bots:
            win_odds = len(rdf[rdf.winner])/len(rdf)
        else:
            win_odds = len(rdf[(rdf.winner) & (rdf.ptype != 'bot')])/len(rdf[rdf.ptype != 'bot'])
        row = [r, win_odds]
        gdata.append(row)
        
    gdf = pd.DataFrame(data = gdata, columns =[col, 'win_odds'])
    
    plt.figure()
    g = sns.regplot(x = col, y = 'win_odds', data = gdf, order = order)
    plt.axhline(y = 0.25, color = 'r')
    return g

#%%

if __name__ == '__main__': 
    
    games = read_games.read_all_games()
    
    #%%
    
    gcount = 0
    data = []
    
    for game in games:
        gcount += 1
        
        pdict = {}
        for p in game.players.keys():
            pdict[p] = {}
            pdict[p]['winner'] = game.players[p].name == game.winner
            pdict[p]['playertype'] = None
        for turn in game.turns:
            if turn.player in pdict.keys():
                pdict[turn.player]['playertype'] = turn.playertype
            else:
                continue
            
            roads = turn.built['road']
            settlements = turn.built['settlement']
            cities = turn.built['city']
            dev_cards = turn.built['dev_card']
            
            row = [gcount, turn.turn, turn.player, roads, settlements, cities, dev_cards, 
                   pdict[turn.player]['playertype'], pdict[turn.player]['winner']]
            data.append(row)
            
    df = pd.DataFrame(data = data, columns = ['gid', 'turnnum', 'p', 'roads', 'settlements', 
                                              'cities', 
                                              'dev_cards', 'ptype', 'winner'])
    
    #%%
    
    data = []
    
    for g, gdf in df.groupby('gid'):
        for p, pdf in gdf.groupby('p'):
            first_city = pdf[pdf.cities > 0].turnnum.min()
            num_cities = pdf.cities.sum()
            num_roads = pdf.roads.sum()
            num_settlements = pdf.settlements.sum()
            num_devcards = pdf.dev_cards.sum()
            first_settlement = pdf[pdf.settlements > 0].turnnum.min()
            settle_first = first_settlement < first_city
            
            row = [g, p, num_roads, num_settlements, num_cities, num_devcards, 
                   first_settlement, first_city, settle_first, pdf.iloc[0]['ptype'],
                   pdf.iloc[0]['winner']]
            
            data.append(row)
            
    ddf = pd.DataFrame(data = data, columns = ['gid', 'player', 'num_roads', 'num_settlements',
                                               'num_cities', 'num_devcards', 'first_settlement',
                                               'first_city', 'settle_first', 'ptype', 'winner'])
    
    #%%

    for c in ['num_roads', 'num_settlements', 'num_cities', 'num_devcards',
              'first_settlement', 'first_city']:
        g = graph_win_odds(ddf, c)
            
    
    #%%
    g = graph_win_odds(ddf, 'settle_first')
    sns.pointplot(x = 'settle_first', y = 'winner', data = ddf)
    
    #%%
    dfs = []
    for g, gdf in df.groupby('gid'):
        gdf['per_turn'] = np.round(100*gdf.turnnum/gdf.turnnum.max())
        for p, pdf in gdf.groupby('p'):
            for c in ['roads', 'settlements', 'cities', 'dev_cards']:
                pdf['curr_' + c] = pdf[c].cumsum()
            dfs.append(pdf)
                
    df = pd.concat(dfs)
    
    #%%
    
    for c in ['curr_roads', 'curr_settlements', 'curr_cities', 'curr_dev_cards']:
        plt.figure()
        sns.lineplot(x = 'per_turn', y = c, hue = 'winner', data = df)