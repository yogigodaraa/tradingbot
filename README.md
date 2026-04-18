# Trading Bot

AI-powered quantitative trading bot for US stocks. Combines ML models, sentiment analysis, and real-time market data to generate automated trading signals on Alpaca.

## What it does

A backend engine that ingests market data + news, runs feature engineering → ML prediction → signal generation → risk check → execution. Supports swing trading and long-term quant strategies, paper or live, with a Next.js dashboard for portfolio metrics, active positions, signals, and backtests.

Every trade passes through a mandatory `RiskManager` gate that enforces position limits, daily loss caps, and drawdown circuit breakers.

## Tech stack

**Backend** (`backend/`, managed by `uv`)
- Python 3.12+, FastAPI
- SQLAlchemy async + Alembic migrations (SQLite)
- scikit-learn, XGBoost (prediction)
- FinBERT via HuggingFace transformers (news sentiment)
- Alpaca broker API (paper + live)
- Alpha Vantage, Finnhub, Alpaca Data API (market data)

**Frontend** (`frontend/`, managed by `pnpm`)
- Next.js 14+, TypeScript
- Shadcn/ui
- TradingView Lightweight Charts, Recharts

## Getting started

```bash
make install       # install backend + frontend deps
make dev           # run both (backend :8000, frontend :3000)
```

Other Make targets:

- `make backend` — FastAPI only
- `make frontend` — Next.js only
- `make test` — backend tests
- `make lint` — lint backend

## Architecture

- All timestamps stored in UTC
- Abstract interfaces: `DataProvider`, `Broker`, `SentimentAnalyzer`, `PredictionModel`
- Pydantic schemas define API contracts; OpenAPI auto-generated
- TradingEngine orchestrates: data → features → predictions → signals → risk → execution

## Status

Active WIP. Core infrastructure established (52+ Python files, test structure, migrations). TODOs remain in `main.py` for trading engine startup, data stream initialization, and scheduler integration.
