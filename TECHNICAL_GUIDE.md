# Technical Guide: Sports Odds Research Tool

This guide explains how the prototype is built. It covers the architecture, the modules, the data contracts, the core algorithms, error handling, and testing. For the product requirements, see [`PRD.md`](./PRD.md). For a non-technical overview, see [`GENERAL_GUIDE.md`](./GENERAL_GUIDE.md).

---

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Fast to write, readable, good HTTP and test tooling |
| Web framework | FastAPI | Minimal boilerplate, automatic docs at `/docs`, easy JSON |
| HTTP client | `httpx` | Clean timeout handling, sync and async support |
| Frontend | One `index.html` with vanilla JS | No build step; the brief asks for no design polish |
| Tests | `pytest` | Standard and simple |
| Server | `uvicorn` | The standard ASGI server for FastAPI |

`requirements.txt`:
```
fastapi
uvicorn
httpx
pytest
```

---

## 2. Architecture

### Data flow

```
┌───────────────┐   ┌──────────────┐   ┌──────────────┐   ┌───────────┐   ┌──────────┐   ┌────────────┐
│ ESPN          │──▶│ espn_client  │──▶│ normalize    │──▶│ odds      │──▶│ flags    │──▶│ /api/games │──▶ index.html
│ Scoreboard API│   │ (fetch raw)  │   │ (→ Game objs)│   │ provider  │   │ (compute)│   │ (JSON)     │
└───────────────┘   └──────────────┘   └──────────────┘   └───────────┘   └──────────┘   └────────────┘
      REAL                                                     MOCK
```

Each stage has one job and passes a clean result to the next one. This separation matters for three reasons:

- The **flag logic never touches raw ESPN JSON.** It only sees clean `Game` objects, so it is easy to test.
- The **odds provider can be swapped** from mock to real without changing any other module.
- **Messy upstream data is handled in one place** (`normalize.py`).

### Project layout

```
odds-research-tool/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes, static file serving
│   ├── config.py        # Constants: URLs, timeout, vig
│   ├── models.py        # Team, Odds, Game, FlagResult dataclasses
│   ├── espn_client.py   # HTTP fetch with timeout and error wrapping
│   ├── normalize.py     # ESPN JSON → list[Game]
│   ├── odds_mock.py     # Deterministic mock odds generator
│   └── flags.py         # implied_prob() and favorite_undervalued()
├── static/
│   └── index.html
├── tests/
│   ├── fixtures/
│   │   └── scoreboard_sample.json   # Saved real ESPN response
│   ├── test_flags.py
│   ├── test_normalize.py
│   └── test_odds_mock.py
├── requirements.txt
├── PRD.md
├── TECHNICAL_GUIDE.md
├── GENERAL_GUIDE.md
└── README.md
```

---

## 3. Data Source: ESPN Scoreboard

**Endpoint** (no API key needed):
```
GET https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=YYYYMMDD
```

Note the date format: the API expects `YYYYMMDD` with no dashes. The app accepts `YYYY-MM-DD` from users and converts it.

**Fields to extract.** This is an unofficial, undocumented API, so **confirm these paths against a live response in milestone M0** and save that response as a test fixture.

| Field | Typical path |
|---|---|
| Games list | `events[]` |
| Game ID | `events[i].id` |
| Start time (UTC ISO) | `events[i].date` |
| Status | `events[i].status.type.state` (`pre` / `in` / `post`) and `.detail` |
| Competitors | `events[i].competitions[0].competitors[]` |
| Home/away | `competitor.homeAway` |
| Team ID / name / abbr | `competitor.team.id`, `.displayName`, `.abbreviation` |
| Overall record | `competitor.records[]`, the entry with `type == "total"` (or `name == "overall"`), then `.summary`, for example `"85-70"` |

The scoreboard response sometimes includes an `odds` block under `competitions[0]`. The prototype deliberately **does not rely on it**, because its availability is inconsistent. The mock provider is used instead, and this is noted as a possible future data source.

---

## 4. Data Model (`models.py`)

```python
from dataclasses import dataclass

@dataclass
class Team:
    id: str
    name: str
    abbr: str
    record: str | None        # "85-70"
    wins: int | None
    losses: int | None
    win_pct: float | None     # None if no games played or record missing

@dataclass
class Odds:
    home: int                 # American moneyline, e.g. -150
    away: int                 # e.g. +130
    source: str               # "mock" or provider name

@dataclass
class FlagResult:
    favorite_undervalued: bool | None   # None = N/A
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
```

