"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type NewsArticle } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Newspaper,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  Search,
  Brain,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
} from "recharts";

function SentimentBadge({ label, score }: { label: string; score: number }) {
  const config = {
    bullish: { color: "bg-green-500/20 text-green-400 border-green-500/30", icon: TrendingUp },
    bearish: { color: "bg-red-500/20 text-red-400 border-red-500/30", icon: TrendingDown },
    neutral: { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", icon: Minus },
  }[label] || { color: "bg-gray-500/20 text-gray-400", icon: Minus };

  return (
    <Badge variant="outline" className={`${config.color} flex items-center gap-1`}>
      <config.icon className="h-3 w-3" />
      {label.toUpperCase()} ({score > 0 ? "+" : ""}{score.toFixed(2)})
    </Badge>
  );
}

function NewsCard({ article }: { article: NewsArticle }) {
  return (
    <div className="p-4 rounded-lg border border-border hover:bg-accent/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-xs">
              {article.ticker}
            </Badge>
            <span className="text-xs text-muted-foreground">{article.source}</span>
            <span className="text-xs text-muted-foreground">
              {new Date(article.published_at).toLocaleDateString()}{" "}
              {new Date(article.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
          <h3 className="font-medium leading-tight mb-1">{article.headline}</h3>
          {article.summary && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {article.summary}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          {article.sentiment && (
            <SentimentBadge label={article.sentiment.label} score={article.sentiment.score} />
          )}
          {article.url && (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              Read
            </a>
          )}
        </div>
      </div>

      {/* Sentiment bar */}
      {article.sentiment && (
        <div className="mt-3 flex items-center gap-2">
          <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden flex">
            <div
              className="h-full bg-green-500"
              style={{ width: `${article.sentiment.positive * 100}%` }}
            />
            <div
              className="h-full bg-gray-500"
              style={{ width: `${article.sentiment.neutral * 100}%` }}
            />
            <div
              className="h-full bg-red-500"
              style={{ width: `${article.sentiment.negative * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground w-32 text-right">
            +{(article.sentiment.positive * 100).toFixed(0)}% / {(article.sentiment.neutral * 100).toFixed(0)}% / {(article.sentiment.negative * 100).toFixed(0)}%
          </span>
        </div>
      )}
    </div>
  );
}

export default function NewsPage() {
  const [tickerFilter, setTickerFilter] = useState<string>("");
  const [impactTicker, setImpactTicker] = useState<string>("AAPL");

  const { data: newsFeed, isLoading: newsLoading, refetch } = useQuery({
    queryKey: ["news", tickerFilter],
    queryFn: () => api.getNewsFeed(tickerFilter || undefined, 30),
    refetchInterval: 300_000, // refresh every 5 min
  });

  const { data: impact, isLoading: impactLoading } = useQuery({
    queryKey: ["impact", impactTicker],
    queryFn: () => api.getNewsImpact(impactTicker),
    enabled: !!impactTicker,
  });

  // Prepare impact chart data
  const impactChartData = impact?.sentiment_by_day.map((s) => {
    const price = impact.price_timeline.find((p) => p.date === s.date);
    return {
      date: s.date.slice(5),
      sentiment: s.avg_sentiment,
      price: price?.close || 0,
      articles: s.article_count,
    };
  }) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Newspaper className="h-6 w-6 text-purple-500" />
          <h1 className="text-2xl font-bold">News & Sentiment</h1>
        </div>
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-purple-400" />
          <span className="text-xs text-muted-foreground">
            Powered by FinBERT AI
          </span>
        </div>
      </div>

      {/* News Impact Analysis */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>News Impact Analysis</CardTitle>
            <div className="flex items-center gap-2">
              <input
                className="px-3 py-1.5 rounded-md border border-border bg-background text-sm w-24"
                placeholder="Ticker"
                value={impactTicker}
                onChange={(e) => setImpactTicker(e.target.value.toUpperCase())}
              />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            See how news sentiment correlates with {impactTicker} price over the last 7 days
          </p>
        </CardHeader>
        <CardContent>
          {impactLoading ? (
            <div className="h-[250px] flex items-center justify-center text-muted-foreground animate-pulse">
              Analyzing {impactTicker} news impact...
            </div>
          ) : impactChartData.length > 0 ? (
            <div className="space-y-4">
              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 rounded-lg bg-accent/50">
                  <div className="text-sm text-muted-foreground">7-Day Price Change</div>
                  <div className={`text-xl font-bold ${(impact?.summary.price_change_7d || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {(impact?.summary.price_change_7d || 0) >= 0 ? "+" : ""}
                    {impact?.summary.price_change_7d.toFixed(2)}%
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-accent/50">
                  <div className="text-sm text-muted-foreground">Avg Sentiment</div>
                  <div className={`text-xl font-bold ${(impact?.summary.avg_sentiment || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {(impact?.summary.avg_sentiment || 0) >= 0 ? "+" : ""}
                    {impact?.summary.avg_sentiment.toFixed(3)}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-accent/50">
                  <div className="text-sm text-muted-foreground">Articles Analyzed</div>
                  <div className="text-xl font-bold">{impact?.summary.total_articles}</div>
                </div>
              </div>

              {/* Dual axis chart: price + sentiment */}
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={impactChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" stroke="#888" fontSize={11} />
                  <YAxis yAxisId="price" stroke="#3b82f6" fontSize={11} />
                  <YAxis yAxisId="sentiment" orientation="right" stroke="#a855f7" fontSize={11} domain={[-1, 1]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333", borderRadius: "8px" }}
                  />
                  <Line yAxisId="price" type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot name="Price ($)" />
                  <Line yAxisId="sentiment" type="monotone" dataKey="sentiment" stroke="#a855f7" strokeWidth={2} dot name="Sentiment" />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-6 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-500 inline-block" /> Price</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-purple-500 inline-block" /> Sentiment</span>
              </div>
            </div>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-muted-foreground">
              Add Alpaca + Finnhub API keys to .env to see news impact analysis.
            </div>
          )}
        </CardContent>
      </Card>

      {/* News Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Live News Feed</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
                <input
                  className="pl-8 pr-3 py-1.5 rounded-md border border-border bg-background text-sm w-40"
                  placeholder="Filter by ticker..."
                  value={tickerFilter}
                  onChange={(e) => setTickerFilter(e.target.value.toUpperCase())}
                />
              </div>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                Refresh
              </Button>
            </div>
          </div>
          {newsFeed && (
            <p className="text-sm text-muted-foreground">
              {newsFeed.count} articles {newsFeed.analyzed ? "analyzed with FinBERT" : ""}
            </p>
          )}
        </CardHeader>
        <CardContent>
          {newsLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-24 rounded-lg bg-accent/30 animate-pulse" />
              ))}
            </div>
          ) : newsFeed && newsFeed.articles.length > 0 ? (
            <div className="space-y-3">
              {newsFeed.articles.map((article, i) => (
                <NewsCard key={`${article.ticker}-${i}`} article={article} />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 text-muted-foreground">
              <Newspaper className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">No news articles yet.</p>
              <p className="text-sm mt-2">
                Add your Finnhub API key to .env to see real financial news with AI sentiment analysis.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
