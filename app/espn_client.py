"""Fetches raw scoreboard JSON from ESPN.

This module's only job is to return a dict or raise one clear error. It does
no parsing, so a change in ESPN's response shape is somebody else's problem
(see normalize.py).
"""

import logging

import httpx

from app.config import ESPN_SCOREBOARD_URL, HTTP_TIMEOUT_SECONDS

log = logging.getLogger(__name__)


class UpstreamError(Exception):
    """The sports data provider could not be reached or returned bad data."""


def fetch_scoreboard(date_yyyymmdd: str) -> dict:
    """Fetch the MLB scoreboard for a date formatted as YYYYMMDD (no dashes)."""
    try:
        resp = httpx.get(
            ESPN_SCOREBOARD_URL,
            params={"dates": date_yyyymmdd},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        # ValueError covers a 200 response whose body isn't valid JSON.
        log.warning("ESPN request failed for %s: %s", date_yyyymmdd, exc)
        raise UpstreamError(f"ESPN request failed: {exc}") from exc
