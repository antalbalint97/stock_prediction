export interface Ticker {
  ticker: string;
  name: string;
}

export interface PriceRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma_20: number;
  ma_50: number;
  rsi_14: number;
  macd: number;
}

export interface ForecastPoint {
  date: string;
  predicted_close: number;
}

export interface ForecastResult {
  ticker: string;
  model_type: string;
  forecast: ForecastPoint[];
  r2_score: number;
  mae: number;
}

export interface PricesResponse {
  ticker: string;
  data: PriceRow[];
}
