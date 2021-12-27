# -*- coding: utf-8 -*-
"""
Created on Mon Dec  6 09:34:48 2021

@author: alext
"""
from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

if __name__ == '__main__': 
    
    url = 'https://colonist.io/api/profile/alex84723'
    res = requests.get(url)
    if res.ok:
        data = res.json()
    #     soup = BS(res.content, 'html.parser')
        
    #     wins = soup.find('h5', {'id': 'wins_stat'})
    #     games = soup.find('h5', {'id': 'games_stat'})
    #     total_points = soup.find('h5', {'id': 'points_stat'})
    #     win_rate = soup.find('h5', {'id': 'win_ratio_stat'})
    #     points_per_game = soup.find('h5', {'id': 'pg_stat'})
    #     total_games = soup.find('h5', {'id': 'total_games_stat'})
        
        
        