---

## 5. Modules

### 5.1 `espn_client.py`

Its only job is to get raw JSON, or raise one clear error.

```python
import httpx
from app.config import ESPN_SCOREBOARD_URL, HTTP_TIMEOUT_SECONDS

class UpstreamError(Exception):
    """Raised when the sports data provider can't be reached or returns bad data."""

def fetch_scoreboard(date_yyyymmdd: str) -> dict:
    try:
        resp = httpx.get(ESPN_SCOREBOARD_URL,
                         params={"dates": date_yyyymmdd},
                         timeout=HTTP_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError(f"ESPN request failed: {exc}") from exc
```

### 5.2 `normalize.py`

This module converts raw JSON into `list[Game]`. **Rule: one bad game never breaks the whole list.**

```python
import logging
from app.models import Game, Team

log = logging.getLogger(__name__)

def parse_record(summary: str | None) -> tuple[int | None, int | None, float | None]:
    if not summary:
        return None, None, None
    try:
        wins, losses = (int(x) for x in summary.split("-")[:2])
    except ValueError:
        return None, None, None
    played = wins + losses
    return wins, losses, (wins / played if played else None)

def _overall_record(competitor: dict) -> str | None:
    for rec in competitor.get("records", []):
        if rec.get("type") == "total" or rec.get("name") == "overall":
            return rec.get("summary")
    return None

def _team(competitor: dict) -> Team:
    t = competitor["team"]
    summary = _overall_record(competitor)
    wins, losses, pct = parse_record(summary)
    return Team(id=str(t["id"]), name=t.get("displayName", "Unknown"),
                abbr=t.get("abbreviation", ""), record=summary,
                wins=wins, losses=losses, win_pct=pct)

def normalize_scoreboard(raw: dict) -> list[Game]:
    games = []
    for event in raw.get("events", []):
        try:
            comp = event["competitions"][0]
            by_side = {c["homeAway"]: c for c in comp["competitors"]}
            games.append(Game(
                id=str(event["id"]),
                start_time=event.get("date", ""),
                status=event.get("status", {}).get("type", {}).get("detail", "Unknown"),
                home=_team(by_side["home"]),
                away=_team(by_side["away"]),
            ))
        except (KeyError, IndexError, TypeError) as exc:
            log.warning("Skipping malformed event %s: %s", event.get("id"), exc)
    return games
```

### 5.3 `odds_mock.py`: the mock odds algorithm

The goal is odds that look **realistic but not perfect**, so some games naturally produce the flag, and results are **reproducible** from run to run.

**Algorithm, per game:**

1. **Seed:** `sha256(f"{date}:{game_id}")` → integer → `random.Random(seed)`.
   Python's built-in `hash()` is randomized per process, so it is not used.
2. **Base probability** that the home team wins, using the **log5** formula on win %:
   `p = (pH − pH·pA) / (pH + pA − 2·pH·pA)`
   If either win % is missing, start at `0.5`.
3. **Home-field bump:** `+0.04`.
4. **Market noise:** add `gauss(0, 0.08)`, then clamp to `[0.25, 0.75]`.
   This noise is what creates the "market disagrees" cases.
5. **Add vig:** scale both sides so they sum to `1.045` (a 4.5% overround).
6. **Convert to American odds** and round to the nearest 5:
   - If `p ≥ 0.5`: `−100 · p / (1 − p)`
   - If `p < 0.5`: `+100 · (1 − p) / p`

```python
import hashlib, random
from app.models import Game, Odds

VIG = 1.045

def _seeded_rng(date: str, game_id: str) -> random.Random:
    digest = hashlib.sha256(f"{date}:{game_id}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))

def _log5(p_a: float, p_b: float) -> float:
    denom = p_a + p_b - 2 * p_a * p_b
    return 0.5 if denom == 0 else (p_a - p_a * p_b) / denom

def prob_to_american(p: float) -> int:
    raw = -100 * p / (1 - p) if p >= 0.5 else 100 * (1 - p) / p
    return int(round(raw / 5) * 5)

def mock_odds(game: Game, date: str) -> Odds:
    rng = _seeded_rng(date, game.id)
    ph, pa = game.home.win_pct, game.away.win_pct
    base = _log5(ph, pa) if ph is not None and pa is not None else 0.5
    p_home = min(0.75, max(0.25, base + 0.04 + rng.gauss(0, 0.08)))
    home_vig = min(p_home * VIG, 0.95)
    away_vig = min((1 - p_home) * VIG, 0.95)
    return Odds(home=prob_to_american(home_vig),
                away=prob_to_american(away_vig),
                source="mock")
```

