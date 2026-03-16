"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import IndicatorPanel from "@/components/IndicatorPanel";
import PriceChart from "@/components/PriceChart";
import TickerSelector from "@/components/TickerSelector";
import { getPrices, getTickers } from "@/lib/api";
import { PriceRow, Ticker } from "@/types/stock";

const PRESETS = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"];

export default function Home() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string>("");
  const [prices, setPrices] = useState<PriceRow[]>([]);
  const [loadingTickers, setLoadingTickers] = useState<boolean>(true);
  const [loadingPrices, setLoadingPrices] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTickers = async () => {
      try {
        const data = await getTickers();
        setTickers(data);
        if (data.length > 0) {
          setSelectedTicker(data[0].ticker);
          await fetchPrices(data[0].ticker);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load tickers";
        setError(message);
      } finally {
        setLoadingTickers(false);
      }
    };
    loadTickers();
  }, []);

  const fetchPrices = async (ticker: string) => {
    setLoadingPrices(true);
    setError(null);
    try {
      const response = await getPrices(ticker, 90);
      setPrices(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load prices";
      setError(message);
      setPrices([]);
    } finally {
      setLoadingPrices(false);
    }
  };

  const handleSelect = (ticker: string) => {
    setSelectedTicker(ticker);
    fetchPrices(ticker);
  };

  return (
    <main className="min-h-screen px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-2">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Stock Forecast</p>
          <h1 className="text-3xl font-semibold text-white">Visualize market data and indicators</h1>
          <p className="text-slate-400">
            Select a ticker to view price action, moving averages, RSI, and MACD. Continue to the forecast page to run
            machine learning models.
          </p>
        </header>

        <div className="card">
          <TickerSelector
            tickers={tickers}
            presets={PRESETS}
            loading={loadingTickers}
            onSelect={handleSelect}
            selected={selectedTicker}
          />
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="card">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Price &amp; Averages</h2>
              {loadingPrices && <span className="text-xs text-slate-400">Loading…</span>}
            </div>
            <PriceChart data={prices} loading={loadingPrices} />
          </div>

          <div className="card">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Momentum Indicators</h2>
              {loadingPrices && <span className="text-xs text-slate-400">Loading…</span>}
            </div>
            <IndicatorPanel data={prices} loading={loadingPrices} />
          </div>
        </div>

        <div className="flex justify-end">
          <Link
            href={selectedTicker ? `/forecast/${selectedTicker}` : "#"}
            className={`rounded-lg bg-gradient-to-r from-[#60a5fa] to-[#a78bfa] px-5 py-3 text-sm font-semibold text-slate-900 shadow transition hover:opacity-90 ${
              selectedTicker ? "" : "pointer-events-none opacity-60"
            }`}
            aria-disabled={!selectedTicker}
          >
            Run Forecast →
          </Link>
        </div>
      </div>
    </main>
  );
}
