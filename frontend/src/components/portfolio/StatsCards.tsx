"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  Shield,
} from "lucide-react";
import type { PortfolioOverview } from "@/lib/api/client";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatPct(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function StatsCards({ portfolio }: { portfolio: PortfolioOverview }) {
  const stats = [
    {
      title: "Portfolio Value",
      value: formatCurrency(portfolio.total_value),
      icon: DollarSign,
      color: "text-blue-500",
    },
    {
      title: "Cash",
      value: formatCurrency(portfolio.cash),
      icon: BarChart3,
      color: "text-green-500",
    },
    {
      title: "Daily P&L",
      value: `${formatCurrency(portfolio.daily_pnl)} (${formatPct(portfolio.daily_pnl_pct)})`,
      icon: portfolio.daily_pnl >= 0 ? TrendingUp : TrendingDown,
      color: portfolio.daily_pnl >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      title: "Total P&L",
      value: `${formatCurrency(portfolio.total_pnl)} (${formatPct(portfolio.total_pnl_pct)})`,
      icon: portfolio.total_pnl >= 0 ? TrendingUp : TrendingDown,
      color: portfolio.total_pnl >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      title: "Positions",
      value: `${portfolio.positions.length} open`,
      icon: Activity,
      color: "text-purple-500",
    },
    {
      title: "Drawdown",
      value: formatPct(-portfolio.drawdown_pct),
      icon: Shield,
      color: portfolio.drawdown_pct > 5 ? "text-red-500" : "text-yellow-500",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-lg font-bold ${stat.color}`}>{stat.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
