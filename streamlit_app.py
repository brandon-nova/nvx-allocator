import streamlit as st
import pandas as pd
import math
from trading_logic import parse_tickers, get_stock_data, allocation_rules, passes_filters
from portfolio_manager import load_portfolios, save_portfolios, load_amount, save_amount
import streamlit.components.v1 as components

st.set_page_config(page_title="Portfolio Allocator", layout="wide")

# --- Persistent State Initialization ---
if 'set_amount' not in st.session_state:
    st.session_state.set_amount = load_amount()
if 'lists' not in st.session_state:
    st.session_state.lists = load_portfolios()
if 'active_list' not in st.session_state:
    st.session_state.active_list = 0
if 'editing' not in st.session_state:
    st.session_state.editing = False

# --- Save Amount on Change ---
def update_amount():
    save_amount(st.session_state.set_amount)

# --- UI: Set Amount (single widget, no submit, updates live) ---
st.title("NVX Allocator")
st.number_input(
    "Set Amount:",
    min_value=1,
    step=1,
    key="set_amount",
    on_change=update_amount,
)

# --- Edit List Full Page (if editing) ---
if st.session_state.editing:
    lst = st.session_state.lists[st.session_state.active_list]
    def_name = f'P{st.session_state.active_list+1}'
    new_name = st.text_input(
        "Name (max 4 chars)",
        value=lst['name'][:4] if lst['name'] else def_name,
        max_chars=4,
        key="edit_list_name"
    )
    new_tickers = st.text_area(
        "Tickers (comma, space, or newline separated)",
        value=lst['tickers'],
        height=100,
        key="edit_list_tickers"
    )
    save_btn = st.button("💾 Save and Exit")
    if save_btn:
        lst['name'] = new_name if new_name else def_name
        lst['tickers'] = new_tickers
        save_portfolios(st.session_state.lists)
        st.session_state.editing = False
    st.stop()  # Block rest of app in edit mode

#EXPANDER FOR LISTS
with st.expander("View Lists", expanded=True):
    cols = st.columns(8)
    for idx in range(6):
        name = st.session_state.lists[idx]['name'][:4] or f'P{idx+1}'
        if cols[idx].button(name, key=f"list_{idx}"):
            st.session_state.active_list = idx
            if st.session_state.editing:
                st.experimental_rerun()
    if cols[6].button("Edit", key="edit_btn"):
        st.session_state.editing = True


# --- Portfolio Table ---
active_list = st.session_state.lists[st.session_state.active_list]
tickers = parse_tickers(active_list['tickers'])

if not tickers:
    st.info("No tickers in this list. Click 'Edit' to add tickers.")
    st.stop()

st.write(f"#### Allocating for: {active_list['name'][:4]}")
st.write(f"Tickers: {' '.join(tickers)}")

# --- Get Stock Data and Filter ---
prices, infos = get_stock_data(tickers)

# --- Data Check: Display error for tickers with no data ---
for t in tickers:
    if t not in prices or prices[t] is None or prices[t].empty:
        st.warning(f"⚠️ No price data returned for {t}. (yfinance may be blocked or symbol is invalid)")
    elif t not in infos or not infos[t] or infos[t].get("marketCap", 0) == 0:
        st.warning(f"⚠️ No company info/market cap for {t}. (Could be API limit or delisted ticker)")

filtered_tickers = [
    t for t in tickers if passes_filters(prices[t], infos[t])
]

if not filtered_tickers:
    st.info("No tickers pass your filter criteria.")
    st.stop()

allocations = {}
for t in filtered_tickers:
    try:
        df = prices[t]
        score = allocation_rules(df)
        allocations[t] = score
    except Exception:
        allocations[t] = 0  # fallback if can't load

# Normalize allocations
total_score = sum(allocations.values()) or 1
alloc_perc = {k: round(v * 100 / total_score, 2) for k, v in allocations.items()}

# --- Build Table Data (add 'Last' column) ---
amount = st.session_state.set_amount
table = []
for t in filtered_tickers:
    perc = alloc_perc[t]
    dollar = round(amount * perc / 100, 2)
    try:
        last_close = prices[t].iloc[-1]['Close']
        shares = math.floor(dollar / last_close,) if last_close else 0
    except Exception:
        last_close = 0
        shares = 0
    table.append({
        'Ticker': t,
        '($)': dollar,
        'Shares': shares,
        '(%)': perc,
        'Last': last_close
    })

df_table = pd.DataFrame(table)
st.dataframe(df_table, use_container_width=True)