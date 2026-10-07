# Trading Bot

[![CI](https://github.com/yogigodaraa/tradingbot/actions/workflows/ci.yml/badge.svg)](https://github.com/yogigodaraa/tradingbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> [!CAUTION]
> **Not financial advice. Use at your own risk.** This is a personal research and learning
> project. It is not investment advice, not a recommendation to buy or sell any security, and
> comes with **no warranty** (see [LICENSE](LICENSE)). Trading involves substantial risk of loss.
> Past or backtested performance does not predict future results. The bot runs on **Alpaca paper
> trading by default**. Only switch to live trading if you fully understand the code and accept
> the risk of losing money.

AI-assisted quantitative trading research bot for US stocks on Alpaca. It combines ML price
models (scikit-learn / XGBoost), FinBERT news sentiment and technical indicators into trading
signals. Every signal must pass a `RiskManager` gate before an order can be placed.

## What it does

```text
market data + news → features → ML predictions + FinBERT sentiment → signal → RiskManager → Alpaca order
```

- **Signals:** swing and long-term strategies combine model predictions, sentiment and technical scores (`backend/app/core/signals/`).
- **Risk gate** (`backend/app/core/risk/manager.py`), checked in order:
  daily-loss circuit breaker → max drawdown from peak → minimum confidence → max open positions →
  max % of equity per position → available cash. Covered by unit tests in `backend/tests/unit/`.
- **Backtesting:** engine, metrics, walk-forward validation and market-regime detection (`backend/app/core/backtest/`).
- **Dashboard:** Next.js pages for portfolio, signals, trades, market movers, news sentiment and backtests.

### Current state

The building blocks above exist, but **the automated trading loop isn't switched on yet**:
`TradingEngine` is never started in `backend/app/main.py` (see its `TODO`s). Today the API serves
market data, news/sentiment, backtests and read-only portfolio/trade views.

## Screenshots

<!-- TODO: add dashboard screenshots (paper account only) -->
_Coming soon._

## Paper vs live trading

| Setting | Default | Effect |
|---|---|---|
| `ALPACA_PAPER` | `true` | Orders go to `https://paper-api.alpaca.markets` (simulated money) |
| `ALPACA_PAPER=false` | n/a | Orders go to the **live** API with **real money** |

The default is enforced in `backend/app/config.py` and tested in `backend/tests/unit/test_config.py`.
The backend logs `Paper trading: True/False` on startup, and `/health` reports `paper_trading`.

## Tech stack

- **Backend** (`backend/`, managed by [uv](https://docs.astral.sh/uv/)): Python 3.12, FastAPI, SQLAlchemy (async, SQLite), alpaca-py, scikit-learn, XGBoost, Hugging Face Transformers (FinBERT), pandas
- **Frontend** (`frontend/`, managed by pnpm 10): Next.js 16, TypeScript, shadcn/ui, Recharts, TradingView Lightweight Charts

## Quickstart

```bash
git clone https://github.com/yogigodaraa/tradingbot.git
cd tradingbot
cp .env.example .env          # add your Alpaca PAPER keys; keep ALPACA_PAPER=true
make install                  # uv sync + pnpm install
make dev                      # backend :8000, frontend :3000
```

Get paper-trading keys at <https://app.alpaca.markets/> (Paper account). The Finnhub and
Alpha Vantage keys are optional for news and indicators. **Never commit `.env`.** It's git-ignored.

### Tests and checks

```bash
make test                                # backend pytest
make lint                                # ruff (config in backend/pyproject.toml)
cd frontend && pnpm lint && pnpm build
```

## Architecture

A guided code tour and the original design document: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Project status

**Active work in progress.** Core modules, backtester and dashboard exist. The live trading loop,
scheduler and data streams are still TODO.

## Roadmap

- [ ] Start `TradingEngine` + scheduler from the app lifespan (paper only at first)
- [ ] Size sell orders from the held position, not the buy limit (see issues)
- [ ] Implement or remove the "sector concentration" limit mentioned in the `RiskManager` docstring
- [ ] Tests for signal generation and the backtest metrics
<!-- TODO(yogi): add your own roadmap items -->

## License

MIT. See [LICENSE](LICENSE). The software is provided "as is", without warranty of any kind.
