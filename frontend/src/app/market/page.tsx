"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Mover, type ChartBar } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

function PriceChange({ mover }: { mover: Mover }) {
  const isUp = mover.change_pct >= 0;
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-3">
        {isUp ? (
          <TrendingUp className="h-5 w-5 text-green-500" />
        ) : (
          <TrendingDown className="h-5 w-5 text-red-500" />
        )}
        <div>
          <span className="font-bold text-lg">{mover.ticker}</span>
          <div className="text-sm text-muted-foreground">
            prev: ${mover.prev_close.toFixed(2)}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="font-bold text-lg">${mover.price.toFixed(2)}</div>
        <Badge className={isUp ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}>
          {isUp ? "+" : ""}
          {mover.change_pct.toFixed(2)}%
        </Badge>
      </div>
    </div>
  );
}

export default function MarketPage() {
  const [selectedTicker, setSelectedTicker] = useState<string>("SPY");
  const [chartDays, setChartDays] = useState(90);

  const { data: movers, isLoading: moversLoading, refetch: refetchMovers } = useQuery({
    queryKey: ["movers"],
    queryFn: api.getMovers,
    refetchInterval: 60_000, // refresh every 60s
  });

  const { data: chart, isLoading: chartLoading } = useQuery({
    queryKey: ["chart", selectedTicker, chartDays],
    queryFn: () => api.getChart(selectedTicker, chartDays),
    enabled: !!selectedTicker,
  });

  const chartData = chart?.bars.map((bar: ChartBar) => ({
    date: bar.time.slice(0, 10),
    price: bar.close,
    volume: bar.volume,
    high: bar.high,
    low: bar.low,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-6 w-6 text-blue-500" />
          <h1 className="text-2xl font-bold">Live Market</h1>
        </div>
        <div className="flex items-center gap-2">
          {movers && (
            <span className="text-xs text-muted-foreground">
              Updated: {new Date(movers.updated_at).toLocaleTimeString()}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={() => refetchMovers()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Price Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{selectedTicker} Price Chart</CardTitle>
            <div className="flex gap-2">
              {[30, 90, 180, 365].map((d) => (
                <Button
                  key={d}
                  variant={chartDays === d ? "default" : "outline"}
                  size="sm"
                  onClick={() => setChartDays(d)}
                >
                  {d}d
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {chartLoading ? (
            <div className="h-[350px] flex items-center justify-center text-muted-foreground animate-pulse">
              Loading chart...
            </div>
          ) : chartData.length > 0 ? (
            <div className="space-y-4">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    stroke="#888"
                    fontSize={11}
                    tickFormatter={(val: string) => val.slice(5)}
                  />
                  <YAxis stroke="#888" fontSize={11} domain={["auto", "auto"]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333", borderRadius: "8px" }}
                    formatter={(value) => [`$${Number(value).toFixed(2)}`, "Price"]}
                  />
                  <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
              <ResponsiveContainer width="100%" height={80}>
                <BarChart data={chartData}>
                  <Bar dataKey="volume" fill="#3b82f680" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[350px] flex items-center justify-center text-muted-foreground">
              No chart data. Add your Alpaca API key to .env to see real data.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Movers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Gainers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Top Gainers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {moversLoading ? (
              <div className="animate-pulse text-muted-foreground">Loading...</div>
            ) : movers && movers.gainers.length > 0 ? (
              <div className="space-y-2">
                {movers.gainers.map((m) => (
                  <button
                    key={m.ticker}
                    className="w-full text-left"
                    onClick={() => setSelectedTicker(m.ticker)}
                  >
                    <PriceChange mover={m} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                No data yet. Add Alpaca API key to see live prices.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Losers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-red-500" />
              Top Losers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {moversLoading ? (
              <div className="animate-pulse text-muted-foreground">Loading...</div>
            ) : movers && movers.losers.length > 0 ? (
              <div className="space-y-2">
                {movers.losers.map((m) => (
                  <button
                    key={m.ticker}
                    className="w-full text-left"
                    onClick={() => setSelectedTicker(m.ticker)}
                  >
                    <PriceChange mover={m} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                No data yet. Add Alpaca API key to see live prices.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* All Stocks Grid */}
      <Card>
        <CardHeader>
          <CardTitle>All Watchlist ({movers?.all.length || 0} stocks)</CardTitle>
        </CardHeader>
        <CardContent>
          {movers && movers.all.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {movers.all.map((m) => (
                <button
                  key={m.ticker}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    selectedTicker === m.ticker
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-border hover:bg-accent/50"
                  }`}
                  onClick={() => setSelectedTicker(m.ticker)}
                >
                  <div className="font-bold">{m.ticker}</div>
                  <div className="text-sm">${m.price.toFixed(2)}</div>
                  <div
                    className={`text-xs font-medium ${
                      m.change_pct >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {m.change_pct >= 0 ? "+" : ""}
                    {m.change_pct.toFixed(2)}%
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Add your Alpaca API key to .env to see real market data.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
