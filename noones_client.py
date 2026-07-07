"""
Noones (formerly Paxful) client — PHASE 2, NOT ACTIVE BY DEFAULT.
Requires authenticated API key/secret for every endpoint. Returns an
empty list until that's implemented, so the bot runs fine without it.
"""
import logging

import settings

log = logging.getLogger(__name__)


def fetch_ads(trade_type: str, amount: float | None = None, fiat: str | None = None, rows: int = 10) -> list[dict]:
    if not settings.ENABLE_NOONES:
        return []
    if not settings.NOONES_API_KEY or not settings.NOONES_API_SECRET:
        log.warning("ENABLE_NOONES is true but NOONES_API_KEY/SECRET are missing. Skipping.")
        return []
    log.warning("Noones client is not implemented yet (needs HMAC request signing).")
    return []
