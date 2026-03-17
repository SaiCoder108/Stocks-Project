# Fintech Project Stack

A modular Python-based fintech and quantitative analysis codebase focused on financial market data processing, technical indicator computation, and portfolio management.

This repository is designed around how real-world financial systems handle market data: ingesting raw price feeds, normalizing time-series structures, and preparing clean inputs for quantitative analysis and research.

---

## Overview

**Key capabilities:**

- Calculation of daily returns and log returns for equities
- Computation of rolling volatility and Sharpe ratio over customizable windows
- Accurate maximum drawdown calculation with proper rolling-window alignment
- Moving average signals for bullish, bearish, or neutral trends
- Produces clean, analysis-ready risk metrics for use in quantitative research and trading strategy development
- Applies this to a backtest over a 15 year period, including testing, validating and out-of-sample screen

This module integrates seamlessly with the market data pipeline, ensuring all quantitative calculations are performed on **normalized, correctly indexed time-series data**.

---

## Strategy & Portfolio Tracking

- Modular strategy layer generates buy/sell/hold signals using technical indicators like moving averages, RSI, volume, and volatility.
- Execution layer tracks positions, shares, entry prices, and trade dates using a JSON-like structure, allowing dynamic updates to cash, unrealized P&L, and total portfolio value.
- Supports multiple stocks, multiple positions, and risk management through stop-loss and take-profit thresholds.
- Enables multi-day simulation with portfolio summaries at each step for performance tracking.

---

## Example Outputs

- Analysis-ready OHLCV CSV files
- Risk & performance metric ratings simplified to buy/sell signals 
- Summary tables and console outputs highlighting trends, volatility, and drawdowns
- Portfolio summaries including total capital, unrealized gains/losses, and total portfolio value

---

## Technical Stack

- Python 3.x
- pandas
- NumPy
- yfinance (historical market data)

---

## Notes

- Current implementation uses historical OHLC data for signal generation.
- Future extensions include NLP/senntiment processing and AI learning for optimizing parameters
