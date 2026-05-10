import streamlit as st
import pandas as pd
import json
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(layout="wide")

DATA = Path("/home/slreflex2/Desktop/agent_projects/fed_data_raw")


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
# SAFE LOADER
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
# DATE FILTER (NEW)
# =========================
st.sidebar.header("Date Filter")

min_date = pd.to_datetime("2000-01-01")
max_date = pd.to_datetime("today")

start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)


def filter_df(df):
    if df is None:
        return None
    return df[(df.index >= pd.to_datetime(start_date)) &
              (df.index <= pd.to_datetime(end_date))]


# =========================
# LOAD SERIES
# =========================
series_keys = [
    "WALCL", "WTREGEN", "RRPONTSYD",
    "FEDFUNDS", "M2SL", "MORTGAGE30US",
    "OBFR"
]

data = {k: filter_df(load_series(k)) for k in series_keys}


sox = filter_df(load_series("SOX"))
spx = filter_df(load_series("SP500"))
ndx = filter_df(load_series("NASDAQ100"))


# =========================
# TITLE
# =========================
st.title("📊 FED Macro + Liquidity + Market Dashboard")


# =========================
# LIQUIDITY
# =========================
st.header("Liquidity")

if data["WALCL"] is not None and data["WTREGEN"] is not None and data["RRPONTSYD"] is not None:

    df_liq = pd.concat([
        data["WALCL"].rename(columns={"value": "WALCL"}),
        data["WTREGEN"].rename(columns={"value": "TGA"}),
        data["RRPONTSYD"].rename(columns={"value": "RRP"}),
    ], axis=1).dropna()

    df_liq["Liquidity"] = df_liq["WALCL"] - df_liq["TGA"] - df_liq["RRP"]

    sns.set_theme(style="darkgrid")

    fig, ax = plt.subplots(figsize=(12,4))
    sns.lineplot(data=df_liq["Liquidity"], ax=ax)

    ax.set_title("Net Liquidity")
    st.pyplot(fig)

    liquidity = df_liq

else:
    liquidity = None
    st.warning("Liquidity missing")


# =========================
# FED MACRO (NEW SECTION)
# =========================
st.header("FED Macro Indicators (All)")

for k, df in data.items():

    if df is None:
        continue

    fig, ax = plt.subplots(figsize=(12,3))
    sns.lineplot(data=df["value"], ax=ax)

    ax.set_title(k)
    st.pyplot(fig)


# =========================
# MARKETS
# =========================
st.header("Markets")

def plot_market(df, name):

    if df is None:
        st.warning(f"{name} missing")
        return

    fig, ax = plt.subplots(figsize=(12,3))
    sns.lineplot(data=df["value"], ax=ax)

    ax.set_title(name)
    st.pyplot(fig)


plot_market(sox, "SOX")
plot_market(spx, "S&P 500")
plot_market(ndx, "NASDAQ100")


# =========================
# NORMALIZED COMPARISON
# =========================
st.header("Normalized Comparison")

fig, ax = plt.subplots(figsize=(12,5))

def norm(df):
    return df["value"] / df["value"].iloc[0] * 100


if liquidity is not None:
    sns.lineplot(
        x=liquidity.index,
        y=liquidity["Liquidity"] / liquidity["Liquidity"].iloc[0] * 100,
        label="Liquidity",
        ax=ax
    )

if sox is not None:
    sns.lineplot(x=sox.index, y=norm(sox), ax=ax, label="SOX")

if spx is not None:
    sns.lineplot(x=spx.index, y=norm(spx), ax=ax, label="SP500")

if ndx is not None:
    sns.lineplot(x=ndx.index, y=norm(ndx), ax=ax, label="NASDAQ100")

ax.legend()
ax.set_title("Normalized Comparison")
st.pyplot(fig)


# =========================
# DEBUG
# =========================
st.header("Debug Info")

st.write({
    k: (len(v) if v is not None else 0)
    for k, v in data.items()
})

st.write({
    "SOX": 0 if sox is None else len(sox),
    "SP500": 0 if spx is None else len(spx),
    "NASDAQ100": 0 if ndx is None else len(ndx),
    "Liquidity": 0 if liquidity is None else len(liquidity)
})