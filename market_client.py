"""
Market price client — Binance's public SPOT market API.

Unlike binance_client.py/bybit_client.py (undocumented P2P endpoints,
individual merchant quotes), this uses Binance's OFFICIAL, documented
public market-data API: https://binance-docs.github.io/apidocs/spot/en/

IMPORTANT: api.binance.com (the main trading API domain) is known to
geo-block certain regions and IP ranges for regulatory reasons, and
GitHub Actions runners can land on IPs that trigger this. If every
single fetch has been failing, this — not a code bug — is the most
likely cause. To reduce that risk, this tries Binance's DEDICATED
public market-data mirror (data-api.binance.vision, built specifically
for unauthenticated public data access) first, falling back to the
main domain only if that fails.
"""
import logging

from http_utils import get_with_retry

log = logging.getLogger(__name__)

# Tried in order. data-api.binance.vision is a separate domain from the
# main trading API, purpose-built for public market data — less likely
# to carry the same geo-IP restrictions as api.binance.com.
BASE_URLS = [
    "https://data-api.binance.vision/api/v3",
    "https://api.binance.com/api/v3",
]

# The real reason the last fetch failed (HTTP status, exception text,
# etc.), captured so a total failure can explain itself instead of just
# saying "didn't work" — read via get_last_error() right after a None
# return from fetch_current/fetch_price_days_ago.
_last_error: str | None = None


def get_last_error() -> str | None:
    return _last_error


def _get_with_fallback(path: str, params: dict):
    """Tries each base URL in turn, returning the first successful
    response. No per-URL retry — trying multiple domains already serves
    that purpose, and stacking both would make a total failure take
    a very long time to report back."""
    global _last_error
    attempted = []
    for base in BASE_URLS:
        try:
            resp = get_with_retry(f"{base}{path}", params=params, timeout=15, retries=0)
            _last_error = None
            return resp
        except Exception as e:
            attempted.append(f"{base}: {e}")
            log.warning("Market data request to %s%s failed: %s", base, path, e)
    _last_error = "; ".join(attempted)
    raise Exception(_last_error)


def fetch_current(symbol: str) -> dict | None:
    """Current price + 24h change for a Binance spot symbol (e.g. 'BTCUSDT').
    Returns {"price": float, "change_24h_pct": float, "high_24h": float,
    "low_24h": float} or None if every mirror fails — check
    get_last_error() for why."""
    try:
        resp = _get_with_fallback("/ticker/24hr", {"symbol": symbol})
        data = resp.json()
        return {
            "price": float(data["lastPrice"]),
            "change_24h_pct": float(data["priceChangePercent"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
        }
    except Exception as e:
        log.error("Binance spot ticker request failed for %s (all mirrors): %s", symbol, e)
        return None


def fetch_price_days_ago(symbol: str, days: int) -> float | None:
    """Closing price approximately `days` ago, using daily candles.
    Returns None if every mirror fails or there's not enough history yet."""
    try:
        resp = _get_with_fallback("/klines", {
            "symbol": symbol,
            "interval": "1d",
            "limit": days + 1,
        })
        candles = resp.json()
        if not candles or len(candles) < days + 1:
            log.warning("Not enough kline history for %s to look back %d days.", symbol, days)
            return None
        oldest_candle = candles[0]
        return float(oldest_candle[4])  # index 4 = close price
    except Exception as e:
        log.error("Binance klines request failed for %s (%d days, all mirrors): %s", symbol, days, e)
        return None
