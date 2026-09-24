"""Tests for parsing ESPN's JSON, including the malformed-game guarantee."""

import json
import pathlib

from app.normalize import normalize_scoreboard, parse_record

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "scoreboard_sample.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# --- parse_record -----------------------------------------------------------

def test_parse_record_normal():
    wins, losses, pct = parse_record("85-70")
    assert (wins, losses) == (85, 70)
    assert pct == 85 / 155


def test_parse_record_missing():
    assert parse_record(None) == (None, None, None)
    assert parse_record("") == (None, None, None)


def test_parse_record_zero_games_has_no_win_pct():
    """0-0 means "hasn't played", which is not the same as a 0% win rate."""
    wins, losses, pct = parse_record("0-0")
    assert (wins, losses) == (0, 0)
    assert pct is None


def test_parse_record_garbage():
    assert parse_record("not-a-record") == (None, None, None)
    assert parse_record("85") == (None, None, None)


# --- normalize_scoreboard ---------------------------------------------------

def test_fixture_parses_all_games():
    games = normalize_scoreboard(load_fixture())
    assert len(games) == 12
    for g in games:
        assert g.home.abbr and g.away.abbr
        assert g.home.win_pct is not None
        assert g.id


def test_fixture_has_expected_matchup():
    games = normalize_scoreboard(load_fixture())
    by_id = {g.id: g for g in games}
    g = by_id["401817063"]
    assert g.away.abbr == "STL"
    assert g.home.abbr == "PIT"
    assert g.home.record == "80-78"
    assert g.home.win_pct == 80 / 158


def test_uses_total_record_not_home_or_road():
    """ESPN returns total/home/road records; we must pick the season total."""
    games = normalize_scoreboard(load_fixture())
    pit = next(g.home for g in games if g.home.abbr == "PIT")
    assert pit.record == "80-78"   # not the 43-37 home split


def test_malformed_game_is_skipped_others_survive():
    raw = load_fixture()
    raw["events"][0]["competitions"][0].pop("competitors")
    games = normalize_scoreboard(raw)
    assert len(games) == 11


def test_empty_scoreboard_returns_empty_list():
    assert normalize_scoreboard({"events": []}) == []
    assert normalize_scoreboard({}) == []
