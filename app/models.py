"""Plain data containers passed between pipeline stages.

Nothing here knows about ESPN, HTTP, or FastAPI on purpose: the flag logic
only ever sees these types, which is what makes it trivial to unit test.
"""

from dataclasses import dataclass


@dataclass
class Team:
    id: str
    name: str
    abbr: str
    record: str | None        # e.g. "85-70"
    wins: int | None
    losses: int | None
    win_pct: float | None     # None when the record is missing or 0-0


@dataclass
class Odds:
    home: int                 # American moneyline, e.g. -150
    away: int                 # e.g. +130
    source: str               # "mock", or a real provider's name


@dataclass
class FlagResult:
    favorite_undervalued: bool | None   # None means N/A, not False
    higher_ranked: str | None           # "home" | "away" | None
    reason: str


@dataclass
class Game:
    id: str
    start_time: str
    status: str
    home: Team
    away: Team
    odds: Odds | None = None
    flag: FlagResult | None = None
