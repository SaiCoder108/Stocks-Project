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

---

## Current Component

### Project 0 — Market Data Ingestion & Processing

This component establishes the foundational data pipeline for the stack.

Key capabilities:
- Retrieval of historical equity market data
- Handling real-world API outputs (e.g. MultiIndex columns)
- Conversion to standardized OHLCV format
- Proper datetime indexing and data normalization

This module produces analysis-ready market data that serves as the input for all subsequent quantitative metrics and models.

---

## Technical Stack

- Python
- pandas
- NumPy
- Public market data APIs (e.g. Yahoo Finance)
