import math


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate the Kelly Criterion fraction for position sizing.

    Args:
        win_rate: Historical win rate (0-1)
        avg_win: Average winning trade return (e.g. 0.05 = 5%)
        avg_loss: Average losing trade return as positive number (e.g. 0.03 = 3%)

    Returns:
        Recommended fraction of capital to risk (0-1).
        Uses half-Kelly for safety.
    """
    if avg_loss == 0 or avg_win == 0:
        return 0.0

    # Kelly formula: f* = (p * b - q) / b
    # where p = win probability, q = 1-p, b = win/loss ratio
    b = avg_win / avg_loss
    p = win_rate
    q = 1 - p

    full_kelly = (p * b - q) / b

    # Half-Kelly for safety (standard practice)
    half_kelly = full_kelly / 2

    # Clamp between 0 and 25% max
    return max(0.0, min(0.25, half_kelly))


def position_size_from_kelly(
    capital: float,
    kelly_f: float,
    entry_price: float,
    stop_loss: float,
) -> float:
    """Calculate position size (number of shares) using Kelly fraction.

    Args:
        capital: Total portfolio value
        kelly_f: Kelly fraction (from kelly_fraction())
        entry_price: Planned entry price
        stop_loss: Stop loss price

    Returns:
        Number of shares to buy (can be fractional).
    """
    if entry_price <= 0 or stop_loss <= 0:
        return 0.0

    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share == 0:
        return 0.0

    risk_amount = capital * kelly_f
    shares = risk_amount / risk_per_share

    return max(0.0, shares)
