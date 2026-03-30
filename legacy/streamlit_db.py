import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

# --- DB CONFIG ---
DB_USER = os.getenv("POSTGRES_USER", "dmlab_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "dmlab_pass")
DB_NAME = os.getenv("POSTGRES_DB", "dmlab_db")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5440")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data():
    query = "SELECT * FROM daily_prices_adjusted"
    df = pd.read_sql(query, engine, parse_dates=['date'])
    return df

df = load_data()

# --- Metric Labels and Descriptions ---
metric_info = {
    "close": ("Closing Price", "The last trading price of the stock for the selected day."),
    "volume": ("Volume", "The number of shares traded during the day."),
    "ma_5": ("MA 5", "5-day moving average: short-term trend based on past 5 days' closing prices."),
    "ma_63": ("MA 63", "63-day moving average: mid-term trend (approx. 1 quarter)."),
    "ma_126": ("MA 126", "126-day moving average: reflects half-year price trend."),
    "ma_252": ("MA 252", "252-day moving average: long-term price trend over a full trading year."),
    "volatility_30d": ("30D Volatility", "30-day rolling standard deviation of daily returns. Higher = riskier."),
    "macd": ("MACD", "Moving Average Convergence Divergence: a trend-following momentum indicator."),
    "rsi": ("RSI", "Relative Strength Index (0–100): above 70 = overbought, below 30 = oversold.")
}

metric_options = list(metric_info.keys())
metric_labels = {k: v[0] for k, v in metric_info.items()}
metric_descriptions = {k: v[1] for k, v in metric_info.items()}

# --- Sidebar Controls ---
st.sidebar.header("Filter Options")
tickers = df["ticker"].unique().tolist()
selected_ticker = st.sidebar.selectbox("Select Ticker", tickers)

dates = df[df["ticker"] == selected_ticker]["date"]
start_date = st.sidebar.date_input("Start Date", value=dates.min(), min_value=dates.min(), max_value=dates.max())
end_date = st.sidebar.date_input("End Date", value=dates.max(), min_value=dates.min(), max_value=dates.max())

# Friendly multiselect
selected_labels = st.sidebar.multiselect(
    "Metrics to Display",
    options=[metric_labels[k] for k in metric_options],
    default=[metric_labels["close"], metric_labels["ma_63"], metric_labels["rsi"]]
)

# Map selected labels back to keys
label_to_key = {v: k for k, v in metric_labels.items()}
selected_metrics = [label_to_key[label] for label in selected_labels]

# --- Metric Explanations ---
with st.expander("ℹ️ Metric Descriptions"):
    for metric in selected_metrics:
        st.markdown(f"**{metric_labels[metric]}**: {metric_descriptions[metric]}")

# --- Filter Data ---
filtered_df = df[
    (df["ticker"] == selected_ticker) &
    (df["date"] >= pd.to_datetime(start_date)) &
    (df["date"] <= pd.to_datetime(end_date))
]

# --- Dashboard View ---
st.title(f"📊 Financial Dashboard for {selected_ticker}")
st.markdown("Use the filters on the left to explore the data interactively.")

if filtered_df.empty:
    st.warning("No data available for the selected range.")
else:
    for metric in selected_metrics:
        label = metric_labels[metric]
        fig = px.line(
            filtered_df,
            x="date",
            y=metric,
            title=f"{label} over Time",
            labels={"date": "Date", metric: label}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Optionally rename columns for the table
    renamed_df = filtered_df[["date", "ticker"] + selected_metrics].rename(columns=metric_labels)
    st.dataframe(renamed_df.sort_values("date", ascending=False).reset_index(drop=True))
