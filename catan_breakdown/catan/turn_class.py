# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 16:52:31 2021

@author: alext
"""
import json

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