"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ForecastChart from "@/components/ForecastChart";
import ForecastControls from "@/components/ForecastControls";
import { getForecast, getPrices, runForecast } from "@/lib/api";
import { ForecastResult, PriceRow } from "@/types/stock";

export default function ForecastPage() {
  const params = useParams<{ ticker: string }>();
  const rawTicker = decodeURIComponent(params.ticker);
  const ticker = rawTicker.toUpperCase();
  const tickerIsValid = /^[A-Z0-9._-]{1,10}$/.test(ticker);

  const [daysAhead, setDaysAhead] = useState<number>(30);
  const [modelType, setModelType] = useState<string>("linear");
  const [history, setHistory] = useState<PriceRow[]>([]);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [loadingPrices, setLoadingPrices] = useState<boolean>(true);
  const [loadingForecast, setLoadingForecast] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!tickerIsValid) {
        setError("Invalid ticker symbol.");
        setLoadingPrices(false);
        return;
      }
      try {
        const prices = await getPrices(ticker, 180);
        setHistory(prices.data);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load price history";
        setError(message);
      } finally {
        setLoadingPrices(false);
      }
    };
    fetchData();
  }, [ticker, tickerIsValid]);

  useEffect(() => {
    const fetchCachedForecast = async () => {
      if (!tickerIsValid) {
        return;
      }
      try {
        const cached = await getForecast(ticker, modelType);
        setForecast(cached);
      } catch {
        // No cached forecast; ignore
      }
    };
    fetchCachedForecast();
  }, [ticker, modelType, tickerIsValid]);

  const handleRun = async () => {
    if (!tickerIsValid) {
      setError("Invalid ticker symbol.");
      return;
    }
    setLoadingForecast(true);
    setError(null);
    try {
      const result = await runForecast(ticker, daysAhead, modelType);
      setForecast(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Forecast failed";
      setError(message);
    } finally {
      setLoadingForecast(false);
    }
  };

  return (
    <main className="min-h-screen px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Forecast</p>
            <h1 className="text-3xl font-semibold text-white">{ticker}</h1>
          </div>
          <Link href="/" className="text-sm text-[#60a5fa] underline underline-offset-4">
            ← Back
          </Link>
        </header>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <ForecastControls
          daysAhead={daysAhead}
          modelType={modelType}
          loading={loadingForecast}
          onDaysChange={setDaysAhead}
          onModelChange={setModelType}
          onRun={handleRun}
        />

        <div className="card">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Forecast</h2>
            {(loadingPrices || loadingForecast) && <span className="text-xs text-slate-400">Loading…</span>}
          </div>
          <ForecastChart history={history} forecast={forecast?.forecast ?? []} loading={loadingForecast || loadingPrices} />
          {forecast && (
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-[#2d3149] bg-[#121420] px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Model</p>
                <p className="text-lg font-semibold text-white">{forecast.model_type}</p>
              </div>
              <div className="rounded-lg border border-[#2d3149] bg-[#121420] px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">R²</p>
                <p className="text-lg font-semibold text-white">{forecast.r2_score.toFixed(3)}</p>
              </div>
              <div className="rounded-lg border border-[#2d3149] bg-[#121420] px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">MAE</p>
                <p className="text-lg font-semibold text-white">{forecast.mae.toFixed(3)}</p>
              </div>
            </div>
          )}
          {!forecast && !loadingForecast && (
            <p className="mt-3 text-sm text-slate-400">Run a forecast to see predictions.</p>
          )}
        </div>
      </div>
    </main>
  );
}