**Tuning:** if too few games are flagged in the demo, raise the noise standard deviation. If too many are flagged, lower it. Record the chosen value in the README.

### 5.4 `flags.py`: the core logic

```python
from app.models import Game, FlagResult

def implied_prob(american: int) -> float:
    """Convert American moneyline odds to implied win probability (0–1)."""
    if american < 0:
        return -american / (-american + 100)
    return 100 / (american + 100)

def favorite_undervalued(game: Game) -> FlagResult:
    h, a = game.home, game.away
    if h.win_pct is None or a.win_pct is None:
        return FlagResult(None, None, "Missing team record.")
    if game.odds is None:
        return FlagResult(None, None, "Missing odds.")
    if h.win_pct == a.win_pct:
        return FlagResult(False, None, "Teams have equal records.")

    side = "home" if h.win_pct > a.win_pct else "away"
    better_odds = game.odds.home if side == "home" else game.odds.away
    worse_odds  = game.odds.away if side == "home" else game.odds.home
    p_better, p_worse = implied_prob(better_odds), implied_prob(worse_odds)
    better = h if side == "home" else a

    if p_better < p_worse:
        return FlagResult(True, side,
            f"{better.abbr} has the better record but the market gives them "
            f"{p_better:.0%} vs {p_worse:.0%}.")
    return FlagResult(False, side, "Market agrees with the records.")
```

