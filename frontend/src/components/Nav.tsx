"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, History, LineChart, Newspaper, Settings, TrendingUp, Zap } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/market", label: "Market", icon: TrendingUp },
  { href: "/news", label: "News", icon: Newspaper },
  { href: "/signals", label: "Signals", icon: Zap },
  { href: "/trades", label: "Trades", icon: History },
  { href: "/backtest", label: "Backtest", icon: LineChart },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-border bg-card">
      <div className="container mx-auto px-4">
        <div className="flex items-center h-14 gap-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Activity className="h-5 w-5 text-green-500" />
            <span>TradingBot</span>
          </Link>

          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse" />
              <span className="text-xs text-muted-foreground">Paper Trading</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
