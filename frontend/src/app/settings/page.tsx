"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export default function SettingsPage() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
  });

  if (isLoading) {
    return <div className="animate-pulse text-muted-foreground">Loading settings...</div>;
  }

  if (!settings) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Bot Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Trading Mode</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Badge
                className={
                  settings.paper_trading ? "bg-yellow-500" : "bg-green-500"
                }
              >
                {settings.paper_trading ? "PAPER" : "LIVE"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {settings.paper_trading
                  ? "Trading with simulated money"
                  : "Trading with real money"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Position Size</span>
              <span className="font-medium">
                {(settings.max_position_pct * 100).toFixed(0)}%
              </span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Open Positions</span>
              <span className="font-medium">{settings.max_open_positions}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Daily Loss</span>
              <span className="font-medium text-red-400">
                {(settings.max_daily_loss_pct * 100).toFixed(0)}%
              </span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Drawdown</span>
              <span className="font-medium text-red-400">
                {(settings.max_drawdown_pct * 100).toFixed(0)}%
              </span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Min Signal Confidence</span>
              <span className="font-medium">
                {(settings.min_signal_confidence * 100).toFixed(0)}%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Watchlist ({settings.watchlist.length} tickers)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {settings.watchlist.map((ticker) => (
                <Badge key={ticker} variant="outline" className="text-sm">
                  {ticker}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