**Design notes:**
- **Strict `<`:** equal implied probabilities (a pick'em) do not flag.
- **N/A is `None`, not `False`:** missing data should never look like "checked and fine."
- **The vig is not removed:** removing it rescales both sides by the same factor, so which side is larger never changes. The raw (vigged) implied probabilities are displayed, and this is noted in the UI tooltip.

### 5.5 `main.py`: the API

```python
from datetime import date, datetime
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.espn_client import fetch_scoreboard, UpstreamError
from app.normalize import normalize_scoreboard
from app.odds_mock import mock_odds
from app.flags import favorite_undervalued, implied_prob

app = FastAPI(title="Sports Odds Research Tool")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/games")
def get_games(date_str: str = Query(default=None, alias="date")):
    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        raise HTTPException(400, "Invalid date. Use YYYY-MM-DD.")

    try:
        raw = fetch_scoreboard(day.strftime("%Y%m%d"))
    except UpstreamError:
        raise HTTPException(502, "Couldn't reach the sports data provider. Try again.")

    games = normalize_scoreboard(raw)
    out = []
    for g in games:
        g.odds = mock_odds(g, day.isoformat())
        g.flag = favorite_undervalued(g)
        item = asdict(g)
        item["implied"] = {"home": implied_prob(g.odds.home),
                           "away": implied_prob(g.odds.away)}
        out.append(item)

    return {
        "date": day.isoformat(),
        "league": "MLB",
        "odds_source": "mock",
        "count": len(out),
        "flagged_count": sum(1 for g in out if g["flag"]["favorite_undervalued"]),
        "games": out,
    }
```

---

## 6. API Contract

### `GET /api/games?date=YYYY-MM-DD`

**200 OK**
```json
{
  "date": "2026-09-24",
  "league": "MLB",
  "odds_source": "mock",
  "count": 12,
  "flagged_count": 3,
  "games": [
    {
      "id": "401696123",
      "start_time": "2026-09-24T23:05Z",
      "status": "7:05 PM ET",
      "home": { "id": "10", "name": "New York Yankees", "abbr": "NYY",
                "record": "90-66", "wins": 90, "losses": 66, "win_pct": 0.577 },
      "away": { "id": "2", "name": "Baltimore Orioles", "abbr": "BAL",
                "record": "78-78", "wins": 78, "losses": 78, "win_pct": 0.5 },
      "odds": { "home": 115, "away": -135, "source": "mock" },
      "implied": { "home": 0.465, "away": 0.574 },
      "flag": { "favorite_undervalued": true, "higher_ranked": "home",
                "reason": "NYY has the better record but the market gives them 47% vs 57%." }
    }
  ]
}
```
*(Illustrative values only.)*

| Code | When | Body |
|---|---|---|
| `400` | Bad date format | `{"detail": "Invalid date. Use YYYY-MM-DD."}` |
| `502` | ESPN unreachable or invalid | `{"detail": "Couldn't reach the sports data provider. Try again."}` |

FastAPI also provides interactive docs at **`/docs`**.

---

## 7. Frontend (`static/index.html`)

It is a single file with no framework and no build step.

**Behavior:**
1. On load, it reads the date picker (default: today) and calls `fetch('/api/games?date=...')`.
2. While waiting, it shows "Loading games…"
3. On success, it renders a summary line ("12 games · 3 flagged") and a table.
4. Flagged rows get a `flagged` CSS class (highlighted background) and a ⚠ badge. The `reason` string appears as a tooltip.
5. `null` flags render as a grey "N/A" badge.
6. On an empty list, it shows "No games scheduled for this date."
7. On an error, it shows the `detail` message from the API.
8. A fixed banner reads: **"⚠ Odds are MOCKED for demonstration. Game and record data is live from ESPN."**

**Table columns:** Time · Away (record, win %) · Home (record, win %) · Odds (away / home) · Implied % (away / home) · Flag

**Security note:** team names come from an external API, so insert them with `textContent`, not `innerHTML`.

---

## 8. Error Handling Summary

| Layer | Failure | Handling |
|---|---|---|
| `espn_client` | Timeout, connection error, non-2xx, invalid JSON | Raise `UpstreamError` → API `502` |
| `normalize` | Malformed event | Skip the event and log a warning |
| `normalize` | Missing or unparseable record | `win_pct = None` → flag N/A |
| `normalize` | 0–0 record | `win_pct = None` → flag N/A |
| `main` | Bad date | `400` |
| `index.html` | Any non-200 response | Show the error state; never a blank page |

---

## 9. Testing

Run with `pytest -q`.

### `test_flags.py`

| Case | Setup | Expected |
|---|---|---|
| Implied prob, negative | `-150` | `0.600` |
| Implied prob, positive | `+130` | `≈ 0.4348` |
| Implied prob, even | `+100` | `0.500` |
| Flag fires | Better team at `+120`, worse at `-140` | `True` |
| Flag does not fire | Better team at `-150`, worse at `+130` | `False` |
| Tie in records | Equal win % | `False`, reason mentions equal records |
| Pick'em odds | Both `-110`, different records | `False` (strict comparison) |
| Missing record | `win_pct = None` | `None` |
| Missing odds | `odds = None` | `None` |
| Better team is away | Away has the higher win % and worse odds | `True`, `higher_ranked == "away"` |

### `test_normalize.py`
- The saved fixture parses into the expected number of games, with the correct names and records.
- An event missing `competitors` is skipped, and the others still parse.
- `parse_record("85-70")` returns `(85, 70, 0.548…)`; `parse_record(None)` returns Nones; `parse_record("0-0")` gives win % `None`.

### `test_odds_mock.py`
- The same date and game always produce the same odds (deterministic).
- A different date produces different odds.
- `prob_to_american(0.6)` returns `-150`; `prob_to_american(0.4)` returns `+150`.
- A round-trip check: `implied_prob(prob_to_american(p))` is close to `p`, allowing for rounding.

---

## 10. Running Locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:
- `http://localhost:8000`: the UI
- `http://localhost:8000/api/games?date=2026-09-24`: raw JSON
- `http://localhost:8000/docs`: interactive API docs

---

## 11. Extending the Prototype

**Swap in real odds.** Create `odds_real.py` with a function of the same shape, `get_odds(game, date) -> Odds | None`. Match games to odds-API events by team name and start time, then select the provider in `config.py`. No changes are needed in `flags.py` or the UI.

**Add a league.** Parameterize the ESPN path (`baseball/mlb` → `football/nfl`, `football/college-football`, and so on). For college football, use the AP rank field in the response as the ranking instead of win %.

**Add caching.** Wrap `fetch_scoreboard` with a small in-memory TTL cache (about 5 minutes) keyed by date.

---

## 12. Known Limitations

- ESPN's endpoint is **unofficial**. Its shape can change without notice.
- **Win % is a crude quality measure.** It ignores schedule strength, injuries, and starting pitchers, which matter a lot in baseball.
- **Odds are mocked**, so the flags demonstrate the logic only. They are not real betting signals.
- There is **no caching**, so each page load triggers one upstream request.
- Timezone handling: "today" uses the server's local date. ESPN's day boundaries are based on US time.
