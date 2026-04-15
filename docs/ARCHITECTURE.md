# Trading Bot - Architecture Document

> AI-powered quantitative trading bot with live news detection, sentiment analysis, and predictive algorithms.  
> Author: Yogi | Created: 2026-04-15

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRADING BOT SYSTEM                          │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌───────────────┐  │
│  │  DATA    │──>│ SENTIMENT│──>│ PREDICTION│──>│    SIGNAL     │  │
│  │ PIPELINE │   │  ENGINE  │   │  MODELS   │   │  GENERATOR    │  │
│  └──────────┘   └──────────┘   └───────────┘   └───────┬───────┘  │
│       │                                                  │          │
│       │              ┌───────────────┐                   │          │
│       │              │  RISK MANAGER │<──────────────────┘          │
│       │              │  (mandatory)  │                              │
│       │              └───────┬───────┘                              │
│       │                      │                                      │
│       │              ┌───────▼───────┐      ┌──────────────┐       │
│       │              │  EXECUTION    │─────>│   BROKER     │       │
│       │              │  ENGINE       │      │  (Alpaca)    │       │
│       │              └───────────────┘      └──────────────┘       │
│       │                                                             │
│       │    ┌──────────────┐    ┌──────────────┐                    │
│       └───>│  DATABASE    │<───│  BACKTESTER  │                    │
│            │  (SQLite)    │    │              │                    │
│            └──────┬───────┘    └──────────────┘                    │
│                   │                                                 │
│            ┌──────▼───────┐                                        │
│            │  FASTAPI     │                                        │
│            │  REST + WS   │                                        │
│            └──────┬───────┘                                        │
│                   │                                                 │
└───────────────────┼─────────────────────────────────────────────────┘
                    │
             ┌──────▼───────┐
             │   NEXT.JS    │
             │  DASHBOARD   │
             └──────────────┘
```

---

## 2. Tech Stack

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Backend Framework | FastAPI | 0.115+ | Async-native, auto OpenAPI spec, WebSocket support |
| Frontend | Next.js (App Router) | 14+ | TypeScript, Shadcn/ui, TradingView charts |
| Database | SQLite (Phase 1) | - | Zero-config; migrates to PostgreSQL + TimescaleDB in Phase 2 |
| ORM | SQLAlchemy (async) | 2.0+ | Async session support, Alembic migrations |
| ML Framework | scikit-learn + XGBoost | 1.6+ / 3.2+ | Tree models for tabular features, fast iteration |
| Sentiment NLP | FinBERT (ProsusAI) | HuggingFace | Purpose-built for financial text, runs locally on CPU |
| Technical Indicators | ta library | 0.11+ | 40+ indicators (RSI, MACD, Bollinger, ATR, etc.) |
| Broker SDK | alpaca-py | 0.35+ | Paper + live trading, fractional shares, WebSocket streaming |
| News Data | finnhub-python | 2.4+ | Company news, market news, 60 calls/min free |
| Python Package Manager | uv | 0.11+ | Fast, modern lockfile |
| JS Package Manager | pnpm | 10+ | Disk-efficient, fast |
| UI Components | Shadcn/ui | latest | Accessible, customizable, Tailwind CSS |
| Charts | Recharts + Lightweight Charts | latest | Equity curves + financial candlestick charts |
| State Management | TanStack Query | 5+ | Server state, auto-refetch, caching |

---

## 3. Data Flow Architecture

### 3.1 Signal Generation Pipeline

```
Market Data (Alpaca)          News Data (Finnhub)
       │                              │
       ▼                              ▼
 ┌───────────┐                ┌──────────────┐
 │ OHLCV     │                │ News         │
 │ Price Bars │                │ Articles     │
 └─────┬─────┘                └──────┬───────┘
       │                              │
       ▼                              ▼
 ┌───────────┐                ┌──────────────┐
 │ Feature   │                │ FinBERT      │
 │ Engineer  │                │ Sentiment    │
 │ (30+ ind) │                │ Analysis     │
 └─────┬─────┘                └──────┬───────┘
       │                              │
       │    ┌─────────────────┐       │
       └───>│ SIGNAL          │<──────┘
            │ GENERATOR       │
            │                 │
            │ Weights:        │
            │  Model:    50%  │
            │  Sentiment:30%  │
            │  Technical:20%  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ RISK MANAGER    │
            │                 │
            │ Checks:         │
            │  Position size  │
            │  Daily loss     │
            │  Drawdown       │
            │  Confidence     │
            │  Cash available │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ EXECUTION       │──> Alpaca Paper/Live
            │ ENGINE          │
            └─────────────────┘
