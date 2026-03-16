"use client";

import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PriceRow } from "@/types/stock";

type Props = {
  data: PriceRow[];
  loading?: boolean;
};

type TooltipProps = {
  active?: boolean;
  label?: string;
  payload?: { value: number; dataKey: string; color?: string }[];
};

const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-[#2d3149] bg-[#0f1117] px-3 py-2 text-sm text-white shadow">
      <p className="font-semibold">{label}</p>
      {payload.map((item) => (
        <p key={item.dataKey} className="flex items-center gap-2 text-xs">
          <span className="rounded-full" style={{ backgroundColor: item.color, width: 8, height: 8 }} />
          <span className="capitalize">{item.dataKey?.replace("_", " ")}:</span>
          <span className="font-semibold">{item.value.toFixed(2)}</span>
        </p>
      ))}
    </div>
  );
};

export default function PriceChart({ data, loading }: Props) {
  if (loading) {
    return <div className="text-sm text-slate-400">Loading chart...</div>;
  }

  if (!data || data.length === 0) {
    return <p className="text-sm text-slate-400">No price data available.</p>;
  }

  const formatted = data.map((row) => ({
    ...row,
    ma_20: Number(row.ma_20),
    ma_50: Number(row.ma_50),
    close: Number(row.close),
  }));

  const interval = formatted.length > 10 ? Math.floor(formatted.length / 10) : 0;

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={formatted} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid stroke="#1f2433" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fill: "#cbd5e1", fontSize: 12 }} interval={interval} />
          <YAxis tick={{ fill: "#cbd5e1", fontSize: 12 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line type="monotone" dataKey="close" stroke="#ffffff" strokeWidth={2} dot={false} name="Close" />
          <Line type="monotone" dataKey="ma_20" stroke="#60a5fa" strokeWidth={2} dot={false} name="MA 20" />
          <Line type="monotone" dataKey="ma_50" stroke="#fb923c" strokeWidth={2} dot={false} name="MA 50" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
