import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

from src.etl.metrics import MetricsCalculator
from src.ml.forecasting import train_forecast_from_df

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Prediction",
    page_icon="📈",
    layout="wide",
)

PRESETS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL", "NFLX"]

MODEL_INFO = {
    "linear":        ("Linear Regression",   None),
    "random_forest": ("Random Forest",        None),
    "lstm":          ("LSTM (Deep Learning)", "tensorflow"),
    "prophet":       ("Prophet",              "prophet"),
}


# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Fetching market data…")
def load_stock_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    raw = yf.Ticker(ticker).history(start=start, end=end)
    if raw.empty:
        return pd.DataFrame()
    raw = raw.reset_index()
    raw.columns = [c.lower().replace(" ", "_") for c in raw.columns]
    raw["ticker"] = ticker.upper()
    raw["date"] = pd.to_datetime(raw["date"]).dt.tz_localize(None)
    raw = raw[["ticker", "date", "open", "high", "low", "close", "volume"]]
    return MetricsCalculator(raw).get_adjusted_table()


@st.cache_data(ttl=300, show_spinner="Training forecast model…")
def get_forecast(ticker: str, start: str, end: str, days_ahead: int, model_type: str) -> dict:
    df = load_stock_data(ticker, start, end)
    return train_forecast_from_df(df, days_ahead=days_ahead, model_type=model_type)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
if "ticker" not in st.session_state:
    st.session_state["ticker"] = "AAPL"


def _set_ticker(t: str) -> None:
    st.session_state["ticker"] = t


with st.sidebar:
    st.title("📈 Stock Prediction")
    st.caption("Live data via yfinance · No database required")

    ticker_raw = st.text_input(
        "Ticker Symbol",
        value=st.session_state["ticker"],
        help="NYSE / NASDAQ ticker, e.g. AAPL, MSFT, NVDA",
    )
    ticker = ticker_raw.upper().strip() or "AAPL"
    st.session_state["ticker"] = ticker

    st.caption("Quick select:")
    preset_cols = st.columns(4)
    for i, t in enumerate(PRESETS):
        preset_cols[i % 4].button(
            t,
            key=f"btn_{t}",
            on_click=_set_ticker,
            args=(t,),
            use_container_width=True,
        )

    st.divider()

    default_start = datetime.today() - timedelta(days=365 * 3)
    start = st.date_input("Start Date", value=default_start.date())
    end   = st.date_input("End Date",   value=datetime.today().date())

    st.divider()

    st.caption("**Forecast Settings**")
    model_type = st.selectbox(
        "Model",
        options=list(MODEL_INFO.keys()),
        format_func=lambda k: MODEL_INFO[k][0],
    )
    days_ahead = st.selectbox("Days Ahead", [7, 14, 30, 60], index=2)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = load_stock_data(ticker, str(start), str(end))

if df.empty:
    st.error(f"No data found for **{ticker}**. Please check the ticker symbol and date range.")
    st.stop()

# Use the latest row that has a valid close price
valid = df.dropna(subset=["close"])
latest = valid.iloc[-1]
prev   = valid.iloc[-2]
delta  = latest["close"] - prev["close"]
pct    = delta / prev["close"] * 100


# ── HEADER KPIs ───────────────────────────────────────────────────────────────
st.title(f"📈  {ticker}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Close Price",    f"${latest['close']:.2f}",          f"{delta:+.2f}  ({pct:+.2f}%)")
k2.metric("Volume",         f"{int(latest['volume']):,}")
k3.metric("RSI (14d)",      f"{latest['rsi']:.1f}"              if pd.notna(latest.get("rsi"))           else "—")
k4.metric("Volatility 30d", f"{latest['volatility_30d']:.4f}"   if pd.notna(latest.get("volatility_30d")) else "—")

st.divider()


# ── TABS ──────────────────────────────────────────────────────────────────────
tab_price, tab_indicators, tab_forecast = st.tabs(
    ["📊  Price & Moving Averages", "📉  Technical Indicators", "🔮  Forecast"]
)


# ── TAB 1: PRICE ──────────────────────────────────────────────────────────────
with tab_price:
    MA_OPTIONS = {
        "MA 5d":   ("ma_5",   "#f0a500"),
        "MA 63d":  ("ma_63",  "#e35050"),
        "MA 126d": ("ma_126", "#6ab04c"),
        "MA 252d": ("ma_252", "#9b59b6"),
    }
    selected_mas = st.multiselect(
        "Moving Averages",
        options=list(MA_OPTIONS.keys()),
        default=["MA 63d", "MA 252d"],
    )

    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=df["date"], y=df["close"],
        name="Close", line=dict(color="#1f77b4", width=1.5),
    ))
    for label in selected_mas:
        col, color = MA_OPTIONS[label]
        fig_price.add_trace(go.Scatter(
            x=df["date"], y=df[col], name=label,
            line=dict(dash="dot", width=1, color=color),
        ))
    fig_price.update_layout(
        height=420, xaxis_title="Date", yaxis_title="Price (USD)",
        hovermode="x unified", legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_price, use_container_width=True)

    fig_vol = go.Figure(go.Bar(
        x=df["date"], y=df["volume"],
        marker_color="#aec7e8", name="Volume",
    ))
    fig_vol.update_layout(
        height=180, xaxis_title="Date", yaxis_title="Volume", showlegend=False,
    )
    st.plotly_chart(fig_vol, use_container_width=True)