```

### 3.2 Feature Engineering Pipeline

The feature pipeline produces 30+ features from raw OHLCV data:

**Trend Indicators:**
- SMA (20, 50, 200) + price-relative ratios
- MACD + signal + histogram
- ADX (trend strength)
- SMA crossover signals

**Momentum Indicators:**
- RSI (14-period)
- Stochastic Oscillator (K, D)
- Rate of Change (5, 10, 20)

**Volatility Indicators:**
- Bollinger Bands (upper, lower, width, %B)
- ATR (14-period) + ATR as % of price
- 20-day rolling return volatility

**Volume Indicators:**
- Volume SMA (20) + volume ratio
- On-Balance Volume (OBV)

**Returns:**
- 1-day, 5-day, 10-day, 20-day returns

**Calendar:**
- Day of week, month

**Source:** `backend/app/core/models/features.py`

---

## 4. Component Architecture (Detailed)

### 4.1 Data Pipeline

| Component | File | Purpose |
|-----------|------|---------|
| `DataProvider` (ABC) | `core/data/base.py` | Abstract interface for all data sources |
| `AlpacaDataProvider` | `core/data/alpaca.py` | US stock OHLCV bars, latest prices (REST + WebSocket) |
| `NewsFetcher` | `core/sentiment/news_fetcher.py` | Finnhub company + market news polling |

**Alpaca Data Provider:**
- Historical bars: REST API, supports 1min to 1week timeframes
- Latest prices: Batch endpoint for multiple tickers in one call
- Free IEX feed (or SIP with API keys)
- Returns standardized pandas DataFrames

### 4.2 Sentiment Engine

| Component | File | Purpose |
|-----------|------|---------|
| `SentimentAnalyzer` (ABC) | `core/sentiment/base.py` | Abstract interface for NLP models |
| `FinBERTAnalyzer` | `core/sentiment/finbert.py` | ProsusAI/finbert, local CPU inference (~50ms/article) |
| `SentimentScorer` | `core/sentiment/scorer.py` | Weighted composite scoring with decay |

**Scoring Algorithm:**
1. Fetch news articles for ticker (last 3 days)
2. Run each through FinBERT -> {positive, negative, neutral} probabilities
3. Composite per-article = positive - negative (range: -1 to +1)
4. Weight each article by:
   - **Recency**: Exponential decay (half-life = 48 hours)
   - **Source credibility**: Reuters/Bloomberg = 1.0, SeekingAlpha = 0.6
5. Weighted average = final ticker sentiment score
6. **Momentum**: Compare first-half vs second-half average (trend direction)

### 4.3 Prediction Models

| Model | File | Algorithm | Horizon | Features |
|-------|------|-----------|---------|----------|
| Swing Trading | `core/models/swing.py` | XGBoost Classifier | 5 days | 21 technical + sentiment |
| Long-term Factor | `core/models/longterm.py` | Rule-based Factor Ranking | 30 days | Momentum, trend, RSI, vol, volume |
| Ensemble | `core/models/ensemble.py` | Weighted Voting | Adaptive | All sub-model outputs |

**Swing Model (XGBoost):**
- Binary classification: Will price be higher in 5 trading days?
- 21 features: RSI, MACD, Bollinger, ATR, SMA ratios, volume, momentum
- Training: Rolling 2-year window, 5-fold TimeSeriesSplit cross-validation
- Hyperparameters: 200 trees, max_depth=5, lr=0.05
- Model persistence: joblib serialization to `ml/models/swing_xgb.joblib`

**Long-term Factor Model (Rule-based):**
- 5 weighted factors:
  - Momentum (30%): 20-day ROC
  - Trend alignment (25%): Price vs SMA 20/50/200
  - RSI mean reversion (15%): Oversold bullish, overbought bearish
  - Low volatility (15%): Penalize high-vol stocks
  - Volume confirmation (15%): Above-avg volume on up moves

### 4.4 Signal Generator

**File:** `core/signals/generator.py`

Combines model predictions, sentiment, and technical scores:

```
Composite Score = (Model * 0.50) + (Sentiment * 0.30) + (Technical * 0.20)
```

- If |composite| >= min_confidence (0.65): Generate signal
- BUY: Stop loss at -3%, take profit at +6% (2:1 reward:risk)
- SELL: Inverse of BUY levels
- Strategy assigned based on prediction horizon

### 4.5 Risk Manager

**File:** `core/risk/manager.py`

**Every signal MUST pass through the risk manager before execution.** No exceptions.

| Check | Rule | Action on Fail |
|-------|------|---------------|
| Circuit breaker | Daily loss >= 3% | Block all trades for the day |
| Drawdown | Equity dropped >= 10% from peak | Block all trades |
| Confidence | Signal confidence < 0.65 | Reject signal |
| Position count | >= 5 open positions | Reject new buys |
| Position size | > 20% of portfolio | Reduce quantity |
| Existing position | Already hold ticker at max | Reject signal |
| Cash check | Not enough buying power | Reduce quantity or reject |

**Kelly Criterion** (`core/risk/kelly.py`):
- Half-Kelly for safety (standard practice)
- Capped at 25% max position size
- Formula: f* = (p*b - q) / b / 2, where p=win rate, b=win/loss ratio

### 4.6 Execution Engine

| Component | File | Purpose |
|-----------|------|---------|
| `Broker` (ABC) | `core/execution/base.py` | Abstract interface for all brokers |
| `AlpacaBroker` | `core/execution/alpaca.py` | Alpaca paper + live trading |

**Order types:** Market, Limit  
**Fractional shares:** Minimum $1 order (critical for $100 capital)  
**Paper/Live toggle:** Single env var `ALPACA_PAPER=true/false`

### 4.7 Trading Engine (Orchestrator)

**File:** `core/engine.py`

The brain that wires everything together:

```python
async def scan_watchlist():
    account = await broker.get_account()
    positions = await broker.get_positions()
    prices = await data.get_latest_prices(watchlist)

    for ticker in watchlist:
        sentiment = await sentiment_scorer.score_ticker(ticker)
        prediction = await model.predict(ticker, features)
        signal = await signal_generator.generate(ticker, price, prediction, sentiment)

        if signal:
            risk_result = await risk_manager.check_signal(signal, account, positions)
            if risk_result.approved:
                await execute_signal(signal, risk_result.adjusted_quantity)
