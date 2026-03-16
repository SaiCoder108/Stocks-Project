# Imports
import pandas as pd
import fetch_data
import config
import numpy as np
import indicators
import strategy
from datetime import timedelta,datetime
import json
import os

if __name__ == "__main__":

    # File to persist portfolio
    portfolio_file = "portfolio.json"

    if os.path.exists(portfolio_file):
        with open(portfolio_file, "r") as f:
            data = json.load(f)
            positions = data.get("positions", {})
            capital = data.get("capital", 100000)
            num_positions = len(positions)
    else:
        positions = {}
        capital = 100000
        num_positions = 0
    stocklist = [
    "AAPL","MSFT","AMZN","GOOG","META","NVDA",
    "XOM","CVX","COP","EOG","SLB",
    "SPY","DIA","QQQ","XLK","VGT","SOXX","SMH","XLE","VDE","IYE","XOP"
    ]

    # Strategy Specific Inputs
    print("Welcome to Stock Trading Algo! ")
    vol_thold = config.vol_th

    for stock in stocklist:

        # Inputs        
        n_days = config.day_range
        r_days_w = int(n_days)+(config.rv_window - 1)
        days_w = int(n_days)
        buffer1 = days_w*1.5
        buffer2 = int(r_days_w)*1.5
        start_date = (datetime.today() - timedelta(days=int(buffer1))).strftime("%Y-%m-%d")
        rv_start_date = (datetime.today() - timedelta(days=int(buffer2))).strftime("%Y-%m-%d")
        end_date = datetime.today().strftime("%Y-%m-%d")

        # Fail-Case
        if start_date == None:
            start_date = "2025-01-01"
        if end_date == None:
            end_date = datetime.today().strftime("%Y-%m-%d")

        # Fetch Data
        df = fetch_data.fetch_data(stock, start_date, end_date)
        rdf = fetch_data.fetch_data(stock, rv_start_date, end_date)
        prev_df = fetch_data.fetch_data(stock, (datetime.today() - timedelta(days=int(buffer1))).strftime("%Y-%m-%d"), (datetime.today() - timedelta(days=int(1))).strftime("%Y-%m-%d"))

        # Processes
        dr_df = indicators.compute_daily_returns(df, stock)
        prev_dr_df = indicators.compute_daily_returns(prev_df,stock)
        rv_df = indicators.compute_rolling_volatility(indicators.compute_daily_returns(rdf,stock), stock)

        temp_ma, temp_cp = indicators.compute_moving_average(df,days_w,stock)

        mab_s = strategy.ma_band_signal(temp_ma, temp_cp)
        vc = strategy.volatility_check(rv_df, vol_thold)
        rsi_c = strategy.RSI_Check(dr_df, prev_dr_df)
        volume_c = strategy.volume_check(df)
            
        # Trading Rule
        current_price = temp_cp
        # if mab_s != 0 and vc == 1 and rsi_c != 0 and volume_c == 1:    
        if mab_s != 0:
            if stock not in positions and capital>=1000 and num_positions < 20:
                if mab_s == 1:

                    # Shares Logic
                    shares = (capital * config.RPT) / (current_price*config.stop_loss)
                    shares = int(shares)
                    buy_price = shares*current_price
                    trade_info = {"entry_price": current_price,"shares": shares,"entry date": datetime.today().strftime("%Y-%m-%d")}

                    # Portfolio Update
                    positions[stock] = trade_info
                    capital-=buy_price
                    num_positions+=1
                    print(f"{shares} shares of {stock} bought at {current_price}")
            elif stock in positions:
                trade_info = positions[stock]
                entry = trade_info["entry_price"]
                shares = trade_info["shares"]
                if (mab_s == -1 and rsi_c == -1) or (((current_price-entry)/entry) <= -config.stop_loss) or (current_price-entry)/entry >= config.TPM:
                    num_positions-=1
                    PnL = (current_price-entry) * shares
                    capital+= current_price*shares 
                    print(f"{shares} shares of {stock} sold at {current_price} (Gain/Loss: {PnL})")
                    del positions[stock]
    
    # Save to JSON file
    with open(portfolio_file, "w") as f:
        json.dump({"positions": positions, "capital": capital}, f, indent=4)

    print("\n--- Portfolio Summary ---")
    total_value = capital
    un_gain = 0
    for stock, info in positions.items():
        current_price = indicators.compute_moving_average(fetch_data.fetch_data(stock, start_date, end_date), days_w, stock)[1]
        shares = info["shares"]
        entry = info["entry_price"]
        PnL = (current_price - entry) * shares
        total_value += current_price * shares
        un_gain += PnL
        print(f"{stock}: {shares} shares, entry {entry}, current {current_price}, P&L {PnL}")

    print(f"Cash: {capital}")
    print(f"Total Portfolio Value: {total_value}")
    print(f"Unrealized Gain: {un_gain}")
    print(f"Total P&L: {total_value - 100000} ({((total_value - 100000)/100000)*100}%)")  # if 100k initial capital
