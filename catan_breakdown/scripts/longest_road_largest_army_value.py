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
        max_turns = len(game.turns) + 1
        for p in game.players.values():
            win = p.name == game.winner
            longest_road = p.longest_road
            largest_army = p.largest_army
            gained_longest_road = p.gained_longest_road
            lost_longest_road = p.lost_longest_road
            gained_largest_army = p.gained_largest_army
            lost_largest_army = p.lost_largest_army
            num_knights = 0
            for c in p.played_cards:
                if c == 'Knight':
                    num_knights += 1
            
            row = [gcount, p.name, p.isbot, win, longest_road, largest_army, gained_longest_road,
                   lost_longest_road, gained_largest_army, lost_largest_army, max_turns, num_knights, p.built['road']]
            data.append(row)
            
    df = pd.DataFrame(data = data, columns = ['gid', 'player', 'bot', 'winner', 'longest_road', 'largest_army',
                                              'gained_lr', 'lost_lr', 'gained_la', 'lost_la', 'game_len',
                                              'num_knights', 'num_road'])
    dfs = []
    for g, gdf in df.groupby('gid'):
        bot_game = False
        if np.any(gdf.bot):
            bot_game = True
        
        gdf['bot_game'] = bot_game
        dfs.append(gdf)
        
    df = pd.concat(dfs)
    
    botless_df = df[df.bot_game == False]
    
    #%%
    
    odds_with_lr = len(df[(df.longest_road) & (df.winner)])/len(df[df.longest_road])
    odds_with_la = len(df[(df.largest_army) & (df.winner)])/len(df[df.largest_army])
    
    
    botless_odds_with_lr = len(botless_df[(botless_df.longest_road) & (botless_df.winner)])/len(botless_df[botless_df.longest_road])
    botless_odds_with_la = len(botless_df[(botless_df.largest_army) & (botless_df.winner)])/len(botless_df[botless_df.largest_army])
    
    num_roads = df[df.longest_road].num_road.mean()
    
    #%%
    
    
    
    
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
            ever_gained_la = len(rrow[1].gained_la) > 0
            ever_gained_lr = len(rrow[1].gained_lr) > 0
            
            datarow = [g, rrow[1].player, rrow[1].winner, fg_la, fg_lr, ever_gained_la, ever_gained_lr]
            data.append(datarow)
            
    ddf = pd.DataFrame(data = data, columns = ['gid', 'player', 'winner', 'fg_la', 'fg_lr', 'ever_gained_la', 'ever_gained_lr'])
    

    #%%
    
    data = []
    for g, gdf in df.groupby('gid'):
        lr_owner = None
        la_owner = None
        prev_turn = 0
        tot_turns = gdf.game_len.max()
        for i in np.arange(0,1.05,0.05):
            for _, row in gdf.iterrows():
                for t in row.gained_lr:
                    if prev_turn < t < tot_turns * i:
                        lr_owner = row.player
                    
                for t in row.gained_la:
                    if prev_turn < t < tot_turns * i:
                        la_owner = row.player
            
                newrow = [g, row.player, i, lr_owner == row.player, la_owner == row.player, 
                          row.bot_game, row.winner, row.longest_road, row.largest_army]
                data.append(newrow)
            
            prev_turn = tot_turns * i
            
    dddf = pd.DataFrame(data = data, columns = ['gid', 'player', 'per_turn', 'lr', 'la', 'bot', 'winner', 'end_lr', 'end_la'])
    
    
    
    #%%
    data = []
    for g, gdf in dddf.groupby('per_turn'):
        if len(gdf[gdf.lr]):
            odds_win_lr = 100*len(gdf[(gdf.lr) & (gdf.winner)])/len(gdf[gdf.lr])
            odds_end_lr = 100*len(gdf[(gdf.lr) & (gdf.end_lr)])/len(gdf[gdf.lr])
        else:
            odds_win_lr = None
            odds_end_lr = None
        if len(gdf[gdf.la]):
            odds_win_la = 100*len(gdf[(gdf.la) & (gdf.winner)])/len(gdf[gdf.la])
            odds_end_la = 100*len(gdf[(gdf.la) & (gdf.end_la)])/len(gdf[gdf.la])
        else:
            odds_win_la = None
            odds_end_la = None
        
        
        
        
        row = [g*100, odds_win_lr, odds_win_la, odds_end_lr, odds_end_la, len(gdf[gdf.lr]), len(gdf[gdf.la])]
        data.append(row)
    
    odds_df = pd.DataFrame(data = data, columns = ['per_turn', 'odds_win_lr', 'odds_win_la', 
                                                   'odds_end_lr', 'odds_end_la', 'num_lr', 'num_la'])
    

    
        
    #%%
    data = []
    for g, gdf in dddf[dddf.bot == False].groupby('per_turn'):
        if len(gdf[gdf.lr]):
            odds_win_lr = 100* len(gdf[(gdf.lr) & (gdf.winner)])/len(gdf[gdf.lr])
            odds_end_lr = 100*len(gdf[(gdf.lr) & (gdf.end_lr)])/len(gdf[gdf.lr])
        else:
            odds_win_lr = None
            odds_end_lr = None
        if len(gdf[gdf.la]):
            odds_win_la = 100*len(gdf[(gdf.la) & (gdf.winner)])/len(gdf[gdf.la])
            odds_end_la = 100*len(gdf[(gdf.la) & (gdf.end_la)])/len(gdf[gdf.la])
        else:
            odds_win_la = None
            odds_end_la = None
        
        
        
        
        row = [g*100, odds_win_lr, odds_win_la, odds_end_lr, odds_end_la, len(gdf[gdf.lr]), len(gdf[gdf.la])]
        data.append(row)
    
    botless_odds_df = pd.DataFrame(data = data, columns = ['per_turn', 'odds_win_lr', 'odds_win_la', 
                                                   'odds_end_lr', 'odds_end_la', 'num_lr', 'num_la'])
            
    
    #%%
    
    fig, axs = plt.subplots(1,2)
    
    sns.lineplot(ax = axs[0], x = 'per_turn', y = 'odds_end_lr', data = odds_df[odds_df.num_lr > 20])
    sns.lineplot(ax = axs[0], x = 'per_turn', y = 'odds_end_lr', data = botless_odds_df[botless_odds_df.num_lr > 20])
    
    axs[0].set_title('Will You Finish with Longest Road?')
    axs[0].set_ylabel('Odds of Finishing with LR (%)')
    axs[0].set_xlabel('Percent of Game Completed')
    # plt.legend(['All Games', 'Human Only Games'])
    

    
    sns.lineplot(ax = axs[1], x = 'per_turn', y = 'odds_end_la', data = odds_df[odds_df.num_la > 20])
    sns.lineplot(ax = axs[1], x = 'per_turn', y = 'odds_end_la', data = botless_odds_df[botless_odds_df.num_la > 20])
    
    axs[1].set_title('Will You Finish with Largest Army?')
    axs[1].set_ylabel('Odds of Finishing with La (%)')
    axs[1].set_xlabel('Percent of Game Completed')
    plt.legend(['All Games', 'Human Only Games'])
    
    #%%
    fig, axs = plt.subplots(1,2)
    
    sns.lineplot(ax = axs[0], x = 'per_turn', y = 'odds_win_lr', data = odds_df[odds_df.num_lr > 20])
    sns.lineplot(ax = axs[0], x = 'per_turn', y = 'odds_win_lr', data = botless_odds_df[botless_odds_df.num_lr > 20])
    
    axs[0].set_title('Will You Win with Longest Road?')
    axs[0].set_ylabel('Odds of Winning with LR (%)')
    axs[0].set_xlabel('Percent of Game Completed')
    axs[0].axhline(25, color = 'r')

    
    sns.lineplot(ax = axs[1], x = 'per_turn', y = 'odds_win_la', data = odds_df[odds_df.num_la > 20])
    sns.lineplot(ax = axs[1], x = 'per_turn', y = 'odds_win_la', data = botless_odds_df[botless_odds_df.num_la > 20])
    
    axs[1].set_title('Will You Win with Largest Army?')
    axs[1].set_ylabel('Odds of Win with La (%)')
    axs[1].set_xlabel('Percent of Game Completed')
    axs[1].axhline(25, color = 'r')
    plt.legend(['All Games', 'Human Only Games'])
