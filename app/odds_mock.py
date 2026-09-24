"""Deterministic mock odds.

Two requirements pull against each other here. The odds must look realistic
(roughly driven by team strength) but must not be perfect, because a market
that always agrees with the records would never produce a flag. The noise term
in step 4 is what creates the disagreements the tool exists to surface.

They must also be reproducible: the same date and game always yield the same
odds, so a demo or a test gives the same answer every run.
"""

import hashlib
import random

from app.config import (
    HOME_FIELD_BUMP,
    NOISE_SD,
    PROB_CEILING,
    PROB_FLOOR,
    VIG,
)
from app.models import Game, Odds


def _seeded_rng(date: str, game_id: str) -> random.Random:
    """A per-game RNG seeded from a stable hash.

    Python's built-in hash() is salted per process, so it would give different
    odds on every restart. SHA-256 is stable across runs and machines.
    """
    digest = hashlib.sha256(f"{date}:{game_id}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _log5(p_a: float, p_b: float) -> float:
    """Probability that A beats B given each side's win percentage."""
    denom = p_a + p_b - 2 * p_a * p_b
    return 0.5 if denom == 0 else (p_a - p_a * p_b) / denom


def prob_to_american(p: float) -> int:
    """Convert a win probability into American moneyline odds, rounded to 5."""
    if p <= 0 or p >= 1:
        raise ValueError(f"probability must be strictly between 0 and 1, got {p}")
    raw = -100 * p / (1 - p) if p >= 0.5 else 100 * (1 - p) / p
    return int(round(raw / 5) * 5)


def mock_odds(game: Game, date: str) -> Odds:
    """Generate deterministic mock moneyline odds for one game."""
    rng = _seeded_rng(date, game.id)

    # 1. Base probability from team strength, or a coin flip if we don't know.
    ph, pa = game.home.win_pct, game.away.win_pct
    base = _log5(ph, pa) if ph is not None and pa is not None else 0.5

    # 2. Home-field edge, plus the market noise that creates flaggable games.
    p_home = base + HOME_FIELD_BUMP + rng.gauss(0, NOISE_SD)
    p_home = min(PROB_CEILING, max(PROB_FLOOR, p_home))

    # 3. Apply the bookmaker's margin so the two sides sum to VIG, not 1.0.
    home_vig = min(p_home * VIG, 0.95)
    away_vig = min((1 - p_home) * VIG, 0.95)

    return Odds(
        home=prob_to_american(home_vig),
        away=prob_to_american(away_vig),
        source="mock",
    )
