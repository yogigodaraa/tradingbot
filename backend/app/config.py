from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./trading_bot.db"

    # Alpaca
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_paper: bool = True

    # Finnhub
    finnhub_api_key: str = ""

    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # Risk management
    max_position_pct: float = Field(default=0.20, description="Max % of portfolio per position")
    max_open_positions: int = Field(default=5, description="Max concurrent open positions")
    max_daily_loss_pct: float = Field(default=0.03, description="Max daily loss before circuit breaker")
    max_drawdown_pct: float = Field(default=0.10, description="Max drawdown before pausing bot")
    min_signal_confidence: float = Field(default=0.65, description="Min confidence to act on a signal")

    # Watchlist
    default_watchlist: list[str] = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM",
        "V", "UNH", "XOM", "JNJ", "WMT", "PG", "MA", "HD", "CVX", "MRK",
        "ABBV", "PEP", "KO", "COST", "AVGO", "TMO", "MCD", "SPY", "QQQ",
        "DIA", "IWM", "VTI",
    ]

    @property
    def alpaca_base_url(self) -> str:
        if self.alpaca_paper:
            return "https://paper-api.alpaca.markets"
        return "https://api.alpaca.markets"


settings = Settings()
