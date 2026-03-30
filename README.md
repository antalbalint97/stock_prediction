# Stock Prediction Dashboard

Interactive stock analysis and ML forecasting dashboard. Fetches live data from yfinance — no database or API key required.

---

## Project Structure

```
stock_prediction/
├── app.py                        # Streamlit dashboard (main entry point)
├── requirements.txt              # Dashboard dependencies
├── requirements-backend.txt      # Full backend stack (FastAPI + PostgreSQL)
├── src/
│   ├── etl/
│   │   ├── metrics.py            # Technical indicators (MA, RSI, MACD, volatility)
│   │   ├── companies.py          # Company metadata via yfinance (backend ETL)
│   │   └── daily_prices.py       # OHLCV download (backend ETL)
│   ├── ml/
│   │   └── forecasting.py        # 4 ML models: linear, random_forest, lstm, prophet
│   └── database.py               # SQLAlchemy config (backend only)
├── app/
│   ├── api.py                    # FastAPI REST API
│   └── etl_pipeline.py           # ETL orchestration (FAANG → PostgreSQL)
├── legacy/
│   └── streamlit_db.py           # Old dashboard (requires PostgreSQL)
├── docker/
│   ├── docker-compose.yml        # PostgreSQL + FastAPI + Next.js
│   └── Dockerfile
└── frontend/                     # Next.js 14 dashboard (full-stack mode)
```

---

## Streamlit Dashboard (standalone)

### Setup

```bash
pip install -r requirements.txt
```

For LSTM or Prophet models, install the optional dependencies:

```bash
pip install tensorflow          # LSTM model
pip install prophet             # Prophet model
```

### Run

```bash
streamlit run app.py
```

### Features

- **Price & Moving Averages** — Close price with MA 5/63/126/252d overlays and volume bar chart
- **Technical Indicators** — RSI (14d) with overbought/oversold zones, MACD, 30-day rolling volatility
- **ML Forecast** — Train and visualise price forecasts with 4 model options:

| Model | Library | Speed |
|-------|---------|-------|
| Linear Regression | scikit-learn | Fast |
| Random Forest | scikit-learn | Fast |
| LSTM (Deep Learning) | TensorFlow | Slow |
| Prophet | Meta Prophet | Medium |

Ticker selection, date range, model type, and forecast horizon are all configurable from the sidebar.

---

## Full Backend Stack (FastAPI + PostgreSQL)

### Setup

```bash
pip install -r requirements-backend.txt
cp .env.example .env   # fill in Postgres credentials
```

`.env` variables:
```
POSTGRES_USER=dmlab_user
POSTGRES_PASSWORD=dmlab_pass
POSTGRES_DB=dmlab_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5440
```

### Run ETL (populate database)

```bash
python -m app.etl_pipeline
```

Fetches FAANG stocks (META, AAPL, AMZN, NFLX, GOOGL) and writes to:
- `companies` — metadata
- `daily_prices` — OHLCV
- `daily_prices_adjusted` — OHLCV + technical indicators

### Run API

```bash
uvicorn app.api:app --reload --port 8000
```

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tickers` | All tickers in the database |
| `GET` | `/api/prices/{ticker}?period=90` | OHLCV + indicators |
| `POST` | `/api/forecast` | Run a forecast model |
| `GET` | `/api/forecast/{ticker}?model_type=linear` | Last cached forecast |

### Docker (full stack)

```bash
docker compose -f docker/docker-compose.yml up --build
```

Services:
- `db` — PostgreSQL 15 at port 5440
- `api` — FastAPI at `http://localhost:8000`
- `frontend` — Next.js at `http://localhost:3000`