```

### 4.8 Backtesting Engine

**File:** `core/backtest/engine.py`

Event-driven backtester that mirrors live execution:
- Iterates through historical bars chronologically
- Applies same signal generation logic
- Passes through same risk manager
- Models slippage (0.1% default) and commissions ($0 for Alpaca)
- Checks stop loss / take profit on each bar

**Metrics computed** (`core/backtest/metrics.py`):
- Total return, annualized return
- Sharpe ratio (risk-free rate = 4% AUS cash rate)
- Sortino ratio (downside-only volatility)
- Max drawdown, average drawdown
- Win rate, profit factor
- Average win %, average loss %, largest win/loss
- Average holding period

---

## 5. Database Schema

```
trades
├── id (PK)
├── broker_order_id
├── ticker (indexed)
├── direction (long/short)
├── status (pending/filled/cancelled/rejected)
├── strategy (swing/longterm)
├── quantity, entry_price, exit_price
├── stop_loss, take_profit
├── pnl, pnl_pct, fees
├── signal_id (FK)
├── created_at, filled_at, closed_at

signals
├── id (PK)
├── ticker (indexed)
├── action (buy/sell/hold)
├── strategy (swing/longterm)
├── confidence
├── entry_price, stop_loss, take_profit
├── model_prediction, sentiment_score, technical_score
├── executed, trade_id
├── created_at

price_bars
├── id (PK)
├── ticker (indexed), timeframe
├── open, high, low, close, volume
├── timestamp (indexed)

sentiment_records
├── id (PK)
├── ticker (indexed)
├── headline, source, url
├── positive, negative, neutral, composite_score
├── published_at, analyzed_at

portfolio_snapshots
├── id (PK)
├── total_value, cash, positions_value
├── daily_pnl, daily_pnl_pct
├── total_pnl, total_pnl_pct
├── drawdown_pct
├── timestamp (indexed)

watchlist
├── id (PK)
├── ticker (unique, indexed)
├── name, sector
├── active
├── added_at
```

---

## 6. API Endpoints

### REST API (FastAPI)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check + status |
| GET | `/api/v1/dashboard/portfolio` | Portfolio overview with positions |
| GET | `/api/v1/dashboard/settings` | Current bot configuration |
| GET | `/api/v1/signals/?limit=50&ticker=AAPL` | List trading signals |
| GET | `/api/v1/trades/?limit=50&ticker=AAPL` | List trade history |
| POST | `/api/v1/backtest/run` | Run backtest with parameters |

### WebSocket

| Endpoint | Events |
|----------|--------|
| `ws://localhost:8000/api/v1/ws/live` | portfolio_update, signal, trade, alert |

