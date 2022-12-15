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
from catan import read_games 


def graph_win_odds(ddf, col, include_bots = True, order = 1):
    gdata = []
    for r, rdf in ddf.groupby(col):
        if include_bots:
            win_odds = 100*len(rdf[rdf.winner])/len(rdf)
        else:
            win_odds = 100*len(rdf[(rdf.winner) & (rdf.ptype != 'bot')])/len(rdf[rdf.ptype != 'bot'])
        row = [r, win_odds]
        gdata.append(row)
        
    gdf = pd.DataFrame(data = gdata, columns =[col, 'win_odds'])
    
    plt.figure()
    g = sns.regplot(x = col, y = 'win_odds', data = gdf, order = order)
    plt.axhline(y = 25, color = 'r')
    plt.ylabel('Odds of Winning')
    plt.title("Odds of Winning based on a Player's " + col)
    plt.ylim([0,100])
    
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
            build_order = []
            for rrow in pdf.sort_values('turnnum').iterrows():
                if rrow[1]['settlements']:
                    build_order.append('S')
                if rrow[1]['cities']:
                    build_order.append('C')
                
            
            first_city = pdf[pdf.cities > 0].turnnum.min()
            num_cities = pdf.cities.sum()
            num_roads = pdf.roads.sum()
            num_settlements = pdf.settlements.sum()
            num_devcards = pdf.dev_cards.sum()
            first_settlement = pdf[pdf.settlements > 0].turnnum.min()
            if pd.notnull(first_settlement) and pd.notnull(first_city):
                settle_first = first_settlement < first_city
            elif pd.notnull(first_settlement):
                settle_first = True
            elif pd.notnull(first_city):
                settle_first = False
            first_two = '/'.join(build_order[:2])
            
            row = [g, p, num_roads, num_settlements, num_cities, num_devcards, 
                   first_settlement, first_city, settle_first, pdf.iloc[0]['ptype'],
                   pdf.iloc[0]['winner'], build_order, first_two]
            
            data.append(row)
            
    ddf = pd.DataFrame(data = data, columns = ['gid', 'player', 'Number of Roads', 'Number of Settlements',
                                               'Number of Cities', 'Number of Development Cards', 'Turn of First Settlement',
                                               'Turn of First City', 'settle_first', 'ptype', 'winner',
                                               'build_order', 'first_two'])
    
    #%%

    for c in ['Number of Roads', 'Number of Settlements', 'Number of Cities', 'Number of Development Cards']:
        g = graph_win_odds(ddf, c)
        
    #%%
    for c in ['Turn of First Settlement', 'Turn of First City']:
        g = graph_win_odds(ddf, c)
            
    
    #%%
    # g = graph_win_odds(ddf, 'settle_first')
    ddf['winodds'] = ddf.winner * 100
    ddf['First Build'] = ddf.settle_first.map({False: 'City First', True: 'Settlement First'})
    sns.pointplot(x = 'First Build', y = 'winodds', data = ddf, join = False)
    plt.axhline(25, color = 'r')
    plt.ylabel('Odds of Winning')
    plt.title('Win Odds based on Settlement or City First')    
    #%%
    dfs = []
    for g, gdf in df.groupby('gid'):
        gdf['per_turn'] = np.round(100*gdf.turnnum/gdf.turnnum.max())
        for p, pdf in gdf.groupby('p'):
            for c in ['roads', 'settlements', 'cities', 'dev_cards']:
                pdf['Current Number of ' + c.title()] = pdf[c].cumsum()
            dfs.append(pdf)
                
    df = pd.concat(dfs)
    
    #%%
    # plt.figure()
    # sns.lineplot(x = 'per_turn', y = 'winner', hue = 'Current Number of Settlements', data = df)
    
    #%%
    
    df['Game Result'] = df.winner.map({False: 'Lost', True: 'Won'})
    for c in ['Roads', 'Settlements', 'Cities',
              'Dev_Cards']:#'curr_roads', 'curr_settlements', 'curr_cities', 'curr_dev_cards']:
        plt.figure()
        sns.set_palette(sns.color_palette("Set2"), 2)
        sns.lineplot(x = 'per_turn', y = 'Current Number of '+c, hue = 'Game Result',
                     data = df.sort_values('Game Result', ascending = False))
        plt.xlabel('Percent of Game Completed')
        plt.title(f"Number of {c} Built at a Given Turn")
        
    #%%
    
    from scipy import stats
    
    result = stats.linregress(x = df[df.winner].per_turn *.7, y = df[df.winner]['Current Number of Settlements'])
    print(result)
    result = stats.linregress(x = df[~df.winner].per_turn *.7, y = df[~df.winner]['Current Number of Settlements'])
    print(result)
        
    #%%
    plt.figure()
    ddf['winodds'] = ddf.winner * 100
    sns.pointplot(x = 'first_two', y = 'winodds', data = ddf, join = False)
    plt.axhline(25, color = 'r')
    plt.ylabel('Odds of Winning')
    plt.title('Win Odds based on First 2 Builds')  