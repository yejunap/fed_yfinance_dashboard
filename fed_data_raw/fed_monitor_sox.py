#!/usr/bin/env python3
"""
FED + Market Data Monitor
- FRED: macro + SP500 + NASDAQ100
- Yahoo: SOX (Philadelphia Semiconductor Index)
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import urllib.request
import yfinance as yf
import pandas as pd

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
        logging.FileHandler(LOG_DIR / "fed_monitor.log"),
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
# SOX (Yahoo Finance)
# =========================
def fetch_sox_data():
    try:
        logger.info("Fetching SOX from Yahoo Finance...")
        sox = yf.download("^SOX", start=START_DATE, end=END_DATE, progress=False)

        if sox.empty:
            logger.warning("SOX data empty")
            return None

        # Reset index to make Date a column
        sox = sox.reset_index()
        
        # Handle MultiIndex columns (common with yfinance)
        # Columns look like: [('Date', ''), ('Close', '^SOX'), ...]
        if isinstance(sox.columns, pd.MultiIndex):
            sox.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        
        # Extract data
        observations = []
        for _, row in sox.iterrows():
            date_val = row["Date"]
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val).split()[0][:10]
            
            close_value = float(row["Close"])
            observations.append({
                "date": date_str,
                "value": close_value
            })

        return observations

    except Exception as e:
        logger.error(f"SOX fetch error: {e}")
        return None

# =========================
# MAIN
# =========================
def main():

    logger.info("=" * 60)
    logger.info("FED + MARKET DATA MONITOR")
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
    # SOX 추가
    # =========================
    sox_hist = fetch_sox_data()

    if sox_hist:
        historical_data["SOX"] = {
            "name": "Philadelphia Semiconductor Index",
            "observations": sox_hist
        }

        latest = sox_hist[-1]
        results["SOX"] = {
            "name": "Philadelphia Semiconductor Index",
            "date": latest["date"],
            "value": latest["value"]
        }

        logger.info(f"SOX: {latest['value']} ({latest['date']})")
    else:
        logger.warning("SOX fetch failed")

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