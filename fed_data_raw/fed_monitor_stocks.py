#!/usr/bin/env python3
"""
FED + Market Data Monitor
- FRED: macro + SP500 + NASDAQ100
- Yahoo: SOX (Philadelphia Semiconductor Index)
- Yahoo: Samsung (005930.KS), SK Hynix (000660.KS), SK Square (096770.KS)
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import urllib.request
import yfinance as yf

# =========================
# CONFIG
# =========================
DATA_DIR = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "fed_monitor_stocks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================
# FRED CONFIG
# =========================
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES = {
    "FEDFUNDS": "Fed Funds Rate",
    "M2SL": "M2 Money Supply",
    "WALCL": "Fed Total Assets",
    "OBFR": "Overnight Bank Funding Rate",
    "MORTGAGE30US": "30-Year Mortgage Rate",
    "RRPONTSYD": "Reverse Repo",
    "WTREGEN": "Treasury General Account",
    "SP500": "S&P 500 Index",
    "NASDAQ100": "Nasdaq 100 Index",
}

# =========================
# STOCKS CONFIG
# =========================
STOCKS = {
    "005930.KS": "Samsung Electronics",
    "000660.KS": "SK Hynix",
    "096770.KS": "SK Square",
}

START_DATE = "2000-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# =========================
# FRED FUNCTIONS
# =========================
def fetch_fred_data(series_id, start_date=None, end_date=None):
    if not FRED_API_KEY:
        logger.warning(f"No API key → skip {series_id}")
        return None

    url = f"{BASE_URL}?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"

    if start_date:
        url += f"&observation_start={start_date}"
    if end_date:
        url += f"&observation_end={end_date}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"{series_id} fetch error: {e}")
        return None


def get_latest_value(series_id):
    data = fetch_fred_data(series_id)
    if not data or "observations" not in data:
        return None

    obs = data["observations"]
    if not obs:
        return None

    last = obs[-1]
    return last["date"], last["value"]


def get_historical_data(series_id):
    data = fetch_fred_data(series_id, START_DATE, END_DATE)
    if not data or "observations" not in data:
        return None
    return data["observations"]

# =========================
# STOCKS (Yahoo Finance)
# =========================
def fetch_stock_data(symbol):
    try:
        logger.info(f"Fetching {symbol} from Yahoo Finance...")
        stock = yf.download(symbol, start=START_DATE, end=END_DATE, progress=False)

        if stock.empty:
            logger.warning(f"{symbol} data empty")
            return None

        stock = stock.reset_index()

        observations = []
        for _, row in stock.iterrows():
            observations.append({
                "date": row["Date"].strftime("%Y-%m-%d"),
                "value": str(row["Close"])
            })

        return observations

    except Exception as e:
        logger.error(f"{symbol} fetch error: {e}")
        return None

# =========================
# MAIN
# =========================
def main():

    logger.info("=" * 60)
    logger.info("FED + MARKET DATA MONITOR (Stocks)")
    logger.info("=" * 60)

    results = {}
    historical_data = {}

    # =========================
    # FRED LOOP
    # =========================
    for sid, name in FRED_SERIES.items():

        logger.info(f"Fetching {sid}...")

        # latest
        latest = get_latest_value(sid)
        if latest:
            date, value = latest
            results[sid] = {
                "name": name,
                "date": date,
                "value": value
            }
            logger.info(f"{name}: {value} ({date})")
        else:
            logger.warning(f"{sid} latest failed")

        # historical
        hist = get_historical_data(sid)
        if hist:
            historical_data[sid] = {
                "name": name,
                "observations": hist
            }
            logger.info(f"{sid} history: {len(hist)} rows")
        else:
            logger.warning(f"{sid} history failed")

    # =========================
    # STOCKS LOOP
    # =========================
    for symbol, name in STOCKS.items():
        logger.info(f"Fetching {symbol}...")
        
        stock_hist = fetch_stock_data(symbol)
        
        if stock_hist:
            historical_data[symbol] = {
                "name": name,
                "observations": stock_hist
            }

            latest = stock_hist[-1]
            results[symbol] = {
                "name": name,
                "date": latest["date"],
                "value": latest["value"]
            }

            logger.info(f"{name}: {latest['value']} ({latest['date']})")
        else:
            logger.warning(f"{symbol} fetch failed")

    # =========================
    # SAVE
    # =========================
    latest_file = DATA_DIR / "fed_data_latest.json"
    hist_file = DATA_DIR / "fed_data_historical.json"

    with open(latest_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data": results
        }, f, indent=2)

    with open(hist_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "start_date": START_DATE,
            "end_date": END_DATE,
            "data": historical_data
        }, f, indent=2)

    logger.info("Saved all data successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()