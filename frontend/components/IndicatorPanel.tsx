"use client";

import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PriceRow } from "@/types/stock";

type Props = {
  data: PriceRow[];
  loading?: boolean;
};

export default function IndicatorPanel({ data, loading }: Props) {
  if (loading) {
    return <div className="text-sm text-slate-400">Loading indicators...</div>;
  }

  if (!data || data.length === 0) {
    return <p className="text-sm text-slate-400">No indicator data available.</p>;
  }

  const enriched = data.map((row) => ({
    ...row,
    macdPositive: row.macd > 0 ? row.macd : 0,
    macdNegative: row.macd < 0 ? row.macd : 0,
  }));

  return (
    <div className="flex flex-col gap-6">
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={enriched} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1f2433" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: "#cbd5e1", fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: "#cbd5e1", fontSize: 11 }} domain={[0, 100]} />
            <Tooltip />
            <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" />
            <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" />
            <Area
              type="monotone"
              dataKey="rsi_14"
              stroke="#60a5fa"
              fill="#60a5fa33"
              name="RSI 14"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={enriched} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1f2433" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: "#cbd5e1", fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: "#cbd5e1", fontSize: 11 }} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="macdPositive"
              stroke="#22c55e"
              fill="#22c55e33"
              name="MACD +"
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="macdNegative"
              stroke="#ef4444"
              fill="#ef444433"
              name="MACD -"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
