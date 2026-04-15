"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { StatsCards } from "@/components/portfolio/StatsCards";
import { PositionsTable } from "@/components/portfolio/PositionsTable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useWebSocket } from "@/lib/hooks/useWebSocket";

export default function Dashboard() {
  const { connected } = useWebSocket();

  const { data: portfolio, isLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: api.getPortfolio,
  });

  const { data: signals } = useQuery({
    queryKey: ["signals"],
    queryFn: () => api.getSignals(10),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">
          Loading dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-xs text-muted-foreground">
            {connected ? "Live" : "Disconnected"}
          </span>
        </div>
      </div>

      {portfolio && <StatsCards portfolio={portfolio} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Open Positions</CardTitle>
          </CardHeader>
          <CardContent>
            {portfolio && <PositionsTable positions={portfolio.positions} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Signals</CardTitle>
          </CardHeader>
          <CardContent>
            {signals && signals.length > 0 ? (
              <div className="space-y-3">
                {signals.map((signal) => (
                  <div
                    key={signal.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-accent/50"
                  >
                    <div>
                      <span className="font-bold">{signal.ticker}</span>
                      <Badge
                        className={`ml-2 ${
                          signal.action === "buy"
                            ? "bg-green-500"
                            : signal.action === "sell"
                              ? "bg-red-500"
                              : "bg-gray-500"
                        }`}
                      >
                        {signal.action.toUpperCase()}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {(signal.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                No signals yet. Waiting for market scan...
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
