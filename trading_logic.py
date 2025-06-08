import yfinance as yf
import pandas as pd

def parse_tickers(raw):
    if not raw:
        return []
    return list({t.strip().upper() for t in raw.replace(',', ' ').replace('\n', ' ').split() if t.strip()})

def get_stock_data(tickers):
    if not tickers:
        return {}
    df = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False, auto_adjust=True)
    prices = {}
    infos = {}
    if isinstance(df.columns, pd.MultiIndex):
        for t in tickers:
            hist = df[t]
            prices[t] = hist
            try:
                ticker_obj = yf.Ticker(t)
                infos[t] = ticker_obj.info
                infos[t]['symbol'] = t
            except Exception:
                infos[t] = {}
    else:
        t = tickers[0]
        prices[t] = df
        try:
            ticker_obj = yf.Ticker(t)
            infos[t] = ticker_obj.info
            infos[t]['symbol'] = t
        except Exception:
            infos[t] = {}
    return prices, infos


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


def passes_filters(df, info):
    """
    df: DataFrame for this ticker (from yfinance)
    info: ticker.info dict (from yfinance.Ticker)
    Returns True if ticker meets all criteria.
    """
    # --- (1) Close > 1% higher than 1 month ago close ---
    if len(df) < 22:  # ~1 month trading days
        return False
    last_close = df['Close'].iloc[-1]
    month_ago_close = df['Close'].iloc[0]
    if last_close <= month_ago_close * 1.01:
        return False

    # --- (2) SCTR score (skipped, see note) ---
    # No SCTR data in yfinance. You'd need to get this from StockCharts API.
    # sctr_large = info.get('sctr_large', 0)
    # sctr_mid = info.get('sctr_mid', 0)
    # sctr_small = info.get('sctr_small', 0)
    # if not (sctr_large > 80 or sctr_mid > 80 or sctr_small > 80):
    #     return False

    # --- (3) Volume above 50,000 ---
    if df['Volume'].iloc[-1] < 50000:
        return False

    # --- (4) Market cap > 1B ---
    market_cap = info.get('marketCap', 0)
    if market_cap is None or market_cap < 1_000_000_000:
        return False

    # --- (5) Close > 21-day SMA ---
    if last_close <= df['Close'].rolling(21).mean().iloc[-1]:
        return False

    # --- (6) Close > 200-day SMA (need more data) ---
    # Need 200 days of data for this, so we fetch a longer history.
    if len(df) < 200:
        hist_long = yf.download(info['symbol'], period="1y", interval="1d", progress=False, auto_adjust=True)
        if len(hist_long) < 200:
            return False
        long_sma = hist_long['Close'].rolling(200).mean().iloc[-1]
        if last_close <= long_sma:
            return False
    else:
        if last_close <= df['Close'].rolling(200).mean().iloc[-1]:
            return False

    return True
