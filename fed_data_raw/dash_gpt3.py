import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

st.set_page_config(layout="wide")

DATA = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")

# =========================
# STYLE SELECTOR
# =========================
style = st.sidebar.selectbox(
    "Seaborn Style",
    ["darkgrid", "whitegrid", "dark", "white", "ticks"]
)
sns.set_style(style)

st.title("📊 Liquidity + Market Dashboard (Stable Version)")


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    with open(DATA / "fed_data_historical.json") as f:
        hist = json.load(f)

    with open(DATA / "fed_data_latest.json") as f:
        latest = json.load(f)

    return hist, latest


hist, latest = load_data()


# =========================
# SAFE SERIES LOADER
# =========================
def load_series(key):
    if key not in hist["data"]:
        return None

    df = pd.DataFrame(hist["data"][key]["observations"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna()
    df = df.sort_values("date").set_index("date")

    if len(df) == 0:
        return None

    return df


# =========================
# LOAD SERIES
# =========================
walcl = load_series("WALCL")
tga = load_series("WTREGEN")
rrp = load_series("RRPONTSYD")

sox = load_series("SOX")
spx = load_series("SP500")
ndx = load_series("NASDAQ100")

# Load stock data
samsung = load_series("005930.KS")
sk_hynix = load_series("000660.KS")
sk_square = load_series("096770.KS")


# =========================
# DATE RANGE (AUTO DETECT)
# =========================
# Auto-detect minimum and maximum dates from available data
all_dates = []

# Collect all dates from available series
series_to_check = ["WALCL", "WTREGEN", "RRPONTSYD", "SOX", "SP500", "NASDAQ100"]
for series_id in series_to_check:
    if series_id in hist["data"]:
        try:
            dates = [obs['date'] for obs in hist["data"][series_id]["observations"] if 'date' in obs]
            if dates:
                all_dates.extend(dates)
        except Exception:
            continue

if all_dates:
    # Convert to datetime objects and find min/max
    try:
        date_objects = [pd.to_datetime(date, errors='coerce') for date in all_dates]
        date_objects = [d for d in date_objects if pd.notna(d)]
        if date_objects:
            min_date = min(date_objects).date()
            max_date = max(date_objects).date()
        else:
            min_date = pd.Timestamp("2000-01-01")
            max_date = pd.Timestamp.today()
    except Exception:
        min_date = pd.Timestamp("2000-01-01")
        max_date = pd.Timestamp.today()
else:
    min_date = pd.Timestamp("2000-01-01")
    max_date = pd.Timestamp.today()

start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)


def filter_df(df):
    if df is None:
        return None
    return df[(df.index >= pd.Timestamp(start_date)) &
              (df.index <= pd.Timestamp(end_date))]


walcl = filter_df(walcl)
tga = filter_df(tga)
rrp = filter_df(rrp)
sox = filter_df(sox)
spx = filter_df(spx)
ndx = filter_df(ndx)
samsung = filter_df(samsung)
sk_hynix = filter_df(sk_hynix)
sk_square = filter_df(sk_square)


# =========================
# LIQUIDITY (FIXED: NO DROPNA TRAP)
# =========================
st.header("Liquidity")

liquidity = None

if walcl is not None and tga is not None and rrp is not None:

    df_liq = pd.concat(
        [
            walcl.rename(columns={"value": "WALCL"}),
            tga.rename(columns={"value": "TGA"}),
            rrp.rename(columns={"value": "RRP"}),
        ],
        axis=1,
        join="outer"   # 🔥 핵심: inner 금지
    )

    df_liq = df_liq.sort_index()

    # forward fill로 연속성 확보
    df_liq = df_liq.ffill()

    df_liq["Liquidity"] = df_liq["WALCL"] - df_liq["TGA"] - df_liq["RRP"]

    liquidity = df_liq


# =========================
# LIQUIDITY PLOT
# =========================
if liquidity is not None:

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.lineplot(data=liquidity, x=liquidity.index, y="Liquidity", ax=ax)
    ax.set_title("Net Liquidity (WALCL - TGA - RRP)")
    ax.grid()

    st.pyplot(fig)
else:
    st.warning("Liquidity missing")


# =========================
# MARKET PLOTS (SAFE)
# =========================
st.header("Markets")


def plot_series(df, title):

    if df is None:
        st.warning(f"{title} missing")
        return

    fig, ax = plt.subplots(figsize=(12, 3))
    sns.lineplot(x=df.index, y=df["value"], ax=ax)
    ax.set_title(title)
    ax.grid()
    st.pyplot(fig)


plot_series(sox, "SOX (Philadelphia Semiconductor)")
plot_series(spx, "S&P 500")
plot_series(ndx, "NASDAQ 100")
plot_series(samsung, "Samsung (005930.KS)")
plot_series(sk_hynix, "SK Hynix (000660.KS)")
plot_series(sk_square, "SK Square (096770.KS)")


# =========================
# NORMALIZED (FIXED ALIGNMENT)
# =========================
st.header("Normalized Comparison")

fig, ax = plt.subplots(figsize=(12, 5))


def norm(df):
    if df is None or len(df) == 0:
        return None
    return df["value"] / df["value"].iloc[0] * 100


if liquidity is not None:
    l = liquidity["Liquidity"].dropna()
    ax.plot(l.index, l / l.iloc[0] * 100, label="Liquidity")

# Add normalized stock data
stocks = [
    (samsung, "Samsung"),
    (sk_hynix, "SK Hynix"),
    (sk_square, "SK Square")
]

for stock_df, name in stocks:
    if stock_df is not None:
        norm_stock = norm(stock_df)
        if norm_stock is not None:
            ax.plot(norm_stock.index, norm_stock, label=name)

# Add normalized market data
markets = [
    (sox, "SOX"),
    (spx, "S&P 500"),
    (ndx, "NASDAQ 100")
]

for market_df, name in markets:
    if market_df is not None:
        norm_market = norm(market_df)
        if norm_market is not None:
            ax.plot(norm_market.index, norm_market, label=name)

ax.set_title("Normalized Time Series Comparison")
ax.set_ylabel("Normalized Value (100 = Start)")
ax.legend()
ax.grid()

st.pyplot(fig)

if sox is not None:
    s = norm(sox)
    ax.plot(sox.index, s, label="SOX")

if spx is not None:
    s = norm(spx)
    ax.plot(spx.index, s, label="SP500")

if ndx is not None:
    n = norm(ndx)
    ax.plot(ndx.index, n, label="NASDAQ100")

ax.legend()
ax.grid()

st.pyplot(fig)


# =========================
# DEBUG
# =========================
st.header("Debug")

st.write({
    "SOX": 0 if sox is None else len(sox),
    "SP500": 0 if spx is None else len(spx),
    "NASDAQ100": 0 if ndx is None else len(ndx),
    "Liquidity": 0 if liquidity is None else len(liquidity)
})