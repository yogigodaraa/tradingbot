"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Signal } from "@/lib/api/client";

export function SignalCard({ signal }: { signal: Signal }) {
  const actionColor =
    signal.action === "buy"
      ? "bg-green-500"
      : signal.action === "sell"
        ? "bg-red-500"
        : "bg-gray-500";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{signal.ticker}</CardTitle>
          <div className="flex gap-2">
            <Badge className={actionColor}>{signal.action.toUpperCase()}</Badge>
            <Badge variant="outline">{signal.strategy}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Confidence:</span>{" "}
            <span className="font-medium">{(signal.confidence * 100).toFixed(1)}%</span>
          </div>
          {signal.entry_price && (
            <div>
              <span className="text-muted-foreground">Entry:</span>{" "}
              <span className="font-medium">${signal.entry_price.toFixed(2)}</span>
            </div>
          )}
          {signal.stop_loss && (
            <div>
              <span className="text-muted-foreground">Stop Loss:</span>{" "}
              <span className="font-medium text-red-400">
                ${signal.stop_loss.toFixed(2)}
              </span>
            </div>
          )}
          {signal.take_profit && (
            <div>
              <span className="text-muted-foreground">Take Profit:</span>{" "}
              <span className="font-medium text-green-400">
                ${signal.take_profit.toFixed(2)}
              </span>
            </div>
          )}
          {signal.sentiment_score !== null && (
            <div>
              <span className="text-muted-foreground">Sentiment:</span>{" "}
              <span
                className={`font-medium ${
                  signal.sentiment_score >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {signal.sentiment_score.toFixed(2)}
              </span>
            </div>
          )}
          <div>
            <span className="text-muted-foreground">Executed:</span>{" "}
            <Badge variant={signal.executed ? "default" : "secondary"}>
              {signal.executed ? "Yes" : "No"}
            </Badge>
          </div>
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          {new Date(signal.created_at).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}
