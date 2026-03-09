# Imports
import pandas as pd
import fetch_data
import config
import numpy as np
import indicators
from datetime import timedelta,datetime

# Provides an average of stock prices given a range (50 or 200) and signals overall trends by filtering noise 
def  ma_band_signal(ma, current_p, band=0.1):
    if current_p < ma*(1-band):
        return -1 # Sell/Short Signal
    elif current_p > ma*(1+band) :
        return 1 # Buy Signal
    else:
        return 0 # Indeterminate Signal

def volatility_check(rv_df, vol_threshold):
    """
    Take precentage and compre df vol to current vol, if current vol is lower than x% of the total vols then trade else no
    ex if vol_t is 70 and vol df gives 5 6 1 52 36 78 21 56 75 41 and current vol is 7, its lower than 70% of the given vol so tradable
    """
    current_vol = rv_df["Volatility"].iloc[-1]
    total = len(rv_df)-1
    count = 0
    for x in range(total):
        if rv_df["Volatility"].iloc[x] > current_vol:
            count+=1
    if count/total > (vol_threshold*0.01):
        return True
    else:
        return False

# RSI 
def RSI(dr_df):
    Gains = 0
    Loss = 0
    sum_g = 0
    sum_l = 0

    for x in range(len(dr_df)):
        temp = dr_df["Returns"] .iloc[x]
        if temp > 0:
            Gains+=temp
            sum_g+=1
        else: 
            Loss+=temp * -1
            sum_l+=1
    
    avg_Gain = Gains/sum_g
    avg_Loss = Loss/sum_l
    
    Relative_Strength = avg_Gain/avg_Loss
    Relative_Strength_Index = 100 - (100/(1+Relative_Strength))

    return Relative_Strength_Index

def RSI_Check(dr_df,prev_df):
    current_RSI = RSI(dr_df)
    prev_RSI = RSI(prev_df)

    if prev_RSI < 30 and current_RSI > 30:
        return 1 # Momnetum mocing back up to equlibrium
    elif prev_RSI > 70 and current_RSI < 70:
        return -1 # Momentum moving back down
    else:
        return 0 # Neutral Movement

# Volume Check
def volume_check(dr_df):
    sum = 0
    counter = 0
    for x in range(len(dr_df)):
        sum+=dr_df["Volume"].iloc[x]
        counter+=1
    
    avg_vol = sum/counter

    if dr_df["Volume"].iloc[len(dr_df)-1] > avg_vol:
        return 1
    else:
        return 0
    
# Max Dropdown

def max_drawdown(normal_df):
    peak = normal_df["Close"].iloc[0]
    max_drawdown = 0
    for x in range(len(normal_df)-1):

        price = normal_df["Close"].iloc[x]
        if price > peak:
            peak = price
    
        drawdown = (price-peak)/peak
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    if max_drawdown >= -0.2:
        return 1
    else:
        return 0 
        