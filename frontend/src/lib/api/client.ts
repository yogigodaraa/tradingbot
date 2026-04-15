const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

// === Types ===

export interface Position {
  ticker: string;
  quantity: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  side: string;
}

export interface PortfolioOverview {
  total_value: number;
  cash: number;
  positions_value: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  total_pnl: number;
  total_pnl_pct: number;
  drawdown_pct: number;
  positions: Position[];
  updated_at: string;
}

export interface Signal {
  id: number;
  ticker: string;
  action: "buy" | "sell" | "hold";
  strategy: "swing" | "longterm";
  confidence: number;
  entry_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  model_prediction: number | null;
  sentiment_score: number | null;
  technical_score: number | null;
  executed: boolean;
  trade_id: number | null;
  created_at: string;
}

export interface Trade {
  id: number;
  broker_order_id: string | null;
  ticker: string;
  direction: "long" | "short";
  status: string;
  strategy: "swing" | "longterm";
  quantity: number;
  entry_price: number | null;
  exit_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  fees: number;
  created_at: string;
  filled_at: string | null;
  closed_at: string | null;
}

export interface BotSettings {
  paper_trading: boolean;
  max_position_pct: number;
  max_open_positions: number;
  max_daily_loss_pct: number;
  max_drawdown_pct: number;
  min_signal_confidence: number;
  watchlist: string[];
}

export interface BacktestRequest {
  ticker: string;
  initial_capital: number;
  days: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  max_position_pct: number;
  max_positions: number;
}

export interface BacktestMetrics {
  total_return_pct: number;
  annualized_return_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  avg_win_pct: number;
  avg_loss_pct: number;
  final_equity: number;
  initial_capital: number;
}

export interface BacktestResponse {
  metrics: BacktestMetrics;
  trades: { ticker: string; entry_date: string; entry_price: number; exit_date: string | null; exit_price: number | null; direction: string; pnl: number; pnl_pct: number }[];
  equity_curve: { timestamp: string; equity: number }[];
}

// === Market Data Types ===

export interface StockPrice {
  ticker: string;
  price: number;
}

export interface Mover {
  ticker: string;
  price: number;
  change: number;
  change_pct: number;
  prev_close: number;
}

export interface MoversResponse {
  gainers: Mover[];
  losers: Mover[];
  all: Mover[];
  updated_at: string;
}

export interface ChartBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  ticker: string;
  timeframe: string;
  bars: ChartBar[];
  count: number;
}

// === News Types ===

export interface NewsSentiment {
  label: "bullish" | "bearish" | "neutral";
  score: number;
  positive: number;
  negative: number;
  neutral: number;
}

export interface NewsArticle {
  headline: string;
  summary: string;
  source: string;
  url: string;
  ticker: string;
  published_at: string;
  sentiment: NewsSentiment | null;
}

export interface NewsFeedResponse {
  articles: NewsArticle[];
  count: number;
  analyzed: boolean;
  updated_at: string;
}

export interface TickerSentimentResponse {
  ticker: string;
  overall_sentiment: "bullish" | "bearish" | "neutral";
  overall_score: number;
  article_count: number;
  articles: { headline: string; source: string; published_at: string; label: string; score: number }[];
  analyzed_at: string;
}

export interface NewsImpactResponse {
  ticker: string;
  price_timeline: { date: string; close: number; volume: number }[];
  news_timeline: { date: string; headline: string; sentiment_score: number; source: string }[];
  sentiment_by_day: { date: string; avg_sentiment: number; article_count: number }[];
  summary: { total_articles: number; avg_sentiment: number; price_change_7d: number };
}

// === API Functions ===

export const api = {
  // Dashboard
  getPortfolio: () => fetchAPI<PortfolioOverview>("/api/v1/dashboard/portfolio"),
  getSettings: () => fetchAPI<BotSettings>("/api/v1/dashboard/settings"),
  getSignals: (limit = 50) => fetchAPI<Signal[]>(`/api/v1/signals/?limit=${limit}`),
  getTrades: (limit = 50) => fetchAPI<Trade[]>(`/api/v1/trades/?limit=${limit}`),

  // Market data
  getPrices: (tickers?: string) =>
    fetchAPI<{ prices: StockPrice[]; updated_at: string }>(
      `/api/v1/market/prices${tickers ? `?tickers=${tickers}` : ""}`
    ),
  getChart: (ticker: string, days = 90, timeframe = "1d") =>
    fetchAPI<ChartResponse>(`/api/v1/market/chart/${ticker}?days=${days}&timeframe=${timeframe}`),
  getMovers: () => fetchAPI<MoversResponse>("/api/v1/market/movers"),

  // News + Sentiment
  getNewsFeed: (ticker?: string, limit = 20) =>
    fetchAPI<NewsFeedResponse>(
      `/api/v1/news/feed?limit=${limit}${ticker ? `&ticker=${ticker}` : ""}`
    ),
  getTickerSentiment: (ticker: string, days = 3) =>
    fetchAPI<TickerSentimentResponse>(`/api/v1/news/sentiment/${ticker}?days=${days}`),
  getNewsImpact: (ticker: string) =>
    fetchAPI<NewsImpactResponse>(`/api/v1/news/impact?ticker=${ticker}`),

  // Backtest
  runBacktest: (params: BacktestRequest) =>
    fetchAPI<BacktestResponse>("/api/v1/backtest/run", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  health: () => fetchAPI<{ status: string }>("/health"),
};
