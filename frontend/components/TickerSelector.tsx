"use client";

import { useEffect, useMemo, useState } from "react";
import { Ticker } from "@/types/stock";

type Props = {
  tickers: Ticker[];
  presets: string[];
  selected?: string;
  loading?: boolean;
  onSelect: (ticker: string) => void;
};

export default function TickerSelector({ tickers, presets, selected, loading, onSelect }: Props) {
  const [input, setInput] = useState<string>(selected ?? "");

  useEffect(() => {
    // Synchronize the input when the parent selection changes
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInput(selected ?? "");
  }, [selected]);

  const suggestions = useMemo(() => tickers.map((t) => t.ticker.toUpperCase()), [tickers]);

  const handleSubmit = () => {
    const value = input.trim().toUpperCase();
    if (value) {
      onSelect(value);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={loading ? "Loading tickers..." : "Enter ticker (e.g., AAPL)"}
          className="w-full rounded-lg border border-[#2d3149] bg-[#121420] px-4 py-3 text-sm text-white outline-none transition focus:border-[#60a5fa]"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSubmit();
            }
          }}
          list="ticker-suggestions"
        />
        <datalist id="ticker-suggestions">
          {suggestions.map((sym) => (
            <option key={sym} value={sym} />
          ))}
        </datalist>
        <button
          type="button"
          onClick={handleSubmit}
          className="rounded-lg bg-[#60a5fa] px-4 py-3 text-sm font-semibold text-slate-900 shadow transition hover:opacity-90"
          disabled={loading}
        >
          {loading ? "Loading..." : "Add"}
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {presets.map((sym) => (
          <button
            key={sym}
            type="button"
            className={`pill-button ${selected === sym ? "border-[#60a5fa] text-[#60a5fa]" : "text-slate-200"}`}
            onClick={() => {
              setInput(sym);
              onSelect(sym);
            }}
          >
            {sym}
          </button>
        ))}
      </div>
    </div>
  );
}
