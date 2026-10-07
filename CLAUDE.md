# Trading Bot

AI-powered quantitative trading bot for US stocks (Alpaca), with swing trading and long-term quant strategies.

## Stack
- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy async / SQLite
- **Frontend**: Next.js 16 / TypeScript (pnpm 10) / Shadcn/ui / TradingView Lightweight Charts
- **ML**: scikit-learn, XGBoost, FinBERT (HuggingFace transformers)
- **Broker**: Alpaca (US stocks, paper + live)
- **Data**: Alpaca Data API, Finnhub, Alpha Vantage

## Project Structure
- `backend/` - Python FastAPI backend (managed by `uv`)
- `frontend/` - Next.js TypeScript frontend (managed by `pnpm`)
- `docs/ARCHITECTURE.md` - code tour + original design doc

## Commands
- `make install` - Install all dependencies
- `make dev` - Run both servers (backend :8000, frontend :3000)
- `make backend` - Run FastAPI only
- `make frontend` - Run Next.js only
- `make test` - Run backend tests
- `make lint` - Lint backend code

## Architecture
- All timestamps stored in UTC
- Abstract interfaces for DataProvider, Broker, SentimentAnalyzer, PredictionModel
- Risk manager is a mandatory gate before every trade execution
- Pydantic schemas define API contracts, auto-generate OpenAPI spec

## Tests
- `backend/tests/unit/test_risk_manager.py` covers every RiskManager rule. Update it whenever a rule changes.
- `backend/tests/unit/test_config.py` locks in paper trading as the default.
- CI: `backend / test` (uv sync, ruff, pytest) and `frontend / test` (pnpm lint, build).

## Safety rules (do not break)
- **Paper trading stays the default.** Never change `alpaca_paper` to default `False`, and never hard-code live URLs.
- **Every order goes through `RiskManager.check_signal`.** No code path may call `broker.submit_order` without it.
- Never commit `.env`, API keys, account numbers, trade logs or trained model files (`backend/ml/models/` stays empty in git).
- Don't loosen risk limits in code defaults; users change them via `.env`.
- Keep the "not financial advice" disclaimer in the README.

