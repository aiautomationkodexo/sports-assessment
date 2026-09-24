"""Tests for the core flag logic -- the most heavily reviewed code here."""

import pytest

from app.flags import favorite_undervalued, implied_prob
from app.models import FlagResult, Game, Odds, Team


def team(abbr: str, win_pct: float | None, record: str = "80-80") -> Team:
    return Team(
        id="1", name=abbr, abbr=abbr, record=record,
        wins=None, losses=None, win_pct=win_pct,
    )


def game(home_pct, away_pct, home_odds=None, away_odds=None) -> Game:
    odds = (
        Odds(home=home_odds, away=away_odds, source="mock")
        if home_odds is not None
        else None
    )
    return Game(
        id="g1", start_time="", status="Scheduled",
        home=team("HOM", home_pct), away=team("AWY", away_pct), odds=odds,
    )


# --- implied_prob -----------------------------------------------------------

def test_implied_prob_negative_odds():
    assert implied_prob(-150) == pytest.approx(0.600)


def test_implied_prob_positive_odds():
    assert implied_prob(130) == pytest.approx(0.4348, abs=1e-4)


def test_implied_prob_even_money():
    assert implied_prob(100) == pytest.approx(0.500)
    assert implied_prob(-100) == pytest.approx(0.500)


# --- the flag itself --------------------------------------------------------

def test_flag_fires_when_better_team_is_the_underdog():
    # Home has the better record but is priced as the dog.
    result = favorite_undervalued(game(0.600, 0.400, home_odds=120, away_odds=-140))
    assert result.favorite_undervalued is True
    assert result.higher_ranked == "home"
    assert "HOM" in result.reason


def test_flag_silent_when_market_agrees():
    result = favorite_undervalued(game(0.600, 0.400, home_odds=-150, away_odds=130))
    assert result.favorite_undervalued is False
    assert result.higher_ranked == "home"


def test_flag_fires_for_the_away_team_too():
    # Away has the better record and the worse price.
    result = favorite_undervalued(game(0.400, 0.600, home_odds=-140, away_odds=120))
    assert result.favorite_undervalued is True
    assert result.higher_ranked == "away"
    assert "AWY" in result.reason


def test_equal_records_never_flag():
    result = favorite_undervalued(game(0.500, 0.500, home_odds=120, away_odds=-140))
    assert result.favorite_undervalued is False
    assert result.higher_ranked is None
    assert "equal records" in result.reason.lower()


def test_pickem_odds_do_not_flag():
    """Equal implied probabilities are not a disagreement: the test is strict."""
    result = favorite_undervalued(game(0.600, 0.400, home_odds=-110, away_odds=-110))
    assert result.favorite_undervalued is False


# --- missing data must be N/A, not False ------------------------------------

def test_missing_record_is_na_not_false():
    result = favorite_undervalued(game(None, 0.400, home_odds=120, away_odds=-140))
    assert result.favorite_undervalued is None
    assert result.higher_ranked is None


def test_missing_odds_is_na_not_false():
    result = favorite_undervalued(game(0.600, 0.400))
    assert result.favorite_undervalued is None
    assert "odds" in result.reason.lower()


def test_na_is_distinguishable_from_false():
    """Guards the design decision: None and False must not be conflated."""
    na = favorite_undervalued(game(None, 0.400, home_odds=120, away_odds=-140))
    no = favorite_undervalued(game(0.600, 0.400, home_odds=-150, away_odds=130))
    assert na.favorite_undervalued is None
    assert no.favorite_undervalued is False
    assert na.favorite_undervalued is not no.favorite_undervalued


def test_vig_does_not_change_the_verdict():
    """A uniform margin scales both sides, so it can't flip which is larger."""
    fair = favorite_undervalued(game(0.600, 0.400, home_odds=110, away_odds=-130))
    juiced = favorite_undervalued(game(0.600, 0.400, home_odds=105, away_odds=-140))
    assert fair.favorite_undervalued is juiced.favorite_undervalued is True
