"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface EquityPoint {
  timestamp: string;
  equity: number;
}

export function EquityCurve({ data }: { data: EquityPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No equity data yet. Run a backtest or start paper trading.
      </div>
    );
  }

  // Downsample if too many points
  const maxPoints = 200;
  const step = Math.max(1, Math.floor(data.length / maxPoints));
  const sampled = data.filter((_, i) => i % step === 0);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={sampled}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={(val: string) => {
            const d = new Date(val);
            return `${d.getMonth() + 1}/${d.getDate()}`;
          }}
          stroke="#888"
          fontSize={12}
        />
        <YAxis
          stroke="#888"
          fontSize={12}
          tickFormatter={(val: number) => `$${val.toFixed(0)}`}
        />
        <Tooltip
          contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333" }}
          formatter={(value) => [`$${Number(value).toFixed(2)}`, "Equity"]}
          labelFormatter={(label) => new Date(String(label)).toLocaleDateString()}
        />
        <Line
          type="monotone"
          dataKey="equity"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
