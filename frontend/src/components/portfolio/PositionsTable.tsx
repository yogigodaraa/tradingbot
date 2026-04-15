"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Position } from "@/lib/api/client";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(value);
}

export function PositionsTable({ positions }: { positions: Position[] }) {
  if (positions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No open positions. The bot will generate signals when markets are open.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ticker</TableHead>
          <TableHead>Side</TableHead>
          <TableHead className="text-right">Qty</TableHead>
          <TableHead className="text-right">Avg Entry</TableHead>
          <TableHead className="text-right">Current</TableHead>
          <TableHead className="text-right">Value</TableHead>
          <TableHead className="text-right">P&L</TableHead>
          <TableHead className="text-right">P&L %</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {positions.map((pos) => (
          <TableRow key={pos.ticker}>
            <TableCell className="font-bold">{pos.ticker}</TableCell>
            <TableCell>
              <Badge variant={pos.side === "long" ? "default" : "destructive"}>
                {pos.side.toUpperCase()}
              </Badge>
            </TableCell>
            <TableCell className="text-right">{pos.quantity.toFixed(4)}</TableCell>
            <TableCell className="text-right">
              {formatCurrency(pos.avg_entry_price)}
            </TableCell>
            <TableCell className="text-right">
              {formatCurrency(pos.current_price)}
            </TableCell>
            <TableCell className="text-right">
              {formatCurrency(pos.market_value)}
            </TableCell>
            <TableCell
              className={`text-right font-medium ${
                pos.unrealized_pnl >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {formatCurrency(pos.unrealized_pnl)}
            </TableCell>
            <TableCell
              className={`text-right font-medium ${
                pos.unrealized_pnl_pct >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {(pos.unrealized_pnl_pct * 100).toFixed(2)}%
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
