# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 19:17:36 2021

@author: alext
"""


from bs4 import BeautifulSoup
import os
# import anvil.server
# from anvil.tables import app_tables
import json

from catan.game_class import Game

# def read_anvil_games():
#     '''
#     read all the json data from anvil and return a list of each game as a game class

#     Returns
#     -------
#     games : list of game classes
#         DESCRIPTION.

#     '''
#     anvil.server.connect('')
#     jsons = [r['json_text'] for r in app_tables.submitted_data.search()]
#     print(len(jsons))
#     games = []
#     for j in jsons:
#         jdata = json.loads(j)
#         game = Game(jsondata=jdata)
#         game.read_json()
#         game.game_over_calcs()
#         games.append(game)
#     return games
        
        
    
def read_all_games(start = 0, end = None):
    '''
    read games from local html files

    Parameters
    ----------
    start : int, optional
        if only reading a subset, where to start from. The default is 0.
    end : int, optional
        if only reading a subset, where to end. The default is None.

    Returns
    -------
    games : list of game classes
        DESCRIPTION.

    '''
    fnames = []
    fnums = []
    path = ""
    for file in os.listdir(path):
        if file.endswith(".html"):
            fnames.append(file)
            a = file.split(".")
            
            fnum = a[0].split(' ')
            
            fnums.append(int(fnum[-1]))
        
    if not end:
        end = max(fnums) +1
    
    games = []
    for i in range(len(fnames)):
        if start < fnums[i] and fnums[i] < end: 
            fname = fnames[i]
        else:
            continue
        try: 
            with open(path+'/'+fname, encoding = 'utf-8') as fp:
                soup = BeautifulSoup(fp, 'html.parser')
            
            
            
            newgame = Game(soup)
            newgame.read_html()
    
            
            games.append(newgame)
        except:
            print(fname)
            
    return games

def export_jsons(games):
    jsons = {}
    gcount = 0
    for game in games:
        gcount += 1
        j = game.jsonify_data()
        jsons[gcount] = j
    with open('catan_games.txt', 'w') as outfile:
        json.dump(jsons, outfile)
    

if __name__ == '__main__':
    
    
    games = read_all_games()
    export_jsons(games)
            

    
            
        
    # pickle.dump(games, open('colonist_games.pickle', 'wb'))
                
                
                
