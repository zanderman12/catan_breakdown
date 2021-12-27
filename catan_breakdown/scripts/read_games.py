# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 19:17:36 2021

@author: alext
"""


from bs4 import BeautifulSoup
import os
import json
import scipy.stats as stats
import pickle
import numpy as np

class Turn:
    def __init__(self, turnnumber):
        self.turn = turnnumber
        self.roll = 0
        self.player = ''
        self.playertype = ''
        self.built = {'road': 0,
                      'settlement': 0,
                      'city': 0,
                      'dev_card': 0}
        self.dev_cards_built = ''
        self.trades = []
        self.resources_rolled = {'grain': 0, 'wool': 0, 'ore': 0, 'lumber': 0, ' brick': 0}
        self.robber = []
        self.bank_out_of_resource = ''
        self.player_point_totals = {}
        
    def return_json(self):
        turndict = {'turn': self.turn,
                    'roll': self.roll,
                    'player': self.player,
                    'player_type': self.playertype,
                    'built': self.built,
                    'devcard_played': self.dev_cards_built,
                    'resources_gained_through_roll': self.resources_rolled}
        
        trades = []
        for t in self.trades:
            trades.append(t.__dict__)
        
        turndict['trades'] = json.dumps(trades)
        
        robbers = []
        for r in self.robber:
            robbers.append(r.__dict__)
            
        turndict['robbers'] = json.dumps(robbers)
        
        return turndict
        
        
class Trade:
    def __init__(self, p1, p2, p1resources, p2resources):
        self.p1 = p1
        self.p2 = p2
        self.p1resources = p1resources
        self.p2resources = p2resources
        
class Robber:
    def __init__(self, p1, p2, stolen_resource):
        self.p1 = p1
        self.p2 = p2
        self.stolen_resource = stolen_resource
        
class Player:
    def __init__(self, pname):
        self.name = pname
        self.points = 2
        self.current_resources = {}
        self.total_resources = {}
        self.robber_discards = {}
        for i in ['grain', 'wool', 'ore', 'lumber', ' brick']:
            self.current_resources[i] = 0
            self.total_resources[i] = 0
            self.robber_discards[i] = 0
            
        self.built = {'road': 2,
                      'settlement': 2,
                      'city': 0,
                      'dev_card': 0}
        self.longest_road = False
        self.largest_army = False
        self.played_cards = []
        self.starting_resources = []
        self.trades = []
        self.gained_largest_army = []
        self.gained_longest_road = []
        self.lost_largest_army = []
        self.lost_longest_road = []
        self.proposed_trades = []
        
    def return_json(self):
        pdict = {'name': self.name,
                 'points': self.points,
                 'current_resources': self.current_resources,
                 'total_resources': self.total_resources,
                 'robber_discards': self.robber_discards,
                 'built': self.built,
                 'longest_road': self.longest_road,
                 'largest_army': self.largest_army,
                 'played_cards': self.played_cards,
                 'starting_resources': self.starting_resources,
                 'turn_gained_largest_army': self.gained_largest_army,
                 'turn_gained_longest_road': self.gained_longest_road,
                 'turn_lost_largest_army': self.lost_largest_army,
                 'turn_lost_longest_road': self.lost_longest_road,
                 }
        
        accepted_trades = []
        for t in self.trades:
            accepted_trades.append(t.__dict__)
        
        pdict['accepted_trades'] = accepted_trades
        
        proposed_trades = []
        for t in self.proposed_trades:
            proposed_trades.append(t.__dict__)
        
        pdict['proposed_trades'] = proposed_trades
        
        return pdict
        
class Game:
    def __init__(self, html):
        self.turns = []
        self.winner = ''
        self.players = {}
        self.all_rolls = []
        self.roll_odds = {2: 1,
                     3: 2,
                     4: 3,
                     5: 4,
                     6: 5,
                     7: 6,
                     8: 5,
                     9: 4,
                     10: 3,
                     11: 2,
                     12: 1}
        self.robber_locations = []
        self.html = html
        
    
        
        
    def jsonify_data(self):
        gdict = {'winner': self.winner}
        
        turns = []
        for t in self.turns:
            turns.append(t.return_json())
            
        gdict['turns'] = turns
        
        players = []
        for p in self.players.values():
            players.append(p.return_json())
            
        gdict['players'] = players
        
        return json.dumps(gdict)
    
    def dice_fairness(self):
        numrolls = len(self.all_rolls)
        rolldict = {2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0}
        for i in self.all_rolls:
            rolldict[i] += 1
            
        obs = []
        exp = []
        for i in rolldict.keys():
            obs.append(rolldict[i])
            exp.append(self.roll_odds[i]*numrolls/36)
            
        c, p = stats.chisquare(f_obs = obs, f_exp=exp)
        
        return [c,p, obs, exp]
        
    
    def game_over_calcs(self):
        self.determine_resource_numbers()
        self.resource_availability()
        self.dice_chisq = self.dice_fairness()
    
    def determine_resource_numbers(self):
        ndict = {}
        rdict = {'grain': [],
                 'wool': [], 
                 'ore': [], 
                 'lumber': [], 
                 ' brick': []}
        
        for i in range(2,13):
            ndict[i] = []
            
        for t in self.turns:
            for r in t.resources_rolled.keys():
                if t.resources_rolled[r] > 0:
                    if r not in ndict[t.roll]:
                        ndict[t.roll].append(r)
                    if t.roll not in rdict[r]:
                        rdict[r].append(t.roll)
        
        
        
                
        self.ndict = ndict
        self.rdict = rdict
        
    def resource_availability(self):
        
        
        availdict = {}
        availdictodds = {}
        for r in self.rdict.keys():
            availdict[r] = 0
            for n in self.rdict[r]:
                availdict[r] += self.roll_odds[n]
                
        missing_numbers = []
        missing_resources = []
        for i in [2, 12]:
            if len(self.ndict[i]) < 1:
                missing_numbers.append(i)
        for i in [3,4,5,6,8,9,10,11]:
            if len(self.ndict[i]) < 2:
                for j in range(2-len(self.ndict[i])):
                    missing_numbers.append(i)
        
        for j in ['grain', 'wool', 'lumber']:
            if len(self.rdict[j]) < 4:
                for i in range(4-len(self.rdict[j])):
                    missing_resources.append(j)
        for j in ['ore', ' brick']:
            if len(self.rdict[j]) < 3:
                for i in range(3-len(self.rdict[j])):
                    missing_resources.append(j)
        
        missing_odds = [self.roll_odds[n] for n in missing_numbers]
        avg_missing_odds = np.mean(missing_odds)
        
        for r in missing_resources:
            availdict[r] += avg_missing_odds
                
        for r in availdict.keys():
            availdictodds[r] = availdict[r]/58 #58 dots total on the board
        self.availdict = availdict
        self.availdictodds = availdictodds
    
                        
    def read_html(self):
        threads = self.html.find_all('div', attrs = {'class': 'main_block game_chat_block'})
        turnposts = threads[0].find_all('div', attrs = {'class': 'message_post'})
        
        newturn = 0
        current_turn = 0
        possible_resources = ['grain', 'wool', 'ore', 'lumber', ' brick']
        for i in turnposts:
            
            if i.text == '':
                current_turn += 1
                if newturn:
                    self.turns.append(newturn)
                newturn = Turn(current_turn)
                newturn.player_point_totals = {}
                for p in self.players.keys():
                    newturn.player_point_totals[p] = self.players[p].points
                    
                
            elif 'rolled' in i.text:
                user = i.text.split(' ')[0]
                b = i.find_all('img')
                roll = 0
                for j in b:
                    if 'dice' in j['alt']:
                        roll += int(j['alt'][-1])
                              
                self.all_rolls.append(roll)
                newturn.playertype = b[0]['alt']
                newturn.roll = roll
                newturn.player = user
                
                
            elif 'starting resources' in i.text:
                user = i.text.split(' ')[0]
                
                newplayer = Player(user)
                
                b = i.find_all('img')
                
                for j in b:
                    if j['alt'] in possible_resources:
                        newplayer.starting_resources.append(j['alt'])
                        newplayer.current_resources[j['alt']] += 1
                        newplayer.total_resources[j['alt']] += 1
                
                self.players[user] = newplayer
                current_turn = 0
                self.turns = []
            
            elif 'got' in i.text: 
                user = i.text.split(' ')[0]
                
                for j in i.find_all('img'):
                    if j['alt'] in possible_resources:
                        self.players[user].current_resources[j['alt']] += 1
                        self.players[user].total_resources[j['alt']] += 1
                        
                        newturn.resources_rolled[j['alt']] += 1
                                
            elif 'built' in i.text:
                user = i.text.split(' ')[0]
                
                for j in i.find_all('img'):
                    if j['alt'] in ['road', 'settlement', 'city']:
                        self.players[user].built[j['alt']] += 1
                        if j['alt'] == 'settlement':
                            self.players[user].points += 1
                            for spentres in ['lumber', 'grain', 'wool', ' brick']:
                                self.players[user].current_resources[spentres] -= 1
                        elif j['alt'] == 'city':
                            self.players[user].points += 1
                            for spentres in ['ore', 'ore', 'ore', 'grain', 'grain']:
                                self.players[user].current_resources[spentres] -= 1
                        
                        elif j['alt'] == 'road':
                            
                            for spentres in ['lumber', ' brick']:
                                self.players[user].current_resources[spentres] -= 1
                           
                        if newturn:
                            newturn.built[j['alt']] += 1
                        
            elif 'bought' in i.text:
                user = i.text.split(' ')[0]
                
                self.players[user].built['dev_card'] += 1
                
                
                for spentres in ['ore', 'grain', 'wool']:
                    self.players[user].current_resources[spentres] -= 1
                        
                if newturn:
                    newturn.built['dev_card'] += 1
                
            elif 'received' in i.text and 'starting' not in i.text:
                user = i.text.split(' ')[0]
                for j in i.find_all('img'):
                    if j['alt'] =='largest army':
                        self.players[user].largest_army = True
                        self.players[user].gained_largest_army.append(current_turn)
                        self.players[user].points += 2
                    elif j['alt'] == 'largest road':
                        self.players[user].longest_road = True
                        self.players[user].gained_longest_road.append(current_turn)
                        self.players[user].points += 2
                        
            elif 'won' in i.text:
                user = i.text.split(' ')[1]
                self.winner = user
                    
                
            elif 'discarded' in i.text:
                user = i.text.split(' ')[0]
                
                for j in i.find_all('img'):
                    if j['alt'] in possible_resources:
                        self.players[user].robber_discards[j['alt']] += 1
                        
            elif 'used' in i.text:
                
                user = i.text.split(' ')[0]
                for c in ['Knight', 'Monopoly', 'Road Building', 'Year of Plenty']:
                    if c in i.text:
                        self.players[user].played_cards.append(c)
                        newturn.dev_cards_built = c
                        
                    if c == 'Road Building':
                        self.players[user].built['road'] += 2
                        
            elif 'gave' in i.text:
                user = i.text.split(' ')[0]
                #trade with bank
                a = BeautifulSoup(str(i).split('and took')[0], 'html.parser')
                
                tobank = []
                for j in a.find_all('img'):
                    if j['alt'] in possible_resources:
                        tobank.append(j['alt'])
                        self.players[user].current_resources[j['alt']] -= 1
                        
                b = BeautifulSoup(str(i).split('and took')[1], 'html.parser')
                frombank = []
                for j in b.find_all('img'):
                    if j['alt'] in possible_resources:
                        frombank.append(j['alt'])
                        self.players[user].current_resources[j['alt']] += 1
                        
                newtrade = Trade(user, 'bank', tobank, frombank)
                self.players[user].trades.append(newtrade)
                newturn.trades.append(newtrade)
                
                
            elif 'stole' in i.text and 'all' not in i.text:
                user = i.text.split(' ')[0]
                victim = i.text.split(' ')[-1]
                if victim:
                
                    if user == 'You':
                        user = 'alex84723'
                    if victim == 'you':
                        victim = 'alex84723'
                        
                    for j in i.find_all('img'):
                        if j['alt'] in possible_resources:
                            newsteal = Robber(user, victim, j['alt'])
                            self.players[user].current_resources[j['alt']] += 1
                            self.players[user].total_resources[j['alt']] += 1
                            self.players[victim].current_resources[j['alt']] += 1
                            if newturn:
                                newturn.robber.append(newsteal)
                
            elif 'passed' in i.text:
                victimtext = i.text.split('to:')[0]
                usertext = i.text.split('to:')[1]

                for p in self.players.keys():
                    if p in usertext:
                        user = p
                    if p in victimtext:
                        victim = p
                

                for j in i.find_all('img'):
                    if j['alt'] == 'longest road':
                        self.players[user].longest_road = True
                        self.players[user].gained_longest_road.append(current_turn)
                        self.players[user].points += 2
                        self.players[victim].longest_road = False
                        self.players[victim].lost_longest_road.append(current_turn)
                        self.players[victim].points -= 2
                    elif j['alt'] == 'largest army':
                        self.players[user].largest_army = True
                        self.players[victim].largest_army = False
                        self.players[user].gained_largest_army.append(current_turn)
                        self.players[victim].lost_largest_army.append(current_turn)
                        self.players[user].points += 2
                        self.players[victim].points -= 2
            elif 'traded' in i.text:
                user = i.text.split(' ')[0]
                partner = i.text.split(' ')[-1]
                
                a = BeautifulSoup(str(i).split('for:')[0], 'html.parser')
                topartner = []
                for j in a.find_all('img'):
                    if j['alt'] in possible_resources:
                        topartner.append(j['alt'])
                        self.players[user].current_resources[j['alt']] -= 1
                        self.players[partner].current_resources[j['alt']] += 1
                        
                b = BeautifulSoup(str(i).split('for:')[1], 'html.parser')
                frompartner = []
                for j in b.find_all('img'):
                    if j['alt'] in possible_resources:
                        frompartner.append(j['alt'])
                        self.players[user].current_resources[j['alt']] += 1
                        self.players[partner].current_resources[j['alt']] -= 1
                        
                newtrade = Trade(user, partner, topartner, frompartner)
                newturn.trades.append(newtrade)
                self.players[user].trades.append(newtrade)
                self.players[partner].trades.append(newtrade)
                
            elif 'wants to give' in i.text:
                user = i.text.split(' ')[0]
                
                a = BeautifulSoup(str(i).split('for:')[0], 'html.parser')
                topartner = []
                for j in a.find_all('img'):
                    if j['alt'] in possible_resources:
                        topartner.append(j['alt'])
                        
                b = BeautifulSoup(str(i).split('for:')[1], 'html.parser')
                frompartner = []
                for j in b.find_all('img'):
                    if j['alt'] in possible_resources:
                        frompartner.append(j['alt'])
                        
                proposed_trade = Trade(user, None, topartner, frompartner)
                self.players[user].proposed_trades.append(proposed_trade)
                
            elif 'took from bank' in i.text:
                user = i.text.split(' ')[0]
                
                for j in i.find_all('img'):
                    if j['alt'] in possible_resources:
                        self.players[user].current_resources[j['alt']] += 1
                        self.players[user].total_resources[j['alt']] += 1
                
            elif 'stole all' in i.text:
                user = i.text.split(' ')[0]
                
                total_stolen = 0
                stolen_resource = ''
                for j in i.find_all('img'):
                    if j['alt'] in possible_resources:
                        stolen_resource = j['alt']
                        for p in self.players.keys():
                            if p != user:
                                total_stolen += self.players[p].current_resources[j['alt']]
                                self.players[p].current_resources[j['alt']] = 0
                                
                self.players[user].current_resources[stolen_resource] += total_stolen
                
                
            elif 'moved' in i.text:
                
                imgs = i.find_all('img')[-2:]
                self.robber_locations.append((newturn.turn, imgs[0]['alt'], imgs[1]['alt']))
            
            elif 'bank to distribute' in i.text:
                for j in i.find_all('img'):
                    newturn.bank_out_of_resource = j['alt']
                    
            # else:
            #     print(i.text)
                
        self.game_over_calcs()
        
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
    fnames = []
    path = "C:/Users/alext/Desktop/projects/website/blog/colonist game/saved_html"
    for file in os.listdir(path):
        if file.endswith(".html"):
            fnames.append(file)
            
    
    games = []
    for fname in fnames[200:202]:
        try: 
            with open(path+'/'+fname, encoding = 'utf-8') as fp:
                soup = BeautifulSoup(fp, 'html.parser')
            
            
            
            newgame = Game(soup)
            newgame.read_html()
    
            
            games.append(newgame)
        except:
            print(fname)
            

    
            
        
    # pickle.dump(games, open('colonist_games.pickle', 'wb'))
                
                
                