#!/usr/bin/env python3
"""
FED + Market Data Monitor - YFinance Collection
- Collects sector/industry ETFs from Yahoo Finance
- Saves to fed_yfinance_latest.json and fed_yfinance_historical.json
- Does NOT overwrite the main fed_data files
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import yfinance as yf
import pandas as pd

# =========================
# CONFIG
# =========================
DATA_DIR = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# YFinance 전용 파일명 (기존 fed_data와 구분)
YAHOO_DATA_PREFIX = "fed_yfinance"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "fed_monitor_yfinance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================
# YAHOO FINANCE TICKERS (Categorized by Sector)
# =========================
YAHOO_TICKERS = {
    "Technology": {
        "Tech Sector": "XLK",
        "Cloud": "CLOU",
        "Cybersecurity": "CIBR",
        "Cybersecurity2": "BUG",
        "Robotics/AI": "BOTZ",
    },
    "Energy": {
        "Energy Sector": "XLE",
        "Crude Oil": "CL=F",
        "Natural Gas": "NG=F",
        "Uranium": "URA",
    },
    "Financial": {
        "Financials": "XLF",
        "Regional Banks": "KRE",
        "Fintech": "FINX",
    },
    "Industrials": {
        "Industrials": "XLI",
        "Defense": "ITA",
        "Aerospace": "XAR",
    },
    "Healthcare": {
        "Healthcare": "XLV",
        "Biotech": "XBI",
        "Pharma": "PPH",
    },
    "Consumer": {
        "Consumer Disc": "XLY",
        "Consumer Staple": "XLP",
    },
    "Utilities": {
        "Utilities": "XLU",
        "REITs": "XLRE",
    },
    "Materials": {
        "Materials": "XLB",
        "Rare Earth": "REMX",
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Copper": "HG=F",
    },
    "Volatility": {
        "VIX": "^VIX",
        "US 10Y Yield": "^TNX",
        "Long Treasury": "TLT",
        "High Yield Bond": "HYG",
        "Dollar Index": "DX-Y.NYB",
    },
    "International": {
        "China": "FXI",
        "India": "INDA",
        "Japan": "EWJ",
        "Korea": "EWY",
        "Taiwan": "EWT",
    }
}

# =========================
# GLOBAL TICKERS (for comparison)
# =========================
GLOBAL_TICKERS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
}

START_DATE = "2000-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# =========================
# YAHOO FINANCE FUNCTIONS
# =========================
def fetch_yfinance_data(ticker, start_date=None, end_date=None):
    """Fetch historical data from Yahoo Finance"""
    try:
        if start_date is None:
            start_date = START_DATE
        if end_date is None:
            end_date = END_DATE
            
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Handle MultiIndex columns (common with yfinance)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        
        # Extract data properly
        observations = []
        for _, row in data.iterrows():
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
        logger.error(f"{ticker} fetch error: {e}")
        return None


def get_normalized_data(observations):
    """Normalize data so first value is 1.0"""
    if not observations:
        return None
    
    first_value = observations[0]["value"]
    if first_value == 0:
        return None
    
    normalized = []
    for obs in observations:
        normalized.append({
            "date": obs["date"],
            "value": float(obs["value"]) / float(first_value)
        })
    
    return normalized


def main():
    logger.info("=" * 60)
    logger.info("FED + YAHOO FINANCE DATA MONITOR (SEPARATE FILE)")
    logger.info("=" * 60)
    
    # YFinance 전용 파일 (기존 fed_data 건드리지 않음)
    hist_file = DATA_DIR / f"{YAHOO_DATA_PREFIX}_historical.json"
    latest_file = DATA_DIR / f"{YAHOO_DATA_PREFIX}_latest.json"
    
    # 기존 YFinance 데이터가 있다면 로드
    historical_data = {}
    latest_data = {}
    
    if hist_file.exists():
        with open(hist_file, "r") as f:
            historical_data = json.load(f).get("data", {})
    
    if latest_file.exists():
        with open(latest_file, "r") as f:
            latest_data = json.load(f).get("data", {})
    
    # Process each sector
    for sector, tickers in YAHOO_TICKERS.items():
        logger.info(f"Processing sector: {sector}")
        for name, ticker in tickers.items():
            logger.info(f"  Fetching {ticker} ({name})...")
            
            hist = fetch_yfinance_data(ticker)
            if hist:
                # Save original historical data
                historical_data[ticker] = {
                    "name": name,
                    "category": sector,
                    "observations": hist
                }
                
                # Save latest value
                last_obs = hist[-1]
                latest_data[ticker] = {
                    "name": name,
                    "category": sector,
                    "date": last_obs["date"],
                    "value": last_obs["value"]
                }
                
                # Get normalized data for comparison
                normalized = get_normalized_data(hist)
                if normalized:
                    historical_data[f"{ticker}_NORM"] = {
                        "name": f"{name} (Normalized)",
                        "category": sector,
                        "normalized": True,
                        "observations": normalized
                    }
                
                logger.info(f"    {name}: {last_obs['value']} ({last_obs['date']})")
            else:
                logger.warning(f"    {ticker} fetch failed")
    
    # Add global indices
    logger.info("Processing global indices...")
    for name, ticker in GLOBAL_TICKERS.items():
        hist = fetch_yfinance_data(ticker)
        if hist:
            historical_data[ticker] = {
                "name": name,
                "category": "Global Indices",
                "observations": hist
            }
            
            last_obs = hist[-1]
            latest_data[ticker] = {
                "name": name,
                "category": "Global Indices",
                "date": last_obs["date"],
                "value": last_obs["value"]
            }
            
            normalized = get_normalized_data(hist)
            if normalized:
                historical_data[f"{ticker}_NORM"] = {
                    "name": f"{name} (Normalized)",
                    "category": "Global Indices",
                    "normalized": True,
                    "observations": normalized
                }
            
            logger.info(f"    {name}: {last_obs['value']} ({last_obs['date']})")
    
    # Save data (기존 fed_data_* 파일과 별도)
    with open(latest_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data": latest_data
        }, f, indent=2)
    
    with open(hist_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "start_date": START_DATE,
            "end_date": END_DATE,
            "data": historical_data
        }, f, indent=2)
    
    logger.info(f"Saved YFinance data to: {latest_file}")
    logger.info(f"Total tickers collected: {len(latest_data)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
