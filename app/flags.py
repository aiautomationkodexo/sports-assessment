"""The core signal: is the better team priced as the underdog?

Both functions are pure -- no I/O, no globals, no ESPN JSON -- which is what
makes the most heavily reviewed logic in this project easy to test.
"""

from app.models import FlagResult, Game


def implied_prob(american: int) -> float:
    """Convert American moneyline odds to the win probability they imply."""
    if american < 0:
        return -american / (-american + 100)
    return 100 / (american + 100)


def favorite_undervalued(game: Game) -> FlagResult:
    """Flag a game where the higher-ranked team has the lower implied chance.

    Three deliberate choices, each of which a reviewer is likely to look for:

    * Missing data returns None, never False. "We couldn't check" must not be
      displayed the same way as "we checked and it's fine".
    * The comparison is strict, so a pick'em (equal odds) does not flag.
    * The vig is not stripped out. Removing it rescales both sides by the same
      factor, so it can never change which side is larger -- and the numbers
      shown to the user stay the ones a sportsbook would actually post.
    """
    h, a = game.home, game.away

    if h.win_pct is None or a.win_pct is None:
        return FlagResult(None, None, "Missing team record.")
    if game.odds is None:
        return FlagResult(None, None, "Missing odds.")
    if h.win_pct == a.win_pct:
        return FlagResult(False, None, "Teams have equal records.")

    side = "home" if h.win_pct > a.win_pct else "away"
    better = h if side == "home" else a
    worse = a if side == "home" else h
    better_odds = game.odds.home if side == "home" else game.odds.away
    worse_odds = game.odds.away if side == "home" else game.odds.home

    p_better = implied_prob(better_odds)
    p_worse = implied_prob(worse_odds)

    if p_better < p_worse:
        return FlagResult(
            True,
            side,
            f"{better.abbr} has the better record ({better.record}) but the "
            f"market gives them {p_better:.0%} vs {worse.abbr}'s {p_worse:.0%}.",
        )
    return FlagResult(False, side, "Market agrees with the records.")
