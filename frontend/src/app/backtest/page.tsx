"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type BacktestRequest, type BacktestResponse } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EquityCurve } from "@/components/charts/EquityCurve";
import { Badge } from "@/components/ui/badge";

export default function BacktestPage() {
  const [params, setParams] = useState<BacktestRequest>({
    ticker: "SPY",
    initial_capital: 100,
    days: 730,
    stop_loss_pct: 0.03,
    take_profit_pct: 0.06,
    max_position_pct: 0.2,
    max_positions: 5,
  });

  const mutation = useMutation({
    mutationFn: api.runBacktest,
  });

  const result: BacktestResponse | undefined = mutation.data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Backtesting</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Config Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">Ticker</label>
              <input
                className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background"
                value={params.ticker}
                onChange={(e) =>
                  setParams({ ...params, ticker: e.target.value.toUpperCase() })
                }
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">
                Initial Capital ($)
              </label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background"
                value={params.initial_capital}
                onChange={(e) =>
                  setParams({ ...params, initial_capital: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">
                History (days)
              </label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background"
                value={params.days}
                onChange={(e) =>
                  setParams({ ...params, days: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">
                Stop Loss %
              </label>
              <input
                type="number"
                step="0.01"
                className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background"
                value={params.stop_loss_pct}
                onChange={(e) =>
                  setParams({ ...params, stop_loss_pct: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">
                Take Profit %
              </label>
              <input
                type="number"
                step="0.01"
                className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background"
                value={params.take_profit_pct}
                onChange={(e) =>
                  setParams({ ...params, take_profit_pct: Number(e.target.value) })
                }
              />
            </div>

            <Button
              className="w-full"
              onClick={() => mutation.mutate(params)}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "Running..." : "Run Backtest"}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-3 space-y-6">
          {mutation.isPending && (
            <div className="text-center py-16 text-muted-foreground animate-pulse">
              Running backtest on {params.ticker} ({params.days} days)...
            </div>
          )}

          {result && (
            <>
              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Total Return</div>
                    <div
                      className={`text-2xl font-bold ${
                        result.metrics.total_return_pct >= 0
                          ? "text-green-500"
                          : "text-red-500"
                      }`}
                    >
                      {result.metrics.total_return_pct.toFixed(2)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Sharpe Ratio</div>
                    <div className="text-2xl font-bold">
                      {result.metrics.sharpe_ratio.toFixed(2)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Max Drawdown</div>
                    <div className="text-2xl font-bold text-red-500">
                      -{result.metrics.max_drawdown_pct.toFixed(2)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Win Rate</div>
                    <div className="text-2xl font-bold">
                      {result.metrics.win_rate.toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Total Trades</div>
                    <div className="text-2xl font-bold">
                      {result.metrics.total_trades}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Profit Factor</div>
                    <div className="text-2xl font-bold">
                      {result.metrics.profit_factor.toFixed(2)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Final Equity</div>
                    <div className="text-2xl font-bold">
                      ${result.metrics.final_equity.toFixed(2)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-muted-foreground">Avg Win / Loss</div>
                    <div className="text-sm font-medium">
                      <span className="text-green-500">
                        +{result.metrics.avg_win_pct.toFixed(1)}%
                      </span>{" "}
                      /{" "}
                      <span className="text-red-500">
                        {result.metrics.avg_loss_pct.toFixed(1)}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Equity Curve */}
              <Card>
                <CardHeader>
                  <CardTitle>Equity Curve</CardTitle>
                </CardHeader>
                <CardContent>
                  <EquityCurve data={result.equity_curve} />
                </CardContent>
              </Card>

              {/* Trade List */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    Trades ({result.trades.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-muted-foreground">
                          <th className="text-left pb-2">Entry</th>
                          <th className="text-left pb-2">Exit</th>
                          <th className="text-right pb-2">Entry $</th>
                          <th className="text-right pb-2">Exit $</th>
                          <th className="text-right pb-2">P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.trades.map((t, i) => (
                          <tr key={i} className="border-t border-border">
                            <td className="py-1">{t.entry_date.slice(0, 10)}</td>
                            <td className="py-1">
                              {t.exit_date ? t.exit_date.slice(0, 10) : "-"}
                            </td>
                            <td className="text-right">${t.entry_price.toFixed(2)}</td>
                            <td className="text-right">
                              {t.exit_price ? `$${t.exit_price.toFixed(2)}` : "-"}
                            </td>
                            <td
                              className={`text-right font-medium ${
                                t.pnl >= 0 ? "text-green-500" : "text-red-500"
                              }`}
                            >
                              {t.pnl >= 0 ? "+" : ""}
                              {t.pnl_pct.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {!result && !mutation.isPending && (
            <div className="text-center py-16 text-muted-foreground">
              Configure parameters and click &quot;Run Backtest&quot; to test a strategy
              on historical data.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
