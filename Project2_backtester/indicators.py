# Imports
import pandas as pd
import yfinance as yf
import fetch_data
import config
import numpy as np
from datetime import timedelta,datetime

# Processes and gives daily precent change of a given ticker between a given range
def compute_daily_returns(data,ticker):
    rows = []
    for x in range(1, len(data["Close"])):
        daily_return = (data["Close"].iloc[x]-data["Close"].iloc[x-1])/data["Close"].iloc[x-1]
        row = {
            "Date": data.index[x],
            "Returns": daily_return,
            "Returns (%)": daily_return*100,
        }
        rows.append(row)
    dr_df = pd.DataFrame(rows)
    #dr_df.to_csv(f"{ticker}_returns.csv")

    return(dr_df)


# Processes and gives log-scaled change signal of a given ticker between a given range
def compute_log_returns(data, ticker):
    rows = []
    for x in range(1, len(data["Close"])):
        daily_return = np.log(data["Close"].iloc[x])-np.log(data["Close"].iloc[x-1]) # numpy.log = ln
        row = {
            "Date": data.index[x],
            "Log Returns": daily_return,
        }
        rows.append(row)
    drl_df = pd.DataFrame(rows)
    #drl_df.to_csv(f"{ticker}_log_returns.csv")

    return(drl_df)

# Provides an average of stock prices given a range (50 or 200) and signals overall trends by filtering noise 
def compute_moving_average(data, window=0, ticker=config.symbol):
    sum = 0
    days = len(data["Close"])
    if window == 0:
        window = len(data["Close"])
    for x in range(days):
        sum+=data["Close"].iloc[x]
    moving_avg = sum/days
    current_price = data["Close"].iloc[days-1]


    return moving_avg, current_price

# Provides a measures of how much the returns deviate from their average over a given window
def compute_rolling_volatility(return_data, ticker):
    days = len(return_data["Returns"])
    variance = 0
    rows=[]
    for y in range(config.rv_window-1, days+1):
        sum = 0
        for x in range(y-config.rv_window,y):
            sum+=return_data["Returns"].iloc[x]
        mean = sum/config.rv_window
        variance = 0
        for z in range(y-config.rv_window,y):
            variance+=(return_data["Returns"].iloc[z]-mean)**2
        rolling_v = (variance/(config.rv_window-1))**(1/2)

        row = {
            "Date": return_data["Date"].iloc[y-1],
            "Volatility": rolling_v,
        }
        rows.append(row)
    rv_df = pd.DataFrame(rows)
    #rv_df.to_csv(f"{ticker}_Volatility.csv")
    return rv_df