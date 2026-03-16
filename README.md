# Financial Data ETL, API & Frontend

This project provides an end-to-end ETL pipeline, FastAPI backend, and a Next.js 14 dashboard for exploring and forecasting stock prices.

## Architecture

```
yfinance → ETL → PostgreSQL → FastAPI → Next.js
```

## Quick start (Docker)

Ensure `.env` is populated for PostgreSQL, then run:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Services:
- `db` – PostgreSQL 15
- `api` – FastAPI at `http://localhost:8000`
- `frontend` – Next.js at `http://localhost:3000`

## API Endpoints

- `GET /api/tickers` → `[{ "ticker": "AAPL", "name": "Apple Inc." }, ...]`
- `GET /api/prices/{ticker}?period=90` → OHLCV + indicators (`ma_20`, `ma_50`, `rsi_14`, `macd`)
- `POST /api/forecast`  
  Body: `{ "ticker": "AAPL", "days_ahead": 30, "model_type": "linear" | "random_forest" | "lstm" | "prophet" }`  
  Response: `{ "forecast": [{ "date": "...", "predicted_close": 123.4 }], "r2_score": 0.9, "mae": 1.2 }`
- `GET /api/forecast/{ticker}?model_type=linear` → Last cached forecast

## Local development

### Backend (FastAPI)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### ETL
```bash
python -m app.etl_pipeline
```
Populates `companies`, `daily_prices`, and `daily_prices_adjusted` tables using yfinance.
