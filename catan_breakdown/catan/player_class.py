# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 16:52:52 2021

@author: alext
"""
import json 

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