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
    dr_df.to_csv(f"{ticker}_returns.csv")

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
    drl_df.to_csv(f"{ticker}_log_returns.csv")

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
    if current_price < moving_avg*0.975:
        status = "Bearish (Sell Signal)"
    elif current_price > moving_avg*1.025 :
        status = "Bullish (Buy Signal)"
    else:
        status = "Neutral (Indecisive)"    
    rows =[]
    row = {
            "Window": str(window),
            "Stock":str(ticker),
            "Current Price": str(round(current_price, 2)),
            "MA": str(round(moving_avg, 2)),
            "Signal": status,
        }
    rows.append(row)
    ma_df = pd.DataFrame(rows)
    #ma_df.to_csv(f"{ticker}_moving_avg.csv")
    return ma_df

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
    rv_df.to_csv(f"{ticker}_Volatility.csv")
    return rv_df

def compute_sharpe_ratio(rv_data, dr_df):
    # Extract Last line of volatility and ma value
    volatility = rv_data["Volatility"].iloc[len(rv_data)-1]
    rfr = config.risk_free_rate/252
    avg_dr = dr_df["Returns"].mean()

    # Formula: 
    sharpe_r = (avg_dr-rfr)/volatility
    sharpe_r_annual = sharpe_r * np.sqrt(252)

    if sharpe_r_annual < 0:
        status = "Losing money relative to risk-free, bad"
    elif sharpe_r_annual < 1:
        status = "Not great, barely compensating for risk"
    elif sharpe_r_annual < 2:
        status = "Decent, acceptable in industry"
    elif sharpe_r_annual < 3:
        status = "Excellent, best than industry median"
    else:
        status = "Exceptional, Quant/Hedgefund level"    
    rows =[]
    row = {
            "SharpeR": str(sharpe_r),
            "SharpeR_A":str(sharpe_r_annual),
            "Signal": status,
        }
    rows.append(row)
    sr_df = pd.DataFrame(rows)

    return sr_df
    
def compute_max_drawdown(data, window):
    max_track = []
    total_days = len(data["Close"])
    for x in range(window, total_days+1):
        max_v = data["Close"].iloc[x-window]
        for y in range(x-window,x):
            if data["Close"].iloc[y] > max_v:
                max_v = data["Close"].iloc[y]
        max_track.append(max_v)
    draw_down_lst = []
    max_track_idx = 0
    for z in range(window, total_days+1):
        max_down = 0
        for a in range(z-window,z):
            close = data["Close"].iloc[a]
            draw_down = (close-max_track[max_track_idx])/max_track[max_track_idx]
            if draw_down < max_down:
                max_down = draw_down
        draw_down_lst.append(max_down)
        max_track_idx+=1
    mdd_value = "Max Draw-Down over a "+ str(window) + " period is "+str(min(draw_down_lst)*100)+"%"
    return mdd_value
    
if __name__ == "__main__":

    # Inputs
    stock = input("Enter Stock Ticker: ") or config.symbol
    mode = input("Would you like info between dates or a day-window? (D or W): ").upper() or config.mode

    # Dates
    if mode == "D": 
        start_date = input("Enter Start Date: ") or config.start_date
        end_date = input("Enter End Date: ") or config.end_date
    
    # Day-Range
    else:
        n_days = input("Please input day window: ") or config.day_range
        r_days_w = int(n_days)+(config.rv_window - 1)
        mdd_days = int(n_days)+int(n_days)-1
        days_w = int(n_days)
        buffer1 = days_w*1.5
        buffer2 = r_days_w*1.5
        buffer3 = mdd_days*1.5
        start_date = (datetime.today() - timedelta(days=int(buffer1))).strftime("%Y-%m-%d")
        rv_start_date = (datetime.today() - timedelta(days=int(buffer2))).strftime("%Y-%m-%d")
        mdd_start_date = (datetime.today() - timedelta(days=int(buffer3))).strftime("%Y-%m-%d")
        end_date = datetime.today().strftime("%Y-%m-%d")
    
    # Fail-Case
    if start_date == None:
        start_date = "2025-01-01"
    if end_date == None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    # Fetch Data
    df = fetch_data.fetch_data(stock, start_date, end_date)
    rdf = fetch_data.fetch_data(stock, rv_start_date, end_date)
    mdd_df = fetch_data.fetch_data(stock, mdd_start_date, end_date)

    # Processes
    if mode == "D":
        dr_df = compute_daily_returns(df,stock)
        drl_df = compute_log_returns(df, stock)
        ma_df = compute_moving_average(df,0,stock)
        rv_df = compute_rolling_volatility(compute_daily_returns(rdf, stock),stock)
        s_r = compute_sharpe_ratio(rv_df, dr_df)
    else:
        dr_df = compute_daily_returns(df, stock)
        drl_df = compute_log_returns(df, stock)
        ma_df = compute_moving_average(df,days_w,stock)
        rv_df = compute_rolling_volatility(compute_daily_returns(rdf, stock), stock)
        sr_dr = compute_sharpe_ratio(rv_df, dr_df)
        mdd = compute_max_drawdown(mdd_df,days_w)
        
    # Outputs
    print(ma_df)
    print(sr_dr)
    print(mdd)