### Auto-generated Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 7. Frontend Pages

| Route | Page | Data Source |
|-------|------|-------------|
| `/` | Dashboard | Portfolio + Signals (auto-refresh 30s) |
| `/signals` | Signal Cards | Signals API |
| `/trades` | Trade History Table | Trades API |
| `/backtest` | Interactive Backtester | Backtest API (POST) |
| `/settings` | Bot Configuration | Settings API |

---

## 8. Broker Strategy (Phased)

| Phase | Broker | Market | Min Capital | API Cost |
|-------|--------|--------|-------------|----------|
| 1 | Alpaca (paper) | US Stocks | $0 | Free |
| 2 | Alpaca (live) | US Stocks | $1 (fractional) | Free |
| 3 | OANDA | Forex | $0 | Free |
| 4 | Interactive Brokers | ASX | $5,000+ | $10K API deposit |

---

## 9. Data Source Costs

| Phase | Sources | Monthly Cost |
|-------|---------|-------------|
| 1 (Paper) | Alpaca + Finnhub + Alpha Vantage (free tiers) | $0 |
| 2 (Live) | + Alpha Vantage premium | ~$30-50 AUD |
| 3+ | + Polygon.io + Claude API + VPS | ~$100-300 AUD |

---

## 10. Risk Management Architecture

```
                    Signal
                      │
                      ▼
            ┌─────────────────┐
            │ 1. CIRCUIT      │──> Block if daily loss >= 3%
            │    BREAKER      │
            └────────┬────────┘
                     │ Pass
                     ▼
            ┌─────────────────┐
            │ 2. DRAWDOWN     │──> Block if equity down >= 10% from peak
            │    CHECK        │
            └────────┬────────┘
                     │ Pass
                     ▼
            ┌─────────────────┐
            │ 3. CONFIDENCE   │──> Reject if signal confidence < 65%
            │    CHECK        │
            └────────┬────────┘
                     │ Pass
                     ▼
            ┌─────────────────┐
            │ 4. POSITION     │──> Reject if >= 5 open positions
            │    COUNT        │
            └────────┬────────┘
                     │ Pass
                     ▼
            ┌─────────────────┐
            │ 5. POSITION     │──> Cap at 20% of portfolio
            │    SIZING       │
            └────────┬────────┘
                     │ Pass
                     ▼
            ┌─────────────────┐
            │ 6. CASH         │──> Reduce qty or reject if < $1
            │    CHECK        │
            └────────┬────────┘
                     │ Pass
                     ▼
               EXECUTE ORDER
```

---

## 11. Australian Considerations

### Tax (CGT)
- Track cost base, acquisition date, disposal date for every trade
- 50% CGT discount for assets held > 12 months (long-term strategy benefit)
- Foreign income: US stock gains assessable in Australia
- AUD conversion at exchange rate on disposal date
- Future: Tax reporter module for ATO-compatible CSV export

### Timezone
- US market open: 09:30 ET = 00:30 AEST (next day)
- US market close: 16:00 ET = 07:00 AEST
- All timestamps stored as UTC internally
- Display converted to AEST in frontend
- Bot runs autonomously overnight (Australian time)

### Currency
- Portfolio displayed in both USD and AUD
- AUD/USD exchange rate tracked for accurate valuation
- Alpaca holds USD, OANDA can trade AUD/USD directly

---

## 12. Project File Structure

