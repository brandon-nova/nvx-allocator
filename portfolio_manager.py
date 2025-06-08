import json
import os

PORTFOLIOS_FILE = 'portfolios.json'

def load_portfolios():
    if os.path.exists(PORTFOLIOS_FILE):
        try:
            with open(PORTFOLIOS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # Default: 6 blank portfolios
    return [{'name': f'P {i+1}', 'tickers': ''} for i in range(6)]

def save_portfolios(portfolios):
    try:
        with open(PORTFOLIOS_FILE, 'w') as f:
            json.dump(portfolios, f)
    except Exception:
        pass

SETTINGS_FILE = 'settings.json'

def load_amount():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('set_amount', 10000)
        except Exception:
            pass
    return 10000

def save_amount(amount):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'set_amount': amount}, f)
    except Exception:
        pass
