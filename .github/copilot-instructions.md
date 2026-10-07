# Copilot instructions for Trading Bot

- **Backend:** Python 3.12, FastAPI, SQLAlchemy async, alpaca-py, scikit-learn/XGBoost, FinBERT. Managed with **uv**: `cd backend && uv sync`, `uv run pytest`, `uv run ruff check .` (config in `pyproject.toml`, line length 100).
- **Frontend:** Next.js 16, TypeScript, shadcn/ui, pnpm 10: `pnpm install`, `pnpm lint`, `pnpm build`.
- **Architecture:** data → features → models + sentiment → `SignalGenerator` → `RiskManager.check_signal` → `Broker.submit_order`. Interfaces live in `core/*/base.py`. See `docs/ARCHITECTURE.md`.
- **Safety, non-negotiable:**
  - `alpaca_paper` must default to `True`. Never hard-code live endpoints.
  - Never place an order without passing `RiskManager.check_signal`.
  - Never commit `.env`, keys, trade logs or model binaries.
  - Changing a risk rule means updating `tests/unit/test_risk_manager.py`.
- **Conventions:** timestamps in UTC; Pydantic schemas in `app/schemas/` define API contracts; single-letter capitals (`X`, `A`, `T`) are allowed only in maths/ML code.
- **When reviewing PRs:** flag anything touching `config.py` defaults, `core/risk/`, or `core/execution/`, and ask for tests.
