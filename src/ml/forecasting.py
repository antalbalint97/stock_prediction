from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import inspect, text

from src.database import get_engine


def _get_price_table(engine) -> str:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "daily_prices_adjusted" in tables:
        return "daily_prices_adjusted"
    if "daily_prices" in tables:
        return "daily_prices"
    raise ValueError("Price tables not found")


def _load_dataframe(engine, ticker: str) -> pd.DataFrame:
    table = _get_price_table(engine)
    with engine.connect() as conn:
        df = pd.read_sql_query(
            text(f"SELECT * FROM {table} WHERE ticker = :ticker ORDER BY date ASC"),
            conn,
            params={"ticker": ticker},
            parse_dates=["date"],
        )
    if df.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    return df


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
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


def _prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    df = _add_indicators(df)
    df["target_close"] = df["close"].shift(-1)
    df = df.dropna(subset=["ma_20", "ma_50", "rsi_14", "macd", "target_close"])
    df = df.set_index("date")
    min_date = df.index.max() - pd.Timedelta(days=180)
    df = df[df.index >= min_date]
    df["day_of_week"] = df.index.dayofweek
    df["day_of_month"] = df.index.day
    df["month"] = df.index.month
    features = ["ma_20", "ma_50", "rsi_14", "macd", "day_of_week", "day_of_month", "month"]
    X = df[features].copy()
    y = df["target_close"].copy()
    return X, y


def _compute_future_features(last_row: pd.Series, days_ahead: int) -> pd.DataFrame:
    future_dates = [last_row.name + timedelta(days=i) for i in range(1, days_ahead + 1)]
    future_rows = []
    for d in future_dates:
        future_rows.append(
            {
                "ma_20": last_row["ma_20"],
                "ma_50": last_row["ma_50"],
                "rsi_14": last_row["rsi_14"],
                "macd": last_row["macd"],
                "day_of_week": d.dayofweek,
                "day_of_month": d.day,
                "month": d.month,
                "date": d,
            }
        )
    return pd.DataFrame(future_rows)


def _train_sklearn_model(
    model, X: pd.DataFrame, y: pd.Series, days_ahead: int
) -> Tuple[Dict[str, float], List[Dict[str, float]]]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    try:
        r2 = float(r2_score(y_test, preds)) if len(y_test) > 0 else 0.0
    except ValueError:
        r2 = 0.0
    mae = float(mean_absolute_error(y_test, preds)) if len(y_test) > 0 else 0.0

    last_row = X.iloc[-1]
    future_df = _compute_future_features(last_row, days_ahead)
    future_preds = model.predict(future_df.drop(columns=["date"]))
    forecast = [
        {"date": row["date"].strftime("%Y-%m-%d"), "predicted_close": float(pred)}
        for row, pred in zip(future_df.to_dict(orient="records"), future_preds)
    ]
    return {"r2_score": r2, "mae": mae}, forecast


