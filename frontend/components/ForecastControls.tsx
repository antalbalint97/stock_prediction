"use client";

type Props = {
  daysAhead: number;
  modelType: string;
  loading?: boolean;
  onDaysChange: (days: number) => void;
  onModelChange: (model: string) => void;
  onRun: () => void;
};

const dayOptions = [7, 14, 30, 60];
const modelOptions: { key: string; label: string }[] = [
  { key: "linear", label: "Linear" },
  { key: "random_forest", label: "Random Forest" },
  { key: "lstm", label: "LSTM" },
  { key: "prophet", label: "Prophet" },
];

export default function ForecastControls({ daysAhead, modelType, loading, onDaysChange, onModelChange, onRun }: Props) {
  return (
    <div className="card flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <p className="text-sm text-slate-400">Days ahead</p>
        <div className="flex flex-wrap gap-2">
          {dayOptions.map((day) => (
            <button
              key={day}
              type="button"
              className={`pill-button ${daysAhead === day ? "border-[#60a5fa] text-[#60a5fa]" : "text-slate-200"}`}
              onClick={() => onDaysChange(day)}
              disabled={loading}
            >
              {day}d
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <p className="text-sm text-slate-400">Model type</p>
        <div className="flex flex-wrap gap-2">
          {modelOptions.map((option) => (
            <button
              key={option.key}
              type="button"
              className={`pill-button ${
                modelType === option.key ? "border-[#a78bfa] text-[#a78bfa]" : "text-slate-200"
              }`}
              onClick={() => onModelChange(option.key)}
              disabled={loading}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onRun}
          disabled={loading}
          className="rounded-lg bg-gradient-to-r from-[#60a5fa] to-[#a78bfa] px-5 py-3 text-sm font-semibold text-slate-900 shadow transition hover:opacity-90 disabled:opacity-60"
        >
          {loading ? "Running..." : "Run"}
        </button>
      </div>
    </div>
  );
}
