# Fintech Project Stack

A modular Python-based fintech and quantitative analysis codebase focused on financial market data processing and statistical analysis.

This repository is designed around how real-world financial systems handle market data: ingesting raw price feeds, normalizing time-series structures, and preparing clean inputs for quantitative analysis and research.

---

## Overview

The Fintech Project Stack emphasizes:

- Market data ingestion and normalization
- Time-series data processing
- Explicit quantitative calculations
- Clean, modular, and testable Python design

The focus is on data correctness, structure, and financial intuition, rather than black-box models or abstracted libraries.


**Key capabilities:**

- Calculation of daily returns and log returns for equities
- Computation of rolling volatility and Sharpe ratio over customizable windows
- Accurate maximum drawdown calculation with proper rolling-window alignment
- Moving average signals for bullish, bearish, or neutral trends
- Produces clean, analysis-ready risk metrics for use in quantitative research and trading strategy development

This module integrates seamlessly with the market data pipeline, ensuring all quantitative calculations are performed on **normalized, correctly indexed time-series data**.

### Example Outputs
- Analysis-ready OHLCV CSV files
- Risk & performance metric ratings simplified to buy/sell signals 
- Summary tables and plots highlighting trends, volatility, and drawdowns

---

## Technical Stack

- Python
- pandas
- NumPy
- yfinance (historical market data)
- Modular, testable design supporting and loop-based computations
