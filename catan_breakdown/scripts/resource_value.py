# -*- coding: utf-8 -*-
"""
Created on Mon Dec  6 09:51:41 2021

@author: alext
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from catan import read_games

#%%

if __name__ == '__main__': 
    
    games = read_games.read_all_games()
    #%%
    agames = read_games.read_anvil_games()
    
    #%%
    
    allgames = games + agames
    #%%
    gcount = 0
    data = []
    
    for game in allgames:
        gcount += 1
        pdict = {}
        if len(game.players.keys()) != 4:
            continue
        for p in game.players.keys():
            pdict[p] = {}
            pdict[p]['winner'] = game.players[p].name == game.winner
            pdict[p]['playertype'] = None
            
        woodbase = game.availdict['lumber']
        brickbase = game.availdict[' brick']
        sheepbase = game.availdict['wool']
        wheatbase = game.availdict['grain']
        orebase = game.availdict['ore']
        for turn in game.turns:
            if turn.player in pdict.keys():
                pdict[turn.player]['playertype'] = turn.playertype
            else:
                continue
            for trade in turn.trades:
                p1wood = 0
                p1brick = 0
                p1sheep = 0
                p1wheat = 0
                p1ore = 0
                for r in trade.p1resources:
                    if r == 'lumber':
                        p1wood += 1
                    elif r == ' brick':
                        p1brick += 1
                    elif r == 'wool':
                        p1sheep += 1
                    elif r == 'grain':
                        p1wheat += 1
                    elif r == 'ore':
                        p1ore += 1
                
                p2wood = 0
                p2brick = 0
                p2sheep = 0
                p2wheat = 0
                p2ore = 0
                for r in trade.p2resources:
                    if r == 'lumber':
                        p2wood += 1
                    elif r == ' brick':
                        p2brick += 1
                    elif r == 'wool':
                        p2sheep += 1
                    elif r == 'grain':
                        p2wheat += 1
                    elif r == 'ore':
                        p2ore += 1
                        
                if trade.p1 != 'bank':
                    try: 
                        p1points = turn.player_point_totals[trade.p1]
                    except KeyError:
                        p1points = None
                    p1ptype = pdict[trade.p1]['playertype']
                    p1winner = pdict[trade.p1]['winner']
                else:
                    p1points = None
                    p1ptype = None
                    p1winner = None
                
                if trade.p2 != 'bank':
                    try:
                        p2points = turn.player_point_totals[trade.p2]
                    except KeyError:
                        p2points = None
                    p2ptype = pdict[trade.p2]['playertype']
                    p2winner = pdict[trade.p2]['winner']
                else:
                    p2points = None
                    p2ptype = None
                    p2winner = None
                
                row = [gcount, turn.turn, trade.p1, trade.p2, p1points, p2points, p1wood, p1brick, p1sheep, p1wheat, p1ore, 
                       np.sum([p2wood, p2brick, p2sheep, p2wheat, p2ore]), p1ptype, p2ptype, p1winner, p2winner,
                       woodbase, brickbase, sheepbase, wheatbase, orebase]
                data.append(row)
                row = [gcount, turn.turn, trade.p2, trade.p1, p2points, p1points, p2wood, p2brick, p2sheep, p2wheat, p2ore, 
                       np.sum([p1wood, p1brick, p1sheep, p1wheat, p1ore]), p2ptype, p1ptype, p2winner, p1winner,
                       woodbase, brickbase, sheepbase, wheatbase, orebase]
                data.append(row)
    
    df = pd.DataFrame(data = data, columns = ['gid', 'turn_num', 'p1', 'p2', 'p1points', 'p2points', 
                                              'wood', 'brick', 'sheep', 'wheat', 'ore', 'total_gained',
                                              'p1type', 'p2type', 'p1winner', 'p2winner',
                                              'woodbase', 'brickbase', 'sheepbase', 'wheatbase', 'orebase'])
    
    def myround(x, base=5):
        return base * round(x/base)

    dfs = []                                 
    for g, gdf in df.groupby('gid'):
        gdf['per_turn'] = myround(100*gdf.turn_num / gdf.turn_num.max())
        dfs.append(gdf)
        
    df = pd.concat(dfs)
    
    def assumed_value(r, rgiven, rreceived):
        if r > 0:
            return rreceived/rgiven
        else:
            return None
        
        
        
    df['resources_given'] = df.wood + df.brick + df.sheep + df.wheat + df.ore
    
    for r in ['wood', 'brick', 'sheep', 'wheat', 'ore']:
        df[r+'_value'] = df.apply(lambda x: assumed_value(x[r], x.resources_given, x.total_gained), axis = 1)
    
    #%%
    data = []
    for rrow in df.iterrows():
        
        row = rrow[1]
        for resource in ['wood', 'brick', 'sheep', 'wheat', 'ore']:
            if row[resource + '_value']:
                r = [row.gid, row.turn_num, row.per_turn, row.p1, row.p2, 
                     row.p1points, row.p2points, row.p1type, row.p2type,
                     row.p1winner, row.p2winner,
                     resource, row[resource + '_value'], np.round(row[resource+'base'])]
                data.append(r)
            
    ddf = pd.DataFrame(data = data, columns = ['gid', 'turn_num', 'per_turn', 'p1', 'p2', 
                                               'p1points', 'p2points', 'p1type', 'p2type',
                                               'p1winner', 'p2winner','resource', 'resource_value',
                                               'resourcebase'])
    
    u_resource_value = ddf.resource_value.mean()
    std_resource_value = ddf.resource_value.std()
    
    u_bankless_resource_value = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank')].resource_value.mean()
    std_bankless_resource_value = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank')].resource_value.std()
    
    u_botless_resource_value = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank') & (ddf.p1type != 'bot') & (ddf.p2type != 'bot')].resource_value.mean()
    u_botless_resource_value = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank') & (ddf.p1type != 'bot') & (ddf.p2type != 'bot')].resource_value.std()
    
    ddf['z_resource_value'] = ddf.resource_value.apply(lambda x: (x-u_resource_value)/std_resource_value)
    ddf['z_bankless_resource_value'] = ddf.resource_value.apply(lambda x: (x-u_bankless_resource_value)/std_bankless_resource_value)    
    
    ddf['norm_resource_value'] = ddf.resource_value.apply(lambda x: x/u_resource_value)
    ddf['norm_bankless_resource_value'] = ddf.resource_value.apply(lambda x: x/u_bankless_resource_value)    
    
    #%%
    gdf = ddf.groupby('resource').resource_value.describe()
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'], 
            height = [gdf.loc['wood', 'mean'],
                      gdf.loc['brick', 'mean'],
                      gdf.loc['sheep', 'mean'],
                      gdf.loc['wheat', 'mean'],
                      gdf.loc['ore', 'mean']],
            yerr = [gdf.loc['wood', 'std']/np.sqrt(gdf.loc['wood', 'count']),
                      gdf.loc['brick', 'std']/np.sqrt(gdf.loc['brick', 'count']),
                      gdf.loc['sheep', 'std']/np.sqrt(gdf.loc['sheep', 'count']),
                      gdf.loc['wheat', 'std']/np.sqrt(gdf.loc['wheat', 'count']),
                      gdf.loc['ore', 'std']/np.sqrt(gdf.loc['ore', 'count'])],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    # sns.barplot(x = 'resource', y = 'resource_value', data = ddf)
    plt.xlabel('Resource')
    plt.ylabel('Estimated Resource Value')
    plt.title('General Resource Value')
        
    #%%
    gdf = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank')].groupby('resource').resource_value.describe()
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'], 
            height = [gdf.loc['wood', 'mean'],
                      gdf.loc['brick', 'mean'],
                      gdf.loc['sheep', 'mean'],
                      gdf.loc['wheat', 'mean'],
                      gdf.loc['ore', 'mean']],
            yerr = [gdf.loc['wood', 'std']/np.sqrt(gdf.loc['wood', 'count']),
                      gdf.loc['brick', 'std']/np.sqrt(gdf.loc['brick', 'count']),
                      gdf.loc['sheep', 'std']/np.sqrt(gdf.loc['sheep', 'count']),
                      gdf.loc['wheat', 'std']/np.sqrt(gdf.loc['wheat', 'count']),
                      gdf.loc['ore', 'std']/np.sqrt(gdf.loc['ore', 'count'])],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    
    plt.ylim([0.8,1.2])
    plt.xlabel('Resource')
    plt.ylabel('Estimated Resource Value')
    plt.title('General Resource Value (Excluding Bank Trades)')
    
    #%%
    gdf = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank') & (ddf.p1type != 'bot') & (ddf.p2type != 'bot')].groupby('resource').resource_value.describe()
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'], 
            height = [gdf.loc['wood', 'mean'],
                      gdf.loc['brick', 'mean'],
                      gdf.loc['sheep', 'mean'],
                      gdf.loc['wheat', 'mean'],
                      gdf.loc['ore', 'mean']],
            yerr = [gdf.loc['wood', 'std']/np.sqrt(gdf.loc['wood', 'count']),
                      gdf.loc['brick', 'std']/np.sqrt(gdf.loc['brick', 'count']),
                      gdf.loc['sheep', 'std']/np.sqrt(gdf.loc['sheep', 'count']),
                      gdf.loc['wheat', 'std']/np.sqrt(gdf.loc['wheat', 'count']),
                      gdf.loc['ore', 'std']/np.sqrt(gdf.loc['ore', 'count'])],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    
    
    plt.ylim([0.8,1.3])
    plt.xlabel('Resource')
    plt.ylabel('Estimated Resource Value')
    plt.title('General Resource Value (Excluding Bank and Bot Trades)')
    
    #%%
    plt.figure()
    for x, c in zip(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'],['#336600', '#993300', '#70db70', '#ffcc00', '#808080']):
        gdf = ddf[ddf.resource == x.lower()].groupby('per_turn').mean().reset_index()
        plt.plot(gdf.per_turn, gdf.resource_value, color = c, linewidth = 2)
    # sns.lineplot(x = 'per_turn', y = 'resource_value', hue = 'resource', data = ddf)
    plt.xlabel('% of game complete')
    plt.ylabel('Resource Value')
    plt.title('Resource Value by Amount of Game Played')
    plt.legend(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'])
    
    #%%
    plt.figure()
    for x, c in zip(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'],['#336600', '#993300', '#70db70', '#ffcc00', '#808080']):
        gdf = ddf[(ddf.resource == x.lower()) & (ddf.p1 != 'bank') & (ddf.p2 != 'bank')].groupby('per_turn').mean().reset_index()
        plt.plot(gdf.per_turn, gdf.resource_value, color = c, linewidth = 2)
    # sns.lineplot(x = 'per_turn', y = 'resource_value', hue = 'resource', data = ddf)
    plt.xlabel('% of game complete')
    plt.ylabel('Resource Value')
    plt.title('Bankless Resource Value by Amount of Game Played')
    plt.legend(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'])
    
        #%%
    plt.figure()
    for x, c in zip(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'],['#336600', '#993300', '#70db70', '#ffcc00', '#808080']):
        gdf = ddf[(ddf.resource == x.lower()) & (ddf.p1 != 'bank') & (ddf.p2 != 'bank') & (ddf.p1type != 'bot') & (ddf.p2type != 'bot')].groupby('per_turn').mean().reset_index()
        plt.plot(gdf.per_turn, gdf.resource_value, color = c, linewidth = 2)
    # sns.lineplot(x = 'per_turn', y = 'resource_value', hue = 'resource', data = ddf)
    plt.xlabel('% of game complete')
    plt.ylabel('Resource Value')
    plt.title('Bankless and Botless Resource Value by Amount of Game Played')
    plt.legend(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'])
    
    
    
    #%%
    plt.figure()
    for x, c in zip(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'],['#336600', '#993300', '#70db70', '#ffcc00', '#808080']):
        gdf = ddf[(ddf.resource == x.lower()) & (ddf.p1 != 'bank') & (ddf.p2 != 'bank')].groupby('p1points').mean().reset_index()
        plt.plot(gdf.p1points, gdf.resource_value, color = c, linewidth = 2)
    # sns.lineplot(x = 'p1points', y = 'resource_value', hue = 'resource', data = ddf[(ddf.p1 != 'bank') & (ddf.p2 != 'bank')])
    plt.xlim([2,9])
    plt.xlabel('Point Total')
    plt.ylabel('Resource Value')
    plt.ylim([0.5, 2])
    plt.title('Bankless Resource Value by Amount of Points')
    plt.legend(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'])
    
    #%%
    
    df['point_descrepancy'] = df.p2points - df.p1points
    df['resource_descrepancy'] = df.total_gained - df.resources_given
    
    sns.scatterplot(x = 'point_descrepancy', y = 'resource_descrepancy', data = df[(df.p1 != 'bank') & (df.p2 != 'bank')])
    
    #%%
    tdata = []
    pdata = []
    for g, gdf in df.groupby('gid'):
        a = gdf.per_turn.value_counts()
        b = gdf[(gdf.p1 != 'bank') & (gdf.p2 != 'bank')].per_turn.value_counts()
        
        for i in a.index:
            try:
                t = b.loc[i]
            except:
                t = None
            r = [i, 'general', a.loc[i]]
            tdata.append(r)
            r = [i, 'bankless', t]
            tdata.append(r)
            
    tdf = pd.DataFrame(data = tdata, columns = ['per_turn', 'tradetype', 'trades'])
    
    plt.figure()
    sns.lineplot(x = 'per_turn', y = 'trades', hue = 'tradetype', data = tdf)
    plt.xlabel('% of game complete')
    plt.ylabel('Number of trades')
    plt.title('Number of trades per 5% of game')
    
    
    #%%
    
    
    
    # sns.lineplot(x = 'resourcebase', y = 'resource_value', hue = 'resource', data = gdf)
    
    plt.figure()
    for x, c in zip(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'],['#336600', '#993300', '#70db70', '#ffcc00', '#808080']):
        gdf = ddf[(ddf.resource == x.lower()) & (ddf.resourcebase < 18)].groupby('resourcebase').mean().reset_index()
        plt.plot(gdf.resourcebase, gdf.resource_value, color = c, linewidth = 2)
    plt.xlabel('Resource Base')
    plt.ylabel('Resource Value')
    plt.title('Resource Value by Base Availability')
    plt.legend(['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'])
    
    #%%
    # gdf = ddf.groupby(['gid', 'resource']).mean().reset_index()
    # sns.barplot(x = 'resource', y = 'resourcebase', data = gdf)
    
    gdf = ddf.groupby('resource').resourcebase.describe()
    plt.figure()
    plt.bar(x = ['Wood', 'Brick', 'Sheep', 'Wheat', 'Ore'], 
            height = [gdf.loc['wood', 'mean'],
                      gdf.loc['brick', 'mean'],
                      gdf.loc['sheep', 'mean'],
                      gdf.loc['wheat', 'mean'],
                      gdf.loc['ore', 'mean']],
            yerr = [gdf.loc['wood', 'std']/np.sqrt(gdf.loc['wood', 'count']),
                      gdf.loc['brick', 'std']/np.sqrt(gdf.loc['brick', 'count']),
                      gdf.loc['sheep', 'std']/np.sqrt(gdf.loc['sheep', 'count']),
                      gdf.loc['wheat', 'std']/np.sqrt(gdf.loc['wheat', 'count']),
                      gdf.loc['ore', 'std']/np.sqrt(gdf.loc['ore', 'count'])],
            color = ['#336600', '#993300', '#70db70', '#ffcc00', '#808080'])
    
    plt.xlabel('Resource')
    plt.ylabel('Resource Base')
    plt.title('Average Resource Base')