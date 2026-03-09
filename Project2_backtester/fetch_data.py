# Imports
import pandas as pd
import yfinance as yf
import config

# Input Stock Ticker and Date Range from User 
def fetch_data(stock, start_date, end_date):

    # Fetch Data using Yahoo 
    data = yf.download(stock, start=start_date, end=end_date,progress=False)
    # After fetching data
    if isinstance(data.columns, pd.MultiIndex):
        # Pick the **columns that are numbers**, not strings like 'AAPL'
        data = data.xs(stock, level=1, axis=1)  # select your ticker from second level
    api_format = data.to_dict(orient='index')  # gives {date: {col: val}}

    # List to hold processed data
    rows = []

    # Loop Through API Data and created list with nested dictionaries
    for date_str, day_data in api_format.items():
        row = {
            "Date": date_str,
            "Open": float(day_data["Open"]),
            "High": float(day_data["High"]),
            "Low": float(day_data["Low"]),
            "Close": float(day_data["Close"]),
            "Volume": int(day_data["Volume"]),
        }
        rows.append(row)

    # Create DataFrame (with index as the timestamp)
    df = pd.DataFrame(rows)

    df.index = pd.to_datetime(df["Date"])
    df = df.drop(columns=["Date"])
    #df.to_csv(f"{stock}.csv")

    return(df)  # Return Stock Historical DataFrame
