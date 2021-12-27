# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 19:17:36 2021

@author: alext
"""


from bs4 import BeautifulSoup
import os
import anvil.server
from anvil.tables import app_tables
import json

from catan.game_class import Game

def read_anvil_games():
    anvil.server.connect('TTNUYQ34ZJ6WS6PAZYSTSPME-L7PJBIQLBF6QMRJF')
    jsons = [r['json_text'] for r in app_tables.submitted_data.search()]
    print(len(jsons))
    games = []
    for j in jsons:
        jdata = json.loads(j)
        game = Game(jsondata=jdata)
        game.read_json()
        games.append(game)
    return games
        
        
    
def read_all_games(start = 0, end = None):
    fnames = []
    fnums = []
    path = "C:/Users/alext/Desktop/projects/website/blog/colonist game/saved_html"
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

if __name__ == '__main__':
    # fnames = []
    # path = "C:/Users/alext/Desktop/projects/website/blog/colonist game/saved_html"
    # for file in os.listdir(path):
    #     if file.endswith(".html"):
    #         fnames.append(file)
            
    
    # games = []
    # for fname in fnames[200:202]:
    #     try: 
    #         with open(path+'/'+fname, encoding = 'utf-8') as fp:
    #             soup = BeautifulSoup(fp, 'html.parser')
            
            
            
    #         newgame = Game(soup)
    #         newgame.read_html()
    
            
    #         games.append(newgame)
    #     except:
    #         print(fname)
    
    a = read_anvil_games()
            

    
            
        
    # pickle.dump(games, open('colonist_games.pickle', 'wb'))
                
                
                