def _train_lstm(X: pd.DataFrame, y: pd.Series, days_ahead: int):
    try:
        from tensorflow.keras.layers import Dense, Dropout, LSTM
        from tensorflow.keras.models import Sequential
    except ImportError as exc:
        raise ImportError("TensorFlow is required for LSTM model. Please install tensorflow.") from exc

    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(X)
    seq_len = 60
    if len(scaled_features) <= seq_len:
        raise ValueError("Not enough data to train LSTM model (need more than 60 observations).")

    def create_sequences(features_arr, target_arr, seq_length):
        X_seq, y_seq = [], []
        for i in range(seq_length, len(features_arr)):
            X_seq.append(features_arr[i - seq_length : i])
            y_seq.append(target_arr[i - 1])
        return np.array(X_seq), np.array(y_seq)

    X_seq, y_seq = create_sequences(scaled_features, y.values, seq_len)
    split_index = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split_index], X_seq[split_index:]
    y_train, y_test = y_seq[:split_index], y_seq[split_index:]

    model = Sequential()
    model.add(LSTM(64, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(32))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    model.fit(X_train, y_train, epochs=20, batch_size=32, verbose=0)

    if len(X_test) > 0:
        test_preds = model.predict(X_test, verbose=0).flatten()
        try:
            r2 = float(r2_score(y_test, test_preds))
        except ValueError:
            r2 = 0.0
        mae = float(mean_absolute_error(y_test, test_preds))
    else:
        r2 = 0.0
        mae = 0.0

    last_sequence = X_seq[-1]
    future_forecast = []
    current_seq = last_sequence
    for _ in range(days_ahead):
        next_pred = model.predict(current_seq[np.newaxis, ...], verbose=0).flatten()[0]
        future_forecast.append(next_pred)
        # Append last known feature vector to maintain shape
        current_seq = np.vstack([current_seq[1:], current_seq[-1]])

    last_date = X.index[-1]
    forecast = []
    for idx, pred in enumerate(future_forecast, start=1):
        forecast.append({"date": (last_date + timedelta(days=idx)).strftime("%Y-%m-%d"), "predicted_close": float(pred)})
    return {"r2_score": r2, "mae": mae}, forecast


def _train_prophet(df: pd.DataFrame, days_ahead: int):
    try:
        from prophet import Prophet
    except ImportError as exc:
        raise ImportError("Prophet is required for the 'prophet' model. Please install prophet.") from exc

    data = df.copy().reset_index()
    prophet_df = data.rename(columns={"date": "ds", "close": "y"})
    for reg in ["ma_20", "ma_50", "rsi_14"]:
        prophet_df[reg] = prophet_df[reg].ffill()

    train_df, test_df = train_test_split(prophet_df, test_size=0.2, shuffle=False)
    model = Prophet()
    model.add_regressor("ma_20")
    model.add_regressor("ma_50")
    model.add_regressor("rsi_14")
    model.fit(train_df)

    test_forecast = model.predict(test_df)
    if len(test_df) > 0:
        try:
            r2 = float(r2_score(test_df["y"], test_forecast["yhat"]))
        except ValueError:
            r2 = 0.0
    else:
        r2 = 0.0
    mae = float(mean_absolute_error(test_df["y"], test_forecast["yhat"])) if len(test_df) > 0 else 0.0

    future = model.make_future_dataframe(periods=days_ahead)
    future = future.merge(prophet_df[["ds", "ma_20", "ma_50", "rsi_14"]], on="ds", how="left")
    future[["ma_20", "ma_50", "rsi_14"]] = future[["ma_20", "ma_50", "rsi_14"]].ffill()
    future_forecast = model.predict(future)
    forecast_slice = future_forecast.tail(days_ahead)
    forecast = [
        {"date": row["ds"].strftime("%Y-%m-%d"), "predicted_close": float(row["yhat"])}
        for _, row in forecast_slice.iterrows()
    ]
    return {"r2_score": r2, "mae": mae}, forecast


def train_forecast(ticker: str, days_ahead: int = 30, model_type: str = "linear") -> dict:
    """
    Train a forecasting model for the given ticker and return forecast data and metrics.
    """
    engine = get_engine()
    raw_df = _load_dataframe(engine, ticker)
    X, y = _prepare_features(raw_df)
    if len(X) < 30:
        raise ValueError("Not enough historical data to train a forecasting model.")

    metrics: Dict[str, float]
    forecast: List[Dict[str, float]]

    if model_type == "linear":
        model = LinearRegression()
        metrics, forecast = _train_sklearn_model(model, X, y, days_ahead)
    elif model_type == "random_forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        metrics, forecast = _train_sklearn_model(model, X, y, days_ahead)
    elif model_type == "lstm":
        metrics, forecast = _train_lstm(X, y, days_ahead)
    elif model_type == "prophet":
        df_with_indicators = _add_indicators(raw_df).set_index("date")
        metrics, forecast = _train_prophet(df_with_indicators, days_ahead)
    else:
        raise ValueError("Unsupported model_type. Choose from linear, random_forest, lstm, prophet.")

    return {
        "ticker": ticker,
        "model_type": model_type,
        "forecast": forecast,
        "r2_score": metrics.get("r2_score", 0.0),
        "mae": metrics.get("mae", 0.0),
    }
