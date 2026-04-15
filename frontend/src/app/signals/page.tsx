"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { SignalCard } from "@/components/signals/SignalCard";

export default function SignalsPage() {
  const { data: signals, isLoading } = useQuery({
    queryKey: ["signals"],
    queryFn: () => api.getSignals(50),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trading Signals</h1>

      {isLoading ? (
        <div className="text-muted-foreground animate-pulse">Loading signals...</div>
      ) : signals && signals.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">No signals generated yet.</p>
          <p className="text-sm mt-2">
            Signals will appear here when the bot scans the watchlist during market hours.
          </p>
        </div>
      )}
    </div>
  );
}
