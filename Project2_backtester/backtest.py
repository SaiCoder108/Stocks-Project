# Imports
import pandas as pd
import yfinance as yf
import config
import fetch_data
import indicators as ind
import numpy as np
import strategy 
from datetime import timedelta,datetime

def compute_sharpe_ratio(rv_data, dr_df):
    # Extract Last line of volatility and ma value
    volatility = rv_data["Volatility"].iloc[len(rv_data)-1]
    rfr = config.risk_free_rate/252
    avg_dr = dr_df["Returns"].mean()

    # Formula: 
    sharpe_r = (avg_dr-rfr)/volatility
    sharpe_r_annual = sharpe_r * np.sqrt(252)

    if sharpe_r_annual >= 3:
        return 1
    else: 
        return 0

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
        dr_df = ind.compute_daily_returns(df,stock)
        rv_df = ind.compute_rolling_volatility(ind.compute_daily_returns(rdf, stock),stock)
        s_r = compute_sharpe_ratio(rv_df, dr_df)
    else:
        dr_df = ind.compute_daily_returns(df, stock)
        rv_df = ind.compute_rolling_volatility(ind.compute_daily_returns(rdf, stock), stock)
        sr_dr = compute_sharpe_ratio(rv_df, dr_df)
        
    # Outputs