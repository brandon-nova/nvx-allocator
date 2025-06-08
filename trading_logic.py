import yfinance as yf
import pandas as pd

def parse_tickers(raw):
    if not raw:
        return []
    return list({t.strip().upper() for t in raw.replace(',', ' ').replace('\n', ' ').split() if t.strip()})

def get_stock_data(tickers):
    if not tickers:
        return {}
    df = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False, auto_adjust=True)
    # Handle single ticker vs multi
    if isinstance(df.columns, pd.MultiIndex):
        prices = {}
        for t in tickers:
            hist = df[t]
            prices[t] = hist
        return prices
    else:
        return {tickers[0]: df}

def allocation_rules(df):
    alloc = 0
    if len(df) > 0:
        month_open = df.iloc[0]['Open']
        curr_close = df.iloc[-1]['Close']
        if curr_close > month_open:
            alloc += 10
        df['9dma'] = df['Close'].rolling(window=9).mean()
        today = df.iloc[-1]
        if today['Low'] < today['9dma'] and today['Close'] > today['9dma']:
            alloc += 5
        if today['Close'] < today['Open']:
            alloc += 5
    return alloc
