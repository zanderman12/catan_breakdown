# -*- coding: utf-8 -*-
"""
Created on Sat Nov 27 12:11:10 2021

@author: alext
"""
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from catan import read_games

if __name__ == '__main__': 
    
    games = read_games.read_all_games()
    #%%
    ddata = []
    data = []
    gcount = 0
    for game in games:
        gcount += 1
        start_pos = []
        for p in list(game.players.keys()):
            start_pos.append(p)
        
        start_pos.reverse()
        w = np.argwhere(np.array(start_pos) == game.winner) + 1
        w = w[0][0]
        winner = game.winner
        
        wp = game.players[game.winner]
        
        lr = wp.longest_road
        la = wp.largest_army
        settlements = wp.built['settlement'] - wp.built['city']
        cities = wp.built['city']
        devvps = np.max([0, 10 - wp.points])
        roads = wp.built['road']
        dev_cards = wp.built['dev_card']
        
        resources = np.sum([x for x in wp.total_resources.values()])
        
        turns = len(game.turns)
        rolls = game.all_rolls
        dicefairness = game.dice_chisq
        
        row = [w, turns, lr, la, roads, settlements, cities, dev_cards, devvps, resources, 
               wp.total_resources, rolls, dicefairness]
        
        for p in game.players.values():
            rrow = [gcount, p.name, p.points, len(p.trades), p == wp]
            for i in ['grain', 'wool', 'ore', 'lumber', ' brick']:
                 rrow.append(p.total_resources[i])
            
            for i in ['road', 'settlement', 'city', 'dev_card']:
                rrow.append(p.built[i])
                
            ddata.append(rrow)
        
        data.append(row)
        
    df = pd.DataFrame(data = data, columns = ['place_order', 'num_turns', 'lr', 'la', 
                                              'roads', 'settlements', 'cities', 'dev_cards', 'devvps', 
                                              'resource_total', 'resource_breakdown',
                                              'rolls', 'dicefairness'])
    ddf = pd.DataFrame(data = ddata, columns = ['gid', 'pname', 'points', 'trades', 'winner', 'grain', 'wool', 'ore', 'lumber', 'brick',
                                                'road', 'settlement', 'city', 'dev_card'])
    
    #%%
    # turn count distribution
    sns.violinplot(x = 'num_turns', data = df, orientation = 'h')
    plt.xlabel('Number of Turns')
    plt.axvline(df.num_turns.median(), color = 'r')
    plt.title('Average Number of Turns')
    
    #%%
    
    # gdf = ddf.groupby('gid').sum()
    # # sns.barplot(x = ['Roads', 'Settlements', 'Cities', 'Development Cards'], 
    # #             y = [gdf.road.mean(), gdf.settlement.mean(), gdf.city.mean(), gdf.dev_card.mean()],
    # #             )
    # sns.barplot(x = ['Roads', 'Settlements', 'Cities', 'Development Cards'], 
    #             y = [df.roads.mean(), df.settlements.mean(), df.cities.mean(), df.dev_cards.mean()],
    #             )
    
    #%%
    gdf = ddf.groupby('gid').sum()
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheet', 'Ore'], 
            height = [gdf.lumber.mean(), gdf.brick.mean(), gdf.wool.mean(), gdf.grain.mean(), gdf.ore.mean()],
            yerr = [gdf.lumber.std(), gdf.brick.std(), gdf.wool.std(), gdf.grain.std(), gdf.ore.std()],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    plt.xlabel('Resource')
    plt.ylabel('Count')
    plt.title('Average Total Resource Count Per Game')
    
    #%%
    for i in ['grain', 'wool', 'ore', 'lumber', ' brick']:
        df[i.replace(' ', '')] = df.resource_breakdown.apply(lambda x: x[i])
        
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheet', 'Ore'], 
            height = [df.lumber.mean(), df.brick.mean(), df.wool.mean(), df.grain.mean(), df.ore.mean()],
            yerr = [df.lumber.std(), df.brick.std(), df.wool.std(), df.grain.std(), df.ore.std()],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    plt.xlabel('Resource')
    plt.ylabel('Count')
    plt.title('Winning Total Resource Count Per Game')
    
    #%%
    ddf['total_resources'] = ddf.grain + ddf.wool + ddf.ore + ddf.lumber + ddf.brick
    sns.kdeplot(x = ddf.total_resources)
    sns.kdeplot(x = df.resource_total, color = 'orange')
    plt.xlabel('Total Resources')
    plt.title('Avg Resource Total vs Winning Resource Total')
    

    
    
    #%%
    # total resources vs points
    plt.figure()
    sns.boxplot(x = 'total_resources', y = 'points', data = ddf[ddf.points>=2], orient = 'h')
    plt.gca().invert_yaxis()
    plt.xlabel('Resource Total')
    plt.ylabel('Point Total')
    plt.title('Resources vs Points Per Player')
    
    #%%
    # pie chart of start place order among winners
    labels = ['First', 'Fourth', 'Third', 'Second']
    a = df.place_order.value_counts()
    sizes = [a.loc[1], a.loc[4], a.loc[3], a.loc[2]]
    explode = (0, 0, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')
    
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    plt.title('Percent of Games Won by Starting Order')
    
    #%%
    # roll distribution across all games
    allrolls = []
    for r in df.rolls:
        for rr in r:
            allrolls.append(rr)
    
    a, b = np.unique(allrolls, return_counts = True)
    
    sns.barplot(x = a, y = b)
    plt.title('Aggregate Dice Roll Counts')
    plt.xlabel('Dice Roll')
    plt.ylabel('Roll Count')
    
    #%%
    pvalues = []
    for r in df.dicefairness:
        pvalues.append(r[1])
        
    sns.distplot(x = pvalues)
    
    #%%
    # num trades vs points
    sns.regplot(x = 'trades', y = 'points', data = ddf)
    
    #%%
    a = df.groupby(['lr', 'la', 'settlements', 'cities', 'devvps']).count()
    
    #%%
    
    data = []
    for rrow in ddf.iterrows():
        row = rrow[1]
        
        for i in ['grain', 'wool', 'ore', 'lumber', 'brick']:
            r = [row.pname, row.gid, row[i], i, row.winner]
            data.append(r)
            
    gdf = pd.DataFrame(data = data, columns = ['pname', 'gid', 'resource_count', 'resource', 'winner'])
    
    sns.barplot(x = 'resource', y = 'resource_count', hue = 'winner', data = gdf)
    plt.xlabel('Resource')
    plt.ylabel('Resource Count')
    plt.title('Resource Counts Split by Winner')
        
    
    #%%
    
    from scipy.stats import zscore
    
    dfs = []
    for g, gdf in ddf.groupby('gid'):
        gdf['total_resource_z'] = np.round(zscore(gdf.total_resources),2)
        gdf['placement'] = gdf.points.rank(ascending = False, method = 'min')
        
        dfs.append(gdf)
        
    ddf = pd.concat(dfs)
    
    #%%
    adf = pd.merge(ddf, df[['num_turns']], left_on = 'gid', how = 'left', right_index = True)
    adf.dropna(axis = 0, how = 'any', inplace = True)
    adf['70_turn_norm_resource_total'] = np.round(70 * adf.total_resources/adf.num_turns)
    adf['70_norm_resource_total_z'] = np.round(zscore(adf['70_turn_norm_resource_total']),1)
    
    
    
    fig, axs = plt.subplots(1,2, sharey = True)
    a = adf.groupby('70_turn_norm_resource_total').mean().reset_index()
    a['clean_winner'] = 100*a.winner
    sns.regplot(ax = axs[0], x = '70_turn_norm_resource_total', y = 'clean_winner', data = a)
    axs[0].axhline(y = 50)
    axs[0].axhline(y = 25)
    axs[0].axhline(y = 12.5)

    
    a = adf.groupby('70_norm_resource_total_z').mean().reset_index()
    a['clean_winner'] = 100*a.winner
    sns.regplot(ax = axs[1], x = '70_norm_resource_total_z', y = 'clean_winner', data = a)
    axs[1].axhline(y = 50)
    axs[1].axhline(y = 25)
    axs[1].axhline(y = 12.5)

    axs[0].set_ylabel('Odds of Winning the game')
    axs[0].set_xlabel('Normalized Total Resources')
    axs[1].set_xlabel('Z Score of Normalized Total Resources')
    axs[1].set_ylabel('')
    