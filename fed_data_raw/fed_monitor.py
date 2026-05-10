#!/usr/bin/env python3
"""
FED Macroeconomic Data Monitor
Monitors: Fed Funds Rate, M2 Currency, Treasury General Account, RRP
Updates: Daily
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
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

# FRED API Configuration
# Get your free API key from: https://fred.stlouisfed.org/api keys
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Data series to monitor
FRED_SERIES = {
    "FEDFUNDS": "Fed Funds Rate",
    "M2SL": "M2 Money Supply",
    "WALCL": "Fed Total Asset",  # Weekly
    "OBFR": "Overnight Bank Funding Rate",
    "MORTGAGE30US": "30-Year Mortgage Rate",
    "RRPONTSYD": "Reverse Repo Rate",
    "WTREGEN": "Treasury General Account - Total",
    "SP500": "S&P 500 Index",
    "NASDAQ100": "Nasdaq 100 Index",
}

# Date range for historical data
START_DATE = "2000-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")


def fetch_fred_data(series_id: str, start_date: str = None, end_date: str = None) -> dict | None:
    """Fetch data from FRED API for a given series."""
    if not FRED_API_KEY:
        logger.warning(f"No FRED_API_KEY set. Skipping {series_id}")
        return None
    
    import urllib.request
    import urllib.parse
    
    url = f"{BASE_URL}?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
    if start_date:
        url += f"&observation_start={start_date}"
    if end_date:
        url += f"&observation_end={end_date}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        logger.error(f"Error fetching {series_id}: {e}")
        return None


def get_latest_value(series_id: str) -> tuple | None:
    """Get the latest value for a series."""
    data = fetch_fred_data(series_id)
    if not data or "observations" not in data:
        return None
    
    observations = data["observations"]
    if not observations:
        return None
    
    latest = observations[-1]
    return (latest.get("date"), latest.get("value"))


def get_historical_data(series_id: str, start_date: str, end_date: str) -> list | None:
    """Get historical data for a series from start to end date."""
    data = fetch_fred_data(series_id, start_date, end_date)
    if not data or "observations" not in data:
        return None
    
    return data["observations"]


def main():
    """Main monitoring function."""
    logger.info("=" * 50)
    logger.info("FED Macroeconomic Data Monitor - Daily Update")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("=" * 50)
    
    if not FRED_API_KEY:
        logger.error("FRED_API_KEY not set!")
        logger.info("Get a free API key from: https://fred.stlouisfed.org/api keys")
        logger.info("Set it with: export FRED_API_KEY=your_key_here")
        return
    
    # Fetch all series - latest values
    results = {}
    historical_data = {}
    
    for series_id, description in FRED_SERIES.items():
        result = get_latest_value(series_id)
        if result:
            date, value = result
            results[series_id] = {
                "name": description,
                "date": date,
                "value": value
            }
            logger.info(f"{description} ({series_id}): {value} as of {date}")
        else:
            logger.warning(f"Could not fetch {series_id}")
        
        # Fetch historical data
        hist = get_historical_data(series_id, START_DATE, END_DATE)
        if hist:
            historical_data[series_id] = {
                "name": description,
                "observations": hist
            }
            logger.info(f"  -> Retrieved {len(hist)} historical observations")
    
    # Save latest to JSON
    output_file = DATA_DIR / "fed_data_latest.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "data": results
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Latest data saved to {output_file}")
    
    # Save historical data to JSON
    hist_file = DATA_DIR / "fed_data_historical.json"
    hist_output = {
        "timestamp": datetime.now().isoformat(),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "data": historical_data
    }
    
    with open(hist_file, "w") as f:
        json.dump(hist_output, f, indent=2)
    
    logger.info(f"Historical data saved to {hist_file}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()