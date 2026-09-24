"""API-level tests. Upstream is stubbed so these never touch the network."""

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from app import main
from app.espn_client import UpstreamError

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "scoreboard_sample.json"
client = TestClient(main.app)


@pytest.fixture
def stub_espn(monkeypatch):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    monkeypatch.setattr(main, "fetch_scoreboard", lambda d: raw)
    return raw


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_serves_page_with_mock_banner():
    r = client.get("/")
    assert r.status_code == 200
    assert "MOCKED" in r.text


def test_games_contract(stub_espn):
    r = client.get("/api/games?date=2026-09-24")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == "2026-09-24"
    assert body["league"] == "MLB"
    assert body["odds_source"] == "mock"
    assert body["count"] == 12
    assert len(body["games"]) == 12

    g = body["games"][0]
    assert {"id", "start_time", "status", "home", "away", "odds", "flag", "implied"} <= set(g)
    assert g["odds"]["source"] == "mock"
    assert 0 < g["implied"]["home"] < 1


def test_bad_date_returns_400():
    r = client.get("/api/games?date=banana")
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid date. Use YYYY-MM-DD."


def test_upstream_failure_returns_502(monkeypatch):
    def boom(_):
        raise UpstreamError("simulated outage")
    monkeypatch.setattr(main, "fetch_scoreboard", boom)
    r = client.get("/api/games?date=2026-09-24")
    assert r.status_code == 502
    assert "provider" in r.json()["detail"]


def test_empty_slate_is_200_not_an_error(monkeypatch):
    monkeypatch.setattr(main, "fetch_scoreboard", lambda d: {"events": []})
    r = client.get("/api/games?date=2026-12-25")
    assert r.status_code == 200
    assert r.json()["count"] == 0
    assert r.json()["games"] == []


def test_malformed_game_does_not_break_the_slate(monkeypatch):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["events"][0]["competitions"][0].pop("competitors")
    monkeypatch.setattr(main, "fetch_scoreboard", lambda d: raw)
    r = client.get("/api/games?date=2026-09-24")
    assert r.status_code == 200
    assert r.json()["count"] == 11


def test_flagged_count_counts_only_true(stub_espn):
    body = client.get("/api/games?date=2026-09-24").json()
    expected = sum(
        1 for g in body["games"] if g["flag"]["favorite_undervalued"] is True
    )
    assert body["flagged_count"] == expected


def test_results_are_reproducible(stub_espn):
    a = client.get("/api/games?date=2026-09-24").json()
    b = client.get("/api/games?date=2026-09-24").json()
    assert a == b
