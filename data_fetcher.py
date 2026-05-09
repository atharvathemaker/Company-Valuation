import yfinance as yf
import pandas as pd
import numpy as np

def calculate_beta(ticker, benchmark):
    data = yf.download([ticker, benchmark], period="3y")['Close']
    returns = data.pct_change().dropna()
    covariance = returns.cov().iloc[0, 1]
    variance = returns[benchmark].var()
    return covariance / variance

def get_valuation_data(country):
    # Simplified mock for Damodaran data fetching
    # In a full implementation, this scrapes the 'ctryprem.xlsx'
    return {"risk_free_rate": 0.042, "erp": 0.05}
