import streamlit as st
import pandas as pd
from trading_logic import parse_tickers, get_stock_data, allocation_rules
from portfolio_manager import load_portfolios, save_portfolios, load_amount, save_amount

st.set_page_config(page_title="Portfolio Allocator", layout="wide")

# --- Persistent State ---
if 'lists' not in st.session_state:
    st.session_state.lists = load_portfolios()
if 'active_list' not in st.session_state:
    st.session_state.active_list = 0
if 'initialized' not in st.session_state:
    st.session_state.set_amount = load_amount()
    st.session_state.initialized = True
if 'editing' not in st.session_state:
    st.session_state.editing = False

# --- UI: Set Amount ---
st.title("Portfolio Allocator")
set_amount = st.number_input("Set Amount:", value=st.session_state.set_amount, min_value=1, step=1)
if st.button("Submit Amount"):
    st.session_state.set_amount = set_amount
    save_amount(set_amount)

# --- Edit List Full Page ---
if st.session_state.editing:
    lst = st.session_state.lists[st.session_state.active_list]
    st.header(f"Edit List: {lst['name']}")
    new_name = st.text_input("Name", value=lst['name'], key="edit_list_name")
    new_tickers = st.text_area(
        "Tickers (comma, space, or newline separated)",
        value=lst['tickers'],
        height=100,
        key="edit_list_tickers"
    )
    cols = st.columns([1, 1, 6])
    save_btn = cols[0].button("💾 Save")
    close_btn = cols[1].button("❌ Close")
    if save_btn:
        lst['name'] = new_name
        lst['tickers'] = new_tickers
        save_portfolios(st.session_state.lists)
        st.success("Saved.")
    if close_btn:
        st.session_state.editing = False
    st.stop()  # Don’t show anything else while editing

# --- UI: List Selection and Edit ---
cols = st.columns(8)
for idx in range(6):
    if cols[idx].button(st.session_state.lists[idx]['name'], key=f"list_{idx}"):
        st.session_state.active_list = idx

if cols[6].button("Edit List"):
    st.session_state.editing = True

# --- Portfolio Table ---
active_list = st.session_state.lists[st.session_state.active_list]
tickers = parse_tickers(active_list['tickers'])

if not tickers:
    st.info("No tickers in this list. Click 'Edit List' to add tickers.")
    st.stop()

st.write(f"#### Allocating for: {active_list['name']}")
st.write(f"Tickers: {' '.join(tickers)}")

# --- Get Stock Data ---
prices = get_stock_data(tickers)
allocations = {}
for t in tickers:
    try:
        df = prices[t]
        score = allocation_rules(df)
        allocations[t] = score
    except Exception:
        allocations[t] = 0  # fallback if can't load

# Normalize allocations
total_score = sum(allocations.values()) or 1  # avoid div by zero
alloc_perc = {k: round(v * 100 / total_score, 2) for k, v in allocations.items()}

# --- Build Table Data ---
amount = st.session_state.set_amount
table = []
for t in tickers:
    perc = alloc_perc[t]
    dollar = round(amount * perc / 100, 2)
    try:
        last_close = prices[t].iloc[-1]['Close']
        shares = round(dollar / last_close, 4)
    except Exception:
        last_close = 0
        shares = 0
    table.append({
        'Ticker': t,
        'Amount ($)': dollar,
        'Shares': shares,
        '% Allocation': perc
    })

df_table = pd.DataFrame(table)
st.dataframe(df_table, use_container_width=True)
