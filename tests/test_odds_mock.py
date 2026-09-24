"""Tests for the mock odds generator: determinism and correct conversion."""

import pytest

from app.flags import implied_prob
from app.models import Game, Team
from app.odds_mock import mock_odds, prob_to_american


def game(gid: str = "g1", home_pct: float | None = 0.6,
         away_pct: float | None = 0.4) -> Game:
    mk = lambda a, p: Team(id=a, name=a, abbr=a, record="80-80",
                           wins=None, losses=None, win_pct=p)
    return Game(id=gid, start_time="", status="", 
                home=mk("HOM", home_pct), away=mk("AWY", away_pct))


# --- conversion -------------------------------------------------------------

def test_prob_to_american_favorite():
    assert prob_to_american(0.6) == -150


def test_prob_to_american_underdog():
    assert prob_to_american(0.4) == 150


def test_round_trip_is_stable():
    """Converting a probability to odds and back should land close to home."""
    for p in (0.3, 0.45, 0.5, 0.55, 0.7):
        assert implied_prob(prob_to_american(p)) == pytest.approx(p, abs=0.01)


def test_impossible_probabilities_rejected():
    with pytest.raises(ValueError):
        prob_to_american(0.0)
    with pytest.raises(ValueError):
        prob_to_american(1.0)


# --- determinism ------------------------------------------------------------

def test_same_date_and_game_give_same_odds():
    a = mock_odds(game(), "2026-09-24")
    b = mock_odds(game(), "2026-09-24")
    assert (a.home, a.away) == (b.home, b.away)


def test_different_dates_give_different_odds():
    a = mock_odds(game(), "2026-09-24")
    b = mock_odds(game(), "2026-09-25")
    assert (a.home, a.away) != (b.home, b.away)


def test_different_games_give_different_odds():
    a = mock_odds(game("g1"), "2026-09-24")
    b = mock_odds(game("g2"), "2026-09-24")
    assert (a.home, a.away) != (b.home, b.away)


# --- behaviour --------------------------------------------------------------

def test_source_is_labelled_mock():
    assert mock_odds(game(), "2026-09-24").source == "mock"


def test_missing_win_pct_still_produces_odds():
    """A coin-flip base, rather than a crash, when records are unknown."""
    odds = mock_odds(game(home_pct=None, away_pct=None), "2026-09-24")
    assert isinstance(odds.home, int) and isinstance(odds.away, int)


def test_stronger_team_is_usually_favoured():
    """Noise makes this probabilistic, so assert the tendency over a sample."""
    favoured = 0
    for i in range(60):
        o = mock_odds(game(f"g{i}", home_pct=0.700, away_pct=0.300), "2026-09-24")
        favoured += implied_prob(o.home) > implied_prob(o.away)
    assert favoured > 45
