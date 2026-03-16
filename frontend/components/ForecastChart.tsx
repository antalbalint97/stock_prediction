"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ForecastPoint, PriceRow } from "@/types/stock";

type Props = {
  history: PriceRow[];
  forecast: ForecastPoint[];
  loading?: boolean;
};

export default function ForecastChart({ history, forecast, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-slate-400">Running forecast...</p>;
  }

  if (!history || history.length === 0) {
    return <p className="text-sm text-slate-400">No history available.</p>;
  }

  const historyMap = new Map(history.map((row) => [row.date, Number(row.close)]));
  const forecastMap = new Map(forecast.map((row) => [row.date, Number(row.predicted_close)]));
  const allDates = Array.from(new Set([...historyMap.keys(), ...forecastMap.keys()])).sort();
  const combined = allDates.map((date) => ({
    date,
    close: historyMap.get(date),
    forecast: forecastMap.get(date),
  }));

  const todayLabel = new Date().toISOString().split("T")[0];

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChartWithTooltip data={combined} todayLabel={todayLabel} />
      </ResponsiveContainer>
    </div>
  );
}

type LineChartProps = {
  data: { date: string; close?: number; forecast?: number }[];
  todayLabel: string;
};

function LineChartWithTooltip({ data, todayLabel }: LineChartProps) {
  return (
    <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
      <CartesianGrid stroke="#1f2433" strokeDasharray="3 3" />
      <XAxis dataKey="date" tick={{ fill: "#cbd5e1", fontSize: 12 }} />
      <YAxis tick={{ fill: "#cbd5e1", fontSize: 12 }} />
      <Tooltip />
      <Legend />
      <ReferenceLine x={todayLabel} stroke="#a78bfa" strokeDasharray="5 5" label={{ value: "Today", fill: "#a78bfa" }} />
      <Line type="monotone" dataKey="close" stroke="#ffffff" strokeWidth={2} dot={false} name="Historical Close" />
      <Line
        type="monotone"
        dataKey="forecast"
        stroke="#a78bfa"
        strokeWidth={2}
        strokeDasharray="5 5"
        dot={false}
        name="Forecast"
      />
    </LineChart>
  );
}
