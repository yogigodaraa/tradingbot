"""Safety defaults: the bot must trade on paper unless live trading is explicitly enabled."""

from app.config import Settings


def test_paper_trading_is_the_default(monkeypatch):
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    settings = Settings(_env_file=None)

    assert settings.alpaca_paper is True
    assert settings.alpaca_base_url == "https://paper-api.alpaca.markets"


def test_live_trading_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER", "false")

    settings = Settings(_env_file=None)

    assert settings.alpaca_paper is False
    assert settings.alpaca_base_url == "https://api.alpaca.markets"
