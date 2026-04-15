"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function TradesPage() {
  const { data: trades, isLoading } = useQuery({
    queryKey: ["trades"],
    queryFn: () => api.getTrades(50),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trade History</h1>

      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground animate-pulse">Loading trades...</div>
          ) : trades && trades.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Ticker</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead>Strategy</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Exit</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((trade) => (
                  <TableRow key={trade.id}>
                    <TableCell className="text-sm">
                      {new Date(trade.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="font-bold">{trade.ticker}</TableCell>
                    <TableCell>
                      <Badge
                        variant={trade.direction === "long" ? "default" : "destructive"}
                      >
                        {trade.direction.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{trade.strategy}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{trade.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.quantity.toFixed(4)}
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.entry_price ? `$${trade.entry_price.toFixed(2)}` : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : "-"}
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        trade.pnl !== null
                          ? trade.pnl >= 0
                            ? "text-green-500"
                            : "text-red-500"
                          : ""
                      }`}
                    >
                      {trade.pnl !== null
                        ? `$${trade.pnl.toFixed(2)} (${(trade.pnl_pct! * 100).toFixed(1)}%)`
                        : "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No trades executed yet. Start paper trading to see trade history.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