# ── TAB 2: TECHNICAL INDICATORS ───────────────────────────────────────────────
with tab_indicators:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("RSI (14-day)")
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red",   opacity=0.05)
        fig_rsi.add_hrect(y0=0,  y1=30,  fillcolor="green", opacity=0.05)
        fig_rsi.add_trace(go.Scatter(
            x=df["date"], y=df["rsi"], name="RSI",
            line=dict(color="#ff7f0e", width=1.5),
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",   line_width=1,
                          annotation_text="Overbought (70)", annotation_position="top left")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", line_width=1,
                          annotation_text="Oversold (30)",   annotation_position="bottom left")
        fig_rsi.update_layout(height=300, yaxis=dict(range=[0, 100]), hovermode="x unified")
        st.plotly_chart(fig_rsi, use_container_width=True)

    with c2:
        st.subheader("MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(
            x=df["date"], y=df["macd"], name="MACD",
            fill="tozeroy", line=dict(color="#1f77b4", width=1.5),
        ))
        fig_macd.add_hline(y=0, line_dash="dot", line_color="grey", line_width=1)
        fig_macd.update_layout(height=300, hovermode="x unified")
        st.plotly_chart(fig_macd, use_container_width=True)

    st.subheader("30-Day Rolling Volatility")
    fig_volatility = px.line(
        df, x="date", y="volatility_30d",
        labels={"volatility_30d": "Volatility (σ)", "date": "Date"},
    )
    fig_volatility.update_layout(height=250)
    st.plotly_chart(fig_volatility, use_container_width=True)

    st.subheader("Data Table")
    display_cols = {
        "date": "Date", "close": "Close", "ma_5": "MA 5d",
        "ma_63": "MA 63d", "ma_126": "MA 126d", "ma_252": "MA 252d",
        "rsi": "RSI", "macd": "MACD", "volatility_30d": "Volatility 30d",
    }
    st.dataframe(
        df[list(display_cols.keys())]
          .rename(columns=display_cols)
          .sort_values("Date", ascending=False)
          .reset_index(drop=True),
        use_container_width=True,
    )


# ── TAB 3: FORECAST ───────────────────────────────────────────────────────────
with tab_forecast:
    st.subheader("ML Price Forecast")
    st.caption(
        f"Model: **{MODEL_INFO[model_type][0]}** · "
        f"Horizon: **{days_ahead} days** · "
        f"Trained on last 180 days of data"
    )

    dep = MODEL_INFO[model_type][1]
    if dep:
        st.info(
            f"**{MODEL_INFO[model_type][0]}** requires `{dep}`. "
            f"Install with `pip install {dep}` if not already present.",
            icon="ℹ️",
        )

    if st.button("▶  Run Forecast", type="primary"):
        try:
            result = get_forecast(ticker, str(start), str(end), days_ahead, model_type)

            m1, m2 = st.columns(2)
            m1.metric("R² Score", f"{result['r2_score']:.4f}")
            m2.metric("MAE",      f"${result['mae']:.2f}")

            forecast_df = pd.DataFrame(result["forecast"])
            forecast_df["date"] = pd.to_datetime(forecast_df["date"])

            hist_tail = df[["date", "close"]].tail(90)

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=hist_tail["date"], y=hist_tail["close"],
                name="Historical (last 90d)", line=dict(color="#1f77b4", width=2),
            ))
            fig_fc.add_trace(go.Scatter(
                x=forecast_df["date"], y=forecast_df["predicted_close"],
                name=f"Forecast — {MODEL_INFO[model_type][0]}",
                line=dict(color="#ff7f0e", dash="dash", width=2),
            ))
            fig_fc.update_layout(
                height=420, xaxis_title="Date", yaxis_title="Price (USD)",
                hovermode="x unified", legend=dict(orientation="h"),
            )
            st.plotly_chart(fig_fc, use_container_width=True)

            st.dataframe(
                forecast_df.rename(columns={
                    "date": "Date",
                    "predicted_close": f"Predicted Close (USD)",
                }),
                use_container_width=True,
            )

        except ImportError as e:
            st.error(f"Missing dependency: {e}")
        except ValueError as e:
            st.error(f"Forecast error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            raise
