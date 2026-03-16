from typing import Dict, List, Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text

from src.database import get_engine
from src.ml.forecasting import train_forecast

engine = get_engine()

app = FastAPI(title="Stock Forecasting API")

origins = ["http://localhost:3000", "http://frontend:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

forecast_cache: Dict[str, dict] = {}


class ForecastRequest(BaseModel):
    ticker: str
    days_ahead: int = Field(30, ge=1, le=365)
    model_type: Literal["linear", "random_forest", "lstm", "prophet"] = "linear"


def _get_price_table() -> str:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "daily_prices_adjusted" in table_names:
        return "daily_prices_adjusted"
    if "daily_prices" in table_names:
        return "daily_prices"
    raise HTTPException(status_code=404, detail="Price tables not found")


def _load_prices(ticker: str) -> pd.DataFrame:
    table = _get_price_table()
    with engine.connect() as conn:
        df = pd.read_sql_query(
            text(f"SELECT * FROM {table} WHERE ticker = :ticker ORDER BY date ASC"),
            conn,
            params={"ticker": ticker},
            parse_dates=["date"],
        )
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No price data for ticker {ticker}")
    # Drop internal id column if present
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    return df


def _ensure_indicators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date")

    if "ma_20" not in data.columns:
        data["ma_20"] = data["close"].rolling(window=20, min_periods=1).mean()

    if "ma_50" not in data.columns:
        data["ma_50"] = data["close"].rolling(window=50, min_periods=1).mean()

    if "rsi_14" not in data.columns:
        if "rsi" in data.columns:
            data["rsi_14"] = data["rsi"]
        else:
            delta = data["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data["rsi_14"] = 100 - (100 / (1 + rs))
    data["rsi_14"] = data["rsi_14"].fillna(method="bfill").fillna(method="ffill")

    if "macd" not in data.columns:
        ema_12 = data["close"].ewm(span=12, adjust=False).mean()
        ema_26 = data["close"].ewm(span=26, adjust=False).mean()
        data["macd"] = ema_12 - ema_26
    data["macd"] = data["macd"].fillna(0)

    return data


@app.get("/api/tickers")
def get_tickers() -> List[Dict[str, str]]:
    inspector = inspect(engine)
    if "companies" not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Companies table not found")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT ticker, longName FROM companies")).fetchall()
    response = []
    for row in rows:
        mapping = row._mapping
        response.append(
            {"ticker": mapping.get("ticker"), "name": mapping.get("longName") or mapping.get("ticker")}
        )
    return response


@app.get("/api/prices/{ticker}")
def get_prices(ticker: str, period: int = 90) -> Dict[str, object]:
    period = max(period, 1)
    df = _ensure_indicators(_load_prices(ticker))
    df = df.tail(period)
    df = df.fillna(method="ffill")
    records = df.to_dict(orient="records")
    response = [
        {
            "date": r["date"].strftime("%Y-%m-%d") if not isinstance(r["date"], str) else r["date"],
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": None
            if r.get("volume") is None or pd.isna(r.get("volume"))
            else int(r.get("volume")),
            "ma_20": float(r["ma_20"]),
            "ma_50": float(r["ma_50"]),
            "rsi_14": float(r["rsi_14"]),
            "macd": float(r["macd"]),
        }
        for r in records
    ]
    return {"ticker": ticker, "data": response}


@app.post("/api/forecast")
def run_forecast(request: ForecastRequest) -> Dict[str, object]:
    cache_key = f"{request.ticker}_{request.model_type}"
    try:
        result = train_forecast(request.ticker, request.days_ahead, request.model_type)
    except ImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    forecast_cache[cache_key] = result
    return result


@app.get("/api/forecast/{ticker}")
def get_forecast(ticker: str, model_type: str = "linear") -> Dict[str, object]:
    cache_key = f"{ticker}_{model_type}"
    if cache_key not in forecast_cache:
        raise HTTPException(status_code=404, detail="No cached forecast available")
    return forecast_cache[cache_key]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