```
trading-bot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app + lifespan events
│   │   ├── config.py                  # pydantic-settings (env vars)
│   │   │
│   │   ├── api/v1/                    # REST + WebSocket endpoints
│   │   │   ├── __init__.py            # Router aggregator
│   │   │   ├── dashboard.py           # Portfolio + settings
│   │   │   ├── signals.py             # Signal CRUD
│   │   │   ├── trades.py              # Trade history
│   │   │   ├── backtest.py            # Backtest runner
│   │   │   └── ws.py                  # WebSocket connection manager
│   │   │
│   │   ├── core/                      # Business logic
│   │   │   ├── engine.py              # Trading engine orchestrator
│   │   │   ├── data/
│   │   │   │   ├── base.py            # DataProvider ABC
│   │   │   │   └── alpaca.py          # Alpaca REST + WebSocket
│   │   │   ├── sentiment/
│   │   │   │   ├── base.py            # SentimentAnalyzer ABC
│   │   │   │   ├── finbert.py         # FinBERT local model
│   │   │   │   ├── news_fetcher.py    # Finnhub news polling
│   │   │   │   └── scorer.py          # Weighted composite scoring
│   │   │   ├── models/
│   │   │   │   ├── base.py            # PredictionModel ABC
│   │   │   │   ├── features.py        # 30+ technical indicator features
│   │   │   │   ├── swing.py           # XGBoost 5-day classifier
│   │   │   │   ├── longterm.py        # Factor ranking model
│   │   │   │   └── ensemble.py        # Weighted model voting
│   │   │   ├── signals/
│   │   │   │   └── generator.py       # Signal generation (model+sentiment+technical)
│   │   │   ├── execution/
│   │   │   │   ├── base.py            # Broker ABC
│   │   │   │   └── alpaca.py          # Alpaca order execution
│   │   │   ├── risk/
│   │   │   │   ├── manager.py         # 6-check risk gate
│   │   │   │   └── kelly.py           # Kelly Criterion position sizing
│   │   │   └── backtest/
│   │   │       ├── engine.py          # Event-driven backtester
│   │   │       └── metrics.py         # Sharpe, Sortino, drawdown, etc.
│   │   │
│   │   ├── db/
│   │   │   ├── session.py             # Async SQLite/PostgreSQL engine
│   │   │   └── models.py             # 6 ORM models (trades, signals, etc.)
│   │   │
│   │   └── schemas/                   # Pydantic API contracts
│   │       ├── trade.py
│   │       ├── signal.py
│   │       ├── portfolio.py
│   │       ├── backtest.py
│   │       └── settings.py
│   │
│   ├── ml/
│   │   ├── notebooks/                 # Jupyter research notebooks
│   │   └── models/                    # Saved model artifacts (.joblib)
│   │
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   │
│   └── pyproject.toml                 # Python deps (uv)
│
├── frontend/
│   ├── src/
│   │   ├── app/                       # Next.js App Router (5 pages)
│   │   │   ├── layout.tsx             # Root layout + nav + providers
│   │   │   ├── providers.tsx          # TanStack Query provider
│   │   │   ├── page.tsx               # Dashboard (portfolio + signals)
│   │   │   ├── signals/page.tsx       # Signal cards grid
│   │   │   ├── trades/page.tsx        # Trade history table
│   │   │   ├── backtest/page.tsx      # Interactive backtester
│   │   │   └── settings/page.tsx      # Bot configuration
│   │   ├── components/
│   │   │   ├── Nav.tsx                # Top navigation bar
│   │   │   ├── ui/                    # Shadcn/ui components
│   │   │   ├── portfolio/
│   │   │   │   ├── StatsCards.tsx      # 6 metric cards
│   │   │   │   └── PositionsTable.tsx  # Open positions table
│   │   │   ├── signals/
│   │   │   │   └── SignalCard.tsx      # Signal detail card
│   │   │   └── charts/
│   │   │       └── EquityCurve.tsx     # Recharts line chart
│   │   └── lib/
│   │       ├── api/client.ts          # API client + TypeScript types
│   │       └── hooks/useWebSocket.ts  # WebSocket hook with auto-reconnect
│   └── package.json
│
├── docs/
│   └── ARCHITECTURE.md                # This document
├── .env.example                       # Environment variables template
├── .gitignore
├── Makefile                           # dev, test, lint, db commands
└── CLAUDE.md                          # Project documentation for AI
```

---

## 13. Development Commands

```bash
make install         # Install all dependencies (backend + frontend)
make dev             # Run both servers (backend :8000 + frontend :3000)
make backend         # Run FastAPI only
make frontend        # Run Next.js only
make test            # Run backend tests
make lint            # Lint backend code
make db-migrate      # Run database migrations
```

---

## 14. Future Phases

### Phase 2 (Weeks 5-8): Refinement + Live Trading
- Alpha Vantage integration for additional technical indicators
- Long-term model training with fundamental data
- Model ensemble optimization
- Walk-forward backtesting
- Kelly Criterion position sizing
- Email/Slack alerting
- Go live on Alpaca with real capital

### Phase 3 (Weeks 9-12): Market Expansion
- OANDA forex integration (AUD/USD, EUR/USD)
- Migrate SQLite to PostgreSQL + TimescaleDB
- Redis for caching and pub/sub
- Claude API for nuanced news interpretation
- LSTM/Transformer models (PyTorch)

### Phase 4 (Months 4+): Scale
- ASX stocks via Interactive Brokers
- Reinforcement learning for dynamic allocation
- Multi-timeframe analysis
- Options strategies
- Australian tax reporting module (CGT with 50% discount)
- Cloud deployment (AWS/GCP) with monitoring
