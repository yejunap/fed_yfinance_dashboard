import streamlit as st
import pandas as pd
import json
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
# SAFE LOADER (핵심)
# =========================
def load_series(key):

    if key not in hist["data"]:
        return None

    df = pd.DataFrame(hist["data"][key]["observations"])

    # 안전 처리 (이거 없으면 100% 깨짐)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna()
    df = df.sort_values("date")
    df = df.set_index("date")

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


# =========================
# LIQUIDITY (SAFE)
# =========================
st.title("📊 Liquidity + Market Dashboard")

liquidity = None

if walcl is not None and tga is not None and rrp is not None:

    df_liq = pd.concat(
        [
            walcl.rename(columns={"value": "WALCL"}),
            tga.rename(columns={"value": "TGA"}),
            rrp.rename(columns={"value": "RRP"}),
        ],
        axis=1
    ).dropna()

    df_liq["Liquidity"] = df_liq["WALCL"] - df_liq["TGA"] - df_liq["RRP"]

    liquidity = df_liq


# =========================
# LIQUIDITY PLOT
# =========================
st.header("Liquidity")

if liquidity is not None:

    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(liquidity.index, liquidity["Liquidity"])
    ax.set_title("Net Liquidity (WALCL - TGA - RRP)")
    ax.grid()

    st.pyplot(fig)

else:
    st.warning("Liquidity data missing")


# =========================
# MARKET PLOTS
# =========================
st.header("Markets")

def plot_series(df, title):

    if df is None:
        st.warning(f"{title} missing")
        return

    fig, ax = plt.subplots(figsize=(12,3))
    ax.plot(df.index, df["value"])
    ax.set_title(title)
    ax.grid()
    st.pyplot(fig)


plot_series(sox, "SOX (Philadelphia Semiconductor)")
plot_series(spx, "S&P 500")
plot_series(ndx, "NASDAQ 100")


# =========================
# NORMALIZED COMPARISON
# =========================
st.header("Normalized Comparison")

fig, ax = plt.subplots(figsize=(12,5))

def norm(df):
    return df["value"] / df["value"].iloc[0] * 100

if liquidity is not None:
    ax.plot(liquidity.index, liquidity["Liquidity"] / liquidity["Liquidity"].iloc[0] * 100,
            label="Liquidity (norm)")

if sox is not None:
    ax.plot(sox.index, norm(sox), label="SOX")

if spx is not None:
    ax.plot(spx.index, norm(spx), label="SP500")

if ndx is not None:
    ax.plot(ndx.index, norm(ndx), label="NASDAQ100")

ax.legend()
ax.grid()

st.pyplot(fig)


# =========================
# DEBUG PANEL
# =========================
st.header("Debug Info")

st.write({
    "SOX rows": 0 if sox is None else len(sox),
    "SP500 rows": 0 if spx is None else len(spx),
    "NASDAQ100 rows": 0 if ndx is None else len(ndx),
    "Liquidity rows": 0 if liquidity is None else len(liquidity)
})