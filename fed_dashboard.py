#!/usr/bin/env python3
"""
FED Data Streamlit Dashboard
- FRED: macro indicators (FEDFUNDS, M2SL, WALCL, OBFR, etc.)
- Clean, interactive visualizations
- Date range selector for all graphs
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
# Page Config
# =========================
st.set_page_config(
    page_title="FED Economic Dashboard",
    page_icon="📊",
    layout="wide"
)

# =========================
# Seaborn Styling
# =========================
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (15, 6)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.grid'] = True
plt.rcParams['axes.grid.axis'] = 'both'
plt.rcParams['axes.linewidth'] = 0.5
plt.rcParams['grid.color'] = 'lightgray'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 0.8

# =========================
# Paths
# =========================
DATA_DIR = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")

st.title("📊 FED Economic Dashboard")
st.markdown(f"""
Real-time Federal Reserve economic indicators and liquidity metrics.
Data source: [FRED](https://fred.stlouisfed.org/) | Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
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
    """Load FRED data from JSON files (cached for 1 hour)"""
    with open(DATA_DIR / "fed_data_latest.json", 'r') as f:
        latest_data = json.load(f)
    
    with open(DATA_DIR / "fed_data_historical.json", 'r') as f:
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

# =========================
# Load All Series
# =========================
series_to_load = ["FEDFUNDS", "M2SL", "WALCL", "OBFR", "MORTGAGE30US", 
                  "RRPONTSYD", "WTREGEN", "SP500", "NASDAQ100", "SOX"]

df_series = {}
for key in series_to_load:
    df_series[key] = safe_load_series(key, historical_data, start_date, end_date)

# =========================
# Calculate Net Liquidity
# =========================
liquidity_df = None
if all(k in df_series for k in ["WALCL", "WTREGEN", "RRPONTSYD"]):
    walcl = df_series["WALCL"].rename(columns={"value": "WALCL"})
    tga = df_series["WTREGEN"].rename(columns={"value": "TGA"})
    rrp = df_series["RRPONTSYD"].rename(columns={"value": "RRP"})
    
    # Combine and align dates
    liquidity_df = pd.concat([walcl, tga, rrp], axis=1).dropna()
    liquidity_df["Net_Liquidity"] = liquidity_df["WALCL"] - liquidity_df["TGA"] - liquidity_df["RRP"]
    
    # Calculate rolling averages
    liquidity_df["Liquidity_30d_MA"] = liquidity_df["Net_Liquidity"].rolling(window=30).mean()
    liquidity_df["Liquidity_90d_MA"] = liquidity_df["Net_Liquidity"].rolling(window=90).mean()

# =========================
# Key Metrics (Current Values)
# =========================
st.header("🔑 Key Economic Indicators")

cols = st.columns(5)

key_metrics = [
    ("FEDFUNDS", "Fed Funds Rate", "%"),
    ("M2SL", "M2 Money Supply", "B"),
    ("OBFR", "Overnight Bank Funding", "%"),
    ("RRPONTSYD", "Reverse Repo", "B"),
    ("WTREGEN", "Treasury General", "B"),
]

metric_cols = cols[:len(key_metrics)]
for i, (key, name, unit) in enumerate(key_metrics):
    with metric_cols[i]:
        if key in latest_data.get("data", {}):
            data = latest_data["data"][key]
            value = safe_numeric(data.get("value", 0))
            if unit == "%":
                formatted = f"{value:.2f}%"
            elif unit == "B":
                formatted = f"${value/1000:.2f}B"
            else:
                formatted = f"{value:,.0f}"
            
            st.metric(label=name, value=formatted, delta=data.get("date", ""))

# Net Liquidity card
with metric_cols[4 if len(key_metrics) >= 5 else len(key_metrics)]:
    if liquidity_df is not None and len(liquidity_df) > 0:
        current_liquidity = liquidity_df["Net_Liquidity"].iloc[-1]
        prev_liquidity = liquidity_df["Net_Liquidity"].iloc[-2] if len(liquidity_df) > 1 else current_liquidity
        delta = current_liquidity - prev_liquidity
        
        st.metric(
            label="Net Liquidity",
            value=f"${current_liquidity/1000:.2f}B",
            delta=f"{delta/1000:+.2f}B"
        )

# =========================
# Liquidity Dashboard
# =========================
st.header("💸 Liquidity Analysis")

if liquidity_df is not None and len(liquidity_df) > 0:
    fig, ax = plt.subplots(figsize=(15, 6))
    
    # Plot net liquidity using seaborn style
    ax.plot(liquidity_df.index, liquidity_df["Net_Liquidity"], 
            label="Net Liquidity (WALCL - TGA - RRP)", 
            linewidth=2.5, color="#2E86AB")
    
    # Plot moving averages
    if "Liquidity_30d_MA" in liquidity_df.columns:
        ax.plot(liquidity_df.index, liquidity_df["Liquidity_30d_MA"], 
                label="30-day MA", linestyle="--", color="#A23B72", linewidth=2)
    
    if "Liquidity_90d_MA" in liquidity_df.columns:
        ax.plot(liquidity_df.index, liquidity_df["Liquidity_90d_MA"], 
                label="90-day MA", linestyle="--", color="#F18F01", linewidth=2)
    
    ax.set_title("Net Liquidity Trends", fontsize=16, fontweight='bold')
    ax.set_ylabel("Billions of $", fontsize=13)
    ax.set_xlabel("Date", fontsize=13)
    ax.legend(loc="best", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', which='major', labelsize=11)
    
    # Add zero line
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.3, linewidth=1)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Liquidity Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Net Liquidity = WALCL - TGA - RRP**")
    with col2:
        current = liquidity_df["Net_Liquidity"].iloc[-1]
        st.success(f"Current: ${current/1000:.2f}B" if current > 0 else f"Current: ${current/1000:.2f}B")
    with col3:
        st.warning("Positive = Money to market | Negative = Money absorbed")
else:
    st.warning("Liquidity data unavailable")

# =========================
# Interest Rates
# =========================
st.header("📈 Interest Rates & Monetary Policy")

rate_series = ["FEDFUNDS", "OBFR", "MORTGAGE30US"]
rate_labels = {
    "FEDFUNDS": "Fed Funds Rate",
    "OBFR": "Overnight Bank Funding",
    "MORTGAGE30US": "30-Year Mortgage"
}
rate_colors = ["#016450", "#014636", "#CC4C02"]

fig, ax = plt.subplots(figsize=(15, 5))

for i, key in enumerate(rate_series):
    if df_series.get(key) is not None:
        ax.plot(df_series[key].index, df_series[key]["value"], 
                label=rate_labels.get(key, key),
                linewidth=2, color=rate_colors[i])

ax.set_title("Interest Rates Over Time", fontsize=16, fontweight='bold')
ax.set_ylabel("Rate (%)", fontsize=13)
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# =========================
# Money Supply
# =========================
st.header("💰 Money Supply & Credit")

fig, ax = plt.subplots(figsize=(15, 5))

if df_series.get("M2SL") is not None:
    ax.plot(df_series["M2SL"].index, df_series["M2SL"]["value"], 
            label="M2 Money Supply", linewidth=2.5, color="#2E86AB")
    
    # Add moving average
    m2_ma = df_series["M2SL"]["value"].rolling(window=12).mean()
    ax.plot(df_series["M2SL"].index, m2_ma, 
            label="12-Month MA", linestyle="--", color="#A23B72", linewidth=2)

ax.set_title("M2 Money Supply", fontsize=16, fontweight='bold')
ax.set_ylabel("Billions of $", fontsize=13)
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# =========================
# Asset Markets
# =========================
st.header("📊 Asset Market Performance")

market_series = ["SP500", "NASDAQ100", "SOX"]
market_labels = {
    "SP500": "S&P 500",
    "NASDAQ100": "NASDAQ 100",
    "SOX": "SOX (Semiconductors)"
}

# Normalized comparison
fig, ax = plt.subplots(figsize=(15, 6))

if liquidity_df is not None:
    # Normalize liquidity to start at 100
    liquidity_norm = liquidity_df["Net_Liquidity"].copy()
    liquidity_norm = (liquidity_norm / liquidity_norm.iloc[0]) * 100
    ax.plot(liquidity_norm.index, liquidity_norm, 
            label="Net Liquidity (Norm)", linestyle="--", color="gray", linewidth=2, alpha=0.7)

for i, key in enumerate(market_series):
    if df_series.get(key) is not None:
        series_data = df_series[key]["value"].copy()
        series_normalized = (series_data / series_data.iloc[0]) * 100
        ax.plot(series_normalized.index, series_normalized, 
                label=market_labels.get(key, key), linewidth=2.5, alpha=0.9, marker='o', markersize=3)

ax.set_title("Normalized Comparison (Base = 100)", fontsize=16, fontweight='bold')
ax.set_ylabel("Index (Base = 100)", fontsize=13)
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=11)

plt.tight_layout()
st.pyplot(fig)

# =========================
# Recent Data Table
# =========================
st.header("📋 Recent Data")

selected_series = st.multiselect(
    "Select series to display:",
    series_to_load,
    default=["FEDFUNDS", "M2SL", "WALCL", "RRPONTSYD", "SOX"]
)

if selected_series:
    for key in selected_series:
        if df_series.get(key) is not None:
            st.subheader(f"{historical_data['data'][key]['name']}")
            df_display = df_series[key].tail(10).copy()
            df_display = df_display.reset_index()
            df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_display, use_container_width=True)

# =========================
# Algorithm Explanation
# =========================
st.header("💡 Liquidity Algorithm")

st.markdown("""
### Core Concept
**Net Liquidity = WALCL - TGA - RRP**

This represents the net flow of money into the financial system:

| Metric | Description |
|--------|-------------|
| **WALCL** | Total assets on Fed's balance sheet → *Money supply from Treasury* |
| **TGA** | Treasury General Account → *Money absorbed by Treasury* |
| **RRP** | Reverse Repo Rate → *Money absorbed by Fed* |

### Interpretation
- **Positive Net Liquidity** = Money flowing to market (bullish)
- **Negative Net Liquidity** = Money being absorbed by Fed/Treasury (bearish)

### Key Indicators
1. **Fed Funds Rate** → Benchmark interest rate
2. **M2 Money Supply** → Broad money supply
3. **Reverse Repo** → Emergency lending facility
4. **Net Liquidity** → Overall market liquidity
""")

# =========================
# Footer
# =========================
st.markdown("---")
st.caption("Data: FRED (St. Louis Fed) | Visualizations: Streamlit + Matplotlib")