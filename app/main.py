"""FastAPI app: wires the pipeline together and serves the UI.

    ESPN -> espn_client -> normalize -> odds provider -> flags -> JSON -> page
"""

import logging
import pathlib
from dataclasses import asdict
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import LEAGUE
from app.espn_client import UpstreamError, fetch_scoreboard
from app.flags import favorite_undervalued, implied_prob
from app.normalize import normalize_scoreboard
from app.odds_mock import mock_odds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Sports Odds Research Tool",
    description="Flags MLB games where the better team is priced as the underdog.",
)
# Resolved from this file rather than the working directory, so the app
# serves its page identically under uvicorn, Docker and a serverless host.
STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/games")
def get_games(date_str: str | None = Query(default=None, alias="date")):
    """Return the day's games with odds, implied probabilities and flags."""
    # Validate before doing any network work, so a bad date fails fast.
    try:
        day = (
            datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_str
            else date.today()
        )
    except ValueError:
        raise HTTPException(400, "Invalid date. Use YYYY-MM-DD.")

    try:
        raw = fetch_scoreboard(day.strftime("%Y%m%d"))
    except UpstreamError:
        raise HTTPException(
            502, "Couldn't reach the sports data provider. Try again."
        )

    games = normalize_scoreboard(raw)

    out = []
    for g in games:
        g.odds = mock_odds(g, day.isoformat())
        g.flag = favorite_undervalued(g)
        item = asdict(g)
        item["implied"] = {
            "home": round(implied_prob(g.odds.home), 4),
            "away": round(implied_prob(g.odds.away), 4),
        }
        out.append(item)

    # Count only True; a None flag means "couldn't check", not "not flagged".
    flagged = sum(1 for g in out if g["flag"]["favorite_undervalued"] is True)
    log.info("%s: %d games, %d flagged", day.isoformat(), len(out), flagged)

    return {
        "date": day.isoformat(),
        "league": LEAGUE,
        "odds_source": "mock",
        "count": len(out),
        "flagged_count": flagged,
        "games": out,
    }
