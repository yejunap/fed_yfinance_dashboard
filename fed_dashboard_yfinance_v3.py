#!/usr/bin/env python3
"""
FED YFinance Streamlit Dashboard
- Yahoo Finance sector/industry ETFs
- Global indices
- Commodities
- International markets
- Interactive visualizations
"""

import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# =========================
# Page Config with Style Guide
# =========================
st.set_page_config(
    page_title="FED YFinance Dashboard",
    page_icon="📈",
    layout="wide"
)

# Style Guide Colors (from style-guide.md)
COLORS = {
    "imperial_red": "#E52521",
    "pacific_blue": "#1691A0",
    "davys_gray": "#4D4D4D",
    "blue_ryb": "#0064FF",
    "space_cadet": "#2F3A52",
    "eerie_black": "#221919",
    "emerald": "#23AE78",
    "cool_gray": "#C3C9D1",
    "cultured": "#F5F6F9",
    "sunglow": "#FFC800",
    "coral": "#FF5238",
    "onyx": "#182330",
    "white": "#FFFFFF",
    "black": "#000000"
}

# Seaborn Styling with Style Guide Colors
sns.set_style("whitegrid")
sns.set_palette([COLORS["pacific_blue"], COLORS["imperial_red"], COLORS["emerald"], COLORS["coral"], COLORS["sunglow"]])
plt.rcParams['figure.figsize'] = (15, 6)
plt.rcParams['font.sans-serif'] = ['Be Vietnam Pro', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.grid'] = True
plt.rcParams['axes.grid.axis'] = 'both'
plt.rcParams['axes.linewidth'] = 0.5
plt.rcParams['grid.color'] = '#E0E0E0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 0.8
plt.rcParams['axes.facecolor'] = COLORS["white"]
plt.rcParams['figure.facecolor'] = COLORS["white"]

# =========================
# Paths
# =========================
DATA_DIR = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")

# Custom CSS for Typography and Styling
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;900&display=swap');

body {{
    font-family: 'Be Vietnam Pro', sans-serif;
    background-color: {COLORS["cultured"]};
    color: {COLORS["eerie_black"]};
}}

.stApp {{
    background-color: {COLORS["cultured"]};
    padding: 20px;
}}

h1 {{
    font-weight: 900;
    font-size: 2.5rem;
    color: {COLORS["space_cadet"]};
    margin-bottom: 10px;
}}

h2 {{
    font-weight: 600;
    font-size: 1.5rem;
    color: {COLORS["space_cadet"]};
    margin-top: 24px;
    margin-bottom: 16px;
    border-bottom: 2px solid {COLORS["pacific_blue"]};
    padding-bottom: 8px;
}}

h3 {{
    font-weight: 600;
    font-size: 1.25rem;
    color: {COLORS["space_cadet"]};
    margin-top: 20px;
}}

.stMetric [data-testid="stMetricValue"] {{
    font-size: 2rem;
    font-weight: 600;
    color: {COLORS["space_cadet"]};
}}

.stMetric [data-testid="stMetricLabel"] {{
    font-size: 0.9rem;
    color: {COLORS["davys_gray"]};
}}

.stMetric [data-testid="stMetricDelta"] {{
    font-size: 0.85rem;
}}

.stMetric {{
    background: {COLORS["white"]};
    padding: 15px;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}}

.stMetric [data-testid="stMetricContainer"] {{
    display: flex;
    flex-direction: column;
}}

</style>
""", unsafe_allow_html=True)

st.title("📈 FED YFinance Dashboard")
st.markdown(f"""
Real-time Yahoo Finance sector ETFs, commodities, and global indices.
Data source: [Yahoo Finance](https://finance.yahoo.com/) | Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
""")

# =========================
# Date Range Selector
# =========================
@st.cache_data(ttl=3600)
def get_date_range_options(historical_data):
    """Get minimum and maximum dates from all series"""
    min_date = None
    max_date = None
    
    for key, series in historical_data.get("data", {}).items():
        if "observations" in series and series["observations"]:
            for obs in series["observations"]:
                try:
                    obs_date = pd.to_datetime(obs["date"], errors="coerce")
                    if pd.notna(obs_date):
                        if min_date is None or obs_date < min_date:
                            min_date = obs_date
                        if max_date is None or obs_date > max_date:
                            max_date = obs_date
                except:
                    pass
    
    return min_date, max_date

@st.cache_data(ttl=3600)
def load_data():
    """Load YFinance data from JSON files (cached for 1 hour)"""
    with open(DATA_DIR / "fed_yfinance_latest.json", 'r') as f:
        latest_data = json.load(f)
    
    with open(DATA_DIR / "fed_yfinance_historical.json", 'r') as f:
        historical_data = json.load(f)
    
    return latest_data, historical_data

latest_data, historical_data = load_data()
min_date, max_date = get_date_range_options(historical_data)

# Default start date: 1 year ago from today, or min_date if that's earlier
default_start = max(min_date, datetime.now() - timedelta(days=365)) if min_date else datetime.now() - timedelta(days=365)
default_end = max_date

# Date range selector
st.sidebar.header("📅 Date Range")
start_date = st.sidebar.date_input(
    "Start Date",
    value=default_start,
    min_value=min_date,
    max_value=max_date if max_date else datetime.now()
)

end_date = st.sidebar.date_input(
    "End Date",
    value=default_end,
    min_value=min_date,
    max_value=max_date if max_date else datetime.now()
)

# =========================
# Helper Functions
# =========================
def safe_load_series(key, historical_data, start_date=None, end_date=None):
    """Safely load a series from historical data"""
    if key not in historical_data.get("data", {}):
        return None
    
    series = historical_data["data"][key]
    if "observations" not in series or not series["observations"]:
        return None
    
    df = pd.DataFrame(series["observations"])
    
    # Safe type conversion
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    
    df = df.dropna()
    df = df.sort_values("date")
    df = df.set_index("date")
    
    # Apply date filter if specified
    if start_date is not None:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df.index <= pd.to_datetime(end_date)]
    
    if len(df) == 0:
        return None
    
    return df

def safe_numeric(val):
    """Safely convert to float"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0

def safe_change(current, previous):
    """Calculate percentage change"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

# =========================
# Load All Series
# =========================
# Define global indices first (needed for all_tickers)
global_indices = ["^GSPC", "^IXIC", "^DJI", "^RUT"]

# Organize tickers by category
series_to_load = {
    "Technology": ["XLK", "CLOU", "CIBR", "BUG", "BOTZ"],
    "Energy": ["XLE", "CL=F", "NG=F", "URA"],
    "Financial": ["XLF", "KRE", "FINX"],
    "Industrials": ["XLI", "ITA", "XAR"],
    "Healthcare": ["XLV", "XBI", "PPH"],
    "Consumer": ["XLY", "XLP"],
    "Utilities": ["XLU", "XLRE"],
    "Materials": ["XLB", "REMX", "GC=F", "SI=F", "HG=F"],
    "Volatility": ["^VIX", "^TNX", "TLT", "HYG", "DX-Y.NYB"],
    "International": ["FXI", "INDA", "EWJ", "EWY", "EWT"],
}

# Build all_tickers list
all_tickers = []
for tickers in series_to_load.values():
    all_tickers.extend(tickers)
# Add global indices to all_tickers
all_tickers.extend(global_indices)

df_series = {}
for key in all_tickers:
    df_series[key] = safe_load_series(key, historical_data, start_date, end_date)

# =========================
# Key Metrics (Current Values by Category)
# =========================
st.header("🔑 Sector Performance")

for sector, tickers in series_to_load.items():
    with st.expander(f"{sector} ({len(tickers)} tickers)", expanded=True):
        cols = st.columns(min(5, len(tickers)))
        
        for i, ticker in enumerate(tickers[:5]):
            with cols[i]:
                if ticker in latest_data.get("data", {}):
                    data = latest_data["data"][ticker]
                    value = safe_numeric(data.get("value", 0))
                    name = data.get("name", ticker)
                    date = data.get("date", "")
                    
                    # Format value based on type
                    if ticker in ["^VIX", "^TNX"]:
                        formatted = f"{value:.2f}"
                    elif ticker in ["CL=F", "NG=F", "GC=F", "SI=F", "HG=F"]:
                        formatted = f"${value:.2f}"
                    else:
                        formatted = f"${value:.2f}"
                    
                    st.metric(label=name, value=formatted, delta=date)

# =========================
# Global Indices
# =========================
st.header("🌍 Global Indices")

global_labels = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI": "Dow Jones",
    "^RUT": "Russell 2000"
}

cols = st.columns(4)
for i, ticker in enumerate(global_indices):
    with cols[i]:
        if ticker in latest_data.get("data", {}):
            data = latest_data["data"][ticker]
            value = safe_numeric(data.get("value", 0))
            date = data.get("date", "")
            st.metric(label=global_labels.get(ticker, ticker), value=f"{value:,.0f}", delta=date)

# Normalized comparison chart for global indices
st.subheader("Normalized Comparison (Base = 100)")
fig, ax = plt.subplots(figsize=(15, 6))

for ticker in global_indices:
    if df_series.get(ticker) is not None:
        series_data = df_series[ticker]["value"].copy()
        series_normalized = (series_data / series_data.iloc[0]) * 100
        ax.plot(series_normalized.index, series_normalized, 
                label=global_labels.get(ticker, ticker), 
                linewidth=2.5, alpha=0.9)

ax.set_title("Global Indices Performance (Normalized)", fontsize=16, fontweight='bold')
ax.set_ylabel("Index (Base = 100)", fontsize=13)
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# Absolute value charts for global indices - 2x2 grid
st.subheader("Absolute Values (4-Column Layout)")
absolute_cols = st.columns(2)
for idx, ticker in enumerate(global_indices):
    if df_series.get(ticker) is not None:
        with absolute_cols[idx % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            series_data = df_series[ticker]["value"].copy()
            ax.plot(series_data.index, series_data, 
                    label=global_labels.get(ticker, ticker), 
                    linewidth=2, color='#2E86AB')
            ax.set_title(f"{global_labels.get(ticker, ticker)}", fontsize=12, fontweight='bold')
            ax.set_ylabel("Price", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

# =========================
# Sector Comparison
# =========================
st.header("📊 Sector Comparison")

sector_etfs = ["XLK", "XLE", "XLF", "XLI", "XLV", "XLY", "XLP", "XLU", "XLB"]
sector_labels = {
    "XLK": "Technology",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLV": "Healthcare",
    "XLY": "Consumer Disc",
    "XLP": "Consumer Staple",
    "XLU": "Utilities",
    "XLB": "Materials"
}

fig, ax = plt.subplots(figsize=(15, 6))

for ticker in sector_etfs:
    if df_series.get(ticker) is not None:
        series_data = df_series[ticker]["value"].copy()
        series_normalized = (series_data / series_data.iloc[0]) * 100
        ax.plot(series_normalized.index, series_normalized, 
                label=sector_labels.get(ticker, ticker), 
                linewidth=2.5, alpha=0.9)

ax.set_title("Sector Performance (Normalized)", fontsize=16, fontweight='bold')
ax.set_ylabel("Index (Base = 100)", fontsize=13)
ax.legend(loc="best", fontsize=10)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# Absolute value charts for sector ETFs - 3x3 grid
st.subheader("Absolute Values (3-Column Layout)")
absolute_cols = st.columns(3)
for idx, ticker in enumerate(sector_etfs):
    if df_series.get(ticker) is not None:
        with absolute_cols[idx % 3]:
            fig, ax = plt.subplots(figsize=(8, 4))
            series_data = df_series[ticker]["value"].copy()
            ax.plot(series_data.index, series_data, 
                    label=sector_labels.get(ticker, ticker), 
                    linewidth=2, color='#2E86AB')
            ax.set_title(f"{sector_labels.get(ticker, ticker)}", fontsize=12, fontweight='bold')
            ax.set_ylabel("Price ($)", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

# =========================
# Commodities
# =========================
st.header("🏭 Commodities")

commodities = ["CL=F", "NG=F", "GC=F", "SI=F", "HG=F"]
commodity_labels = {
    "CL=F": "Crude Oil",
    "NG=F": "Natural Gas",
    "GC=F": "Gold",
    "SI=F": "Silver",
    "HG=F": "Copper"
}

fig, ax = plt.subplots(figsize=(15, 6))

for ticker in commodities:
    if df_series.get(ticker) is not None:
        series_data = df_series[ticker]["value"].copy()
        series_normalized = (series_data / series_data.iloc[0]) * 100
        ax.plot(series_normalized.index, series_normalized, 
                label=commodity_labels.get(ticker, ticker), 
                linewidth=2.5, alpha=0.9)

ax.set_title("Commodities Performance (Normalized)", fontsize=16, fontweight='bold')
ax.set_ylabel("Index (Base = 100)", fontsize=13)
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# Absolute value charts for commodities - 2x3 grid
st.subheader("Absolute Values (3-Column Layout)")
absolute_cols = st.columns(3)
for idx, ticker in enumerate(commodities):
    if df_series.get(ticker) is not None:
        with absolute_cols[idx % 3]:
            fig, ax = plt.subplots(figsize=(8, 4))
            series_data = df_series[ticker]["value"].copy()
            ax.plot(series_data.index, series_data, 
                    label=commodity_labels.get(ticker, ticker), 
                    linewidth=2, color='#2E86AB')
            label = commodity_labels.get(ticker, ticker)
            if ticker in ["CL=F", "NG=F"]:
                ylabel = "Price ($/Bbl)"
            elif ticker in ["GC=F", "SI=F", "HG=F"]:
                ylabel = "Price ($/Oz)"
            else:
                ylabel = "Price"
            ax.set_title(f"{label}", fontsize=12, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

# =========================
# Volatility & Interest Rates
# =========================
st.header("⚠️ Volatility & Interest Rates")

volatility_tickers = ["^VIX", "^TNX", "TLT", "HYG", "DX-Y.NYB"]
volatility_labels = {
    "^VIX": "VIX",
    "^TNX": "US 10Y Yield",
    "TLT": "Long Treasury",
    "HYG": "High Yield Bond",
    "DX-Y.NYB": "Dollar Index"
}

cols = st.columns(5)
for i, ticker in enumerate(volatility_tickers):
    with cols[i]:
        if ticker in latest_data.get("data", {}):
            data = latest_data["data"][ticker]
            value = safe_numeric(data.get("value", 0))
            name = volatility_labels.get(ticker, ticker)
            
            if ticker == "^VIX":
                formatted = f"{value:.2f}"
            elif ticker == "^TNX":
                formatted = f"{value:.2f}%"
            else:
                formatted = f"{value:.2f}"
            
            st.metric(label=name, value=formatted, delta=data.get("date", ""))

# Absolute value charts for volatility tickers - 2x3 grid
st.subheader("Absolute Values (3-Column Layout)")
absolute_cols = st.columns(3)
for idx, ticker in enumerate(volatility_tickers):
    if df_series.get(ticker) is not None:
        with absolute_cols[idx % 3]:
            fig, ax = plt.subplots(figsize=(8, 4))
            series_data = df_series[ticker]["value"].copy()
            ax.plot(series_data.index, series_data, 
                    label=volatility_labels.get(ticker, ticker), 
                    linewidth=2, color='#2E86AB')
            label = volatility_labels.get(ticker, ticker)
            if ticker == "^TNX":
                ylabel = "Yield (%)"
            elif ticker == "^VIX":
                ylabel = "VIX Index"
            else:
                ylabel = "Price ($)"
            ax.set_title(f"{label}", fontsize=12, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

# =========================
# International Markets
# =========================
st.header("🌍 International Markets")

international_tickers = ["FXI", "INDA", "EWJ", "EWY", "EWT"]
international_labels = {
    "FXI": "China",
    "INDA": "India",
    "EWJ": "Japan",
    "EWY": "Korea",
    "EWT": "Taiwan"
}

cols = st.columns(5)
for i, ticker in enumerate(international_tickers):
    with cols[i]:
        if ticker in latest_data.get("data", {}):
            data = latest_data["data"][ticker]
            value = safe_numeric(data.get("value", 0))
            name = international_labels.get(ticker, ticker)
            
            formatted = f"${value:.2f}"
            
            st.metric(label=name, value=formatted, delta=data.get("date", ""))

# International comparison chart
fig, ax = plt.subplots(figsize=(15, 6))

for ticker in international_tickers:
    if df_series.get(ticker) is not None:
        series_data = df_series[ticker]["value"].copy()
        series_normalized = (series_data / series_data.iloc[0]) * 100
        ax.plot(series_normalized.index, series_normalized, 
                label=international_labels.get(ticker, ticker), 
                linewidth=2.5, alpha=0.9)

ax.set_title("International Markets Performance (Normalized)", fontsize=16, fontweight='bold')
ax.set_ylabel("Index (Base = 100)", fontsize=13)
ax.legend(loc="best", fontsize=10)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# Absolute value charts for international markets - 2x3 grid
st.subheader("Absolute Values (3-Column Layout)")
absolute_cols = st.columns(3)
for idx, ticker in enumerate(international_tickers):
    if df_series.get(ticker) is not None:
        with absolute_cols[idx % 3]:
            fig, ax = plt.subplots(figsize=(8, 4))
            series_data = df_series[ticker]["value"].copy()
            ax.plot(series_data.index, series_data, 
                    label=international_labels.get(ticker, ticker), 
                    linewidth=2, color='#2E86AB')
            ax.set_title(f"{international_labels.get(ticker, ticker)}", fontsize=12, fontweight='bold')
            ax.set_ylabel("Price ($)", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

# =========================
# Recent Data Table
# =========================
st.header("📋 Recent Data")

# Remove ^GSPC from defaults since it was causing issues
selected_tickers = st.multiselect(
    "Select tickers to display:",
    all_tickers,
    default=["XLK", "XLE", "XLF", "^VIX", "FXI"]
)

if selected_tickers:
    for ticker in selected_tickers:
        if df_series.get(ticker) is not None:
            st.subheader(f"{ticker}")
            df_display = df_series[ticker].tail(10).copy()
            df_display = df_display.reset_index()
            df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
            df_display = df_display.rename(columns={'value': 'Close'})
            st.dataframe(df_display, use_container_width=True)

# =========================
# Ticker Search
# =========================
st.header("🔍 Search Ticker")

search_query = st.text_input("Enter ticker symbol:", "").upper()

if search_query:
    if search_query in df_series and df_series[search_query] is not None:
        st.subheader(f"{search_query}")
        df_display = df_series[search_query].copy()
        df_display = df_display.reset_index()
        df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
        df_display = df_display.rename(columns={'value': 'Close'})
        
        # Display current value
        if search_query in latest_data.get("data", {}):
            data = latest_data["data"][search_query]
            st.metric(label=data.get("name", search_query), 
                     value=f"${safe_numeric(data.get('value', 0)):.2f}",
                     delta=data.get("date", ""))
        
        st.dataframe(df_display.tail(20), use_container_width=True)
        
        # Plot
        fig, ax = plt.subplots(figsize=(15, 4))
        ax.plot(df_display['date'], df_display['Close'], linewidth=2)
        ax.set_title(f"{search_query} Price History", fontsize=14, fontweight='bold')
        ax.set_ylabel("Price ($)", fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning(f"Ticker '{search_query}' not found in data")

# =========================
# Footer
# =========================
st.markdown("---")
st.caption("Data: Yahoo Finance | Visualizations: Streamlit + Matplotlib")
