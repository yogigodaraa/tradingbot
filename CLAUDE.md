# Trading Bot

AI-powered quantitative trading bot for US stocks (Alpaca), with swing trading and long-term quant strategies.

## Stack
- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / SQLite
- **Frontend**: Next.js 14+ / TypeScript / Shadcn/ui / TradingView Lightweight Charts
- **ML**: scikit-learn, XGBoost, FinBERT (HuggingFace transformers)
- **Broker**: Alpaca (US stocks, paper + live)
- **Data**: Alpaca Data API, Finnhub, Alpha Vantage

## Project Structure
- `backend/` - Python FastAPI backend (managed by `uv`)
- `frontend/` - Next.js TypeScript frontend (managed by `pnpm`)
- `scripts/` - Utility scripts

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
