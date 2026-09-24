# Sports Odds Research Tool

Shows a day's MLB games and flags the ones where **the team with the better record is priced as the underdog** — a fast way to spot games where the betting market disagrees with team quality.

Game and record data is **real** (ESPN's public API). Betting odds are **mocked**, and labelled as such everywhere they appear.

```
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠ Odds are MOCKED for demonstration. Game and record data is live      │
│   from ESPN.                                                           │
└────────────────────────────────────────────────────────────────────────┘

16 games · 3 flagged

TIME (ET)  AWAY                      HOME              ODDS      IMPLIED %   FLAG
1:05 PM    Chicago Cubs              Boston Red Sox    +120/-140 45.5/58.3   ⚠ Favorite Undervalued
           87-71 · 55.1%             85-73 · 53.8%
6:40 PM    Pittsburgh Pirates        Detroit Tigers    -110/-110 52.4/52.4   —
           80-78 · 50.6%             74-85 · 46.5%
```

---

## Quick start

```bash
python -m venv .venv
.venv/Scripts/activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000> and set the date to **2026-09-25** — 16 games, 3 flagged, including a doubleheader. No API key required.

| URL | What |
|---|---|
| <http://localhost:8000> | the UI |
| <http://localhost:8000/api/games?date=2026-09-25> | raw JSON |
| <http://localhost:8000/docs> | interactive API docs (generated) |
| <http://localhost:8000/health> | liveness check |

```bash
pytest -q        # 40 tests, no network access required
```

Requires **Python 3.10+**. Docker and Vercel setups are described under [Deployment](#deployment).

---

## Where to start reading

If you only read one file, read **[`app/flags.py`](app/flags.py)** (60 lines). It is the entire product; everything else feeds it.

| # | File | Lines | What it does |
|---|---|---|---|
| 1 | **[`app/flags.py`](app/flags.py)** | 60 | **The signal.** Converts odds to probabilities and decides whether to flag. Pure functions, no I/O. |
| 2 | [`app/models.py`](app/models.py) | 43 | The four dataclasses everything else passes around. |
| 3 | [`app/normalize.py`](app/normalize.py) | 89 | ESPN's JSON → clean `Game` objects. All the defensive parsing lives here. |
| 4 | [`app/odds_mock.py`](app/odds_mock.py) | 69 | Generates deterministic fake odds. |
| 5 | [`app/espn_client.py`](app/espn_client.py) | 34 | One HTTP call, one error type. |
| 6 | [`app/main.py`](app/main.py) | 92 | FastAPI routes; wires the above together. |
| 7 | [`app/config.py`](app/config.py) | 27 | Every tuning knob, in one place. |
| 8 | [`static/index.html`](static/index.html) | 224 | The whole frontend. No framework, no build step. |

**[`tests/test_flags.py`](tests/test_flags.py)** is the best summary of what the tool actually guarantees — 12 tests covering the edge cases below.

---

## The logic

Two independent opinions about the same game, converted to a common unit and compared.

```
RECORDS                                    ODDS
87-71 ─────────────────┐            ┌───────────────── +120
                       │            │
            87 ÷ 158   │            │   100 ÷ (120+100)
             = 55.1%   │            │   = 45.5%
                       ▼            ▼
                  ┌──────────────────────┐
                  │ both now percentages │
                  │   → comparable       │
                  └──────────────────────┘
                              │
        better team's % < worse team's %  →  ⚠ FLAG
```

**Ranking.** MLB has no official ranking, so the better team is the one with the higher season win percentage (`wins ÷ games played`), read from ESPN's season-total record.

**Implied probability.** Negative odds `-X → X/(X+100)`; positive `+X → 100/(X+100)`. So `-150` implies 60%, `+130` implies 43%.

**The flag.** Fires when the higher-ranked team's implied probability is *strictly lower* than its opponent's. A real example the tool produced:

> **CHC has the better record (87-71) but the market gives them 45% vs BOS's 58%.**

### Edge cases

These are deliberate decisions, not oversights:

| Case | Result | Reasoning |
|---|---|---|
| Equal win percentages | not flagged | There is no "better" team to undervalue |
| Equal odds (pick'em) | not flagged | Comparison is strict `<`; the market has taken no view |
| Missing record or odds | **`null`** (N/A) | A data gap must never render as "checked and fine" |
| Team with a 0-0 record | **`null`** (N/A) | No win percentage exists; avoids dividing by zero |
| Bookmaker margin (vig) | not removed | It scales both sides equally, so it cannot change which is larger — and displayed odds stay the ones a book would post |

The `null`-vs-`false` distinction is guarded by its own test (`test_na_is_distinguishable_from_false`), because collapsing the two is the easy bug here and it would silently mislead.

---

## Architecture

```
ESPN API → espn_client → normalize → odds provider → flags → /api/games → index.html
  (real)     (fetch)      (→ Game)      (mock)      (compute)   (JSON)      (render)
```

Each stage has one job. Three things this buys:

- **`flags.py` never sees raw ESPN JSON.** It takes clean `Game` objects, so the most heavily reviewed logic is pure and testable with three-line made-up inputs — no fixtures, no network.
- **The odds provider is swappable.** Write `odds_real.py` exposing `get_odds(game, date) -> Odds | None` and point `main.py` at it. `flags.py` and the UI are untouched.
- **Messy upstream data is contained** in `normalize.py` alone. If ESPN changes shape, exactly one file cares.

```
app/                 the pipeline (see table above)
static/index.html    single-page UI
tests/               40 tests
  fixtures/          a real saved ESPN response
api/index.py         Vercel serverless entrypoint
Dockerfile           multi-stage build, non-root, healthcheck
docker-compose.*.yml dev and prod stacks
```

---

## API

### `GET /api/games?date=YYYY-MM-DD`

Date defaults to today. Returns games with odds, implied probabilities and flags.

```json
{
  "date": "2026-09-25",
  "league": "MLB",
  "odds_source": "mock",
  "count": 16,
  "flagged_count": 3,
  "games": [
    {
      "id": "401817104",
      "start_time": "2026-09-25T17:05Z",
      "status": "Scheduled",
      "away": { "abbr": "CHC", "name": "Chicago Cubs", "record": "87-71",
                "wins": 87, "losses": 71, "win_pct": 0.5506 },
      "home": { "abbr": "BOS", "name": "Boston Red Sox", "record": "85-73",
                "wins": 85, "losses": 73, "win_pct": 0.5380 },
      "odds":    { "away": 120, "home": -140, "source": "mock" },
      "implied": { "away": 0.4545, "home": 0.5833 },
      "flag": {
        "favorite_undervalued": true,
        "higher_ranked": "away",
        "reason": "CHC has the better record (87-71) but the market gives them 45% vs BOS's 58%."
      }
    }
  ]
}
```

| Code | When | Body |
|---|---|---|
| `400` | Bad date format | `{"detail": "Invalid date. Use YYYY-MM-DD."}` |
| `502` | ESPN unreachable or returned junk | `{"detail": "Couldn't reach the sports data provider. Try again."}` |

---

## Verifying it works

Rather than taking the flag on trust, you can re-derive it:

```bash
# 1. Hand-check one game's arithmetic
curl -s "http://localhost:8000/api/games?date=2026-09-25" | python -m json.tool | head -40
#    CHC 87/158 = .551 (better) priced +120 → 100/220 = 45.5%
#    BOS 85/158 = .538           priced -140 → 140/240 = 58.3%
#    better team implied lower → flagged ✓

# 2. Confirm the odds are deterministic
curl -s ".../api/games?date=2026-09-25" > a.json
curl -s ".../api/games?date=2026-09-25" > b.json
diff a.json b.json          # identical

# 3. Run the edge cases
pytest tests/test_flags.py -v
```

Test coverage: **40 tests** — 12 flag logic, 10 mock odds, 9 normalization, 9 API. No network required; upstream is stubbed and a real ESPN response is saved as a fixture.

---

## Mock odds

Realistic enough to be plausible, imperfect enough to actually produce disagreements, and reproducible so a demo gives the same answer every run.

Per game: seed a RNG from `sha256(date:game_id)` → log5 base probability from both win percentages → `+0.04` home-field bump → gaussian noise → clamp to `[0.25, 0.75]` → scale to a 4.5% overround → convert to American odds rounded to 5.

Python's built-in `hash()` is deliberately **not** used: it is salted per process, so odds would change on every restart.

**Noise σ = 0.08** ([`config.NOISE_SD`](app/config.py)). Measured across five dates on a 12-game slate this averages **2.8 flags per slate**, inside the 2–4 target. Raising σ further does not help: past ≈0.10 the `[0.25, 0.75]` clamp binds and extra noise pins probabilities to the rails rather than producing more flips.

### Why not ESPN's own odds?

ESPN's response *does* contain real DraftKings odds — but **only for games happening today**. Checked against four other dates (a future date, two postseason dates, and an opening-week date), every one returned zero odds blocks. A real-odds version would work for a single day and show blank columns for every other date, making the date picker useless.

This is the reason the mock exists, and it is why the provider interface matters: a paid odds API drops in without touching the flag logic.

---

## Error handling

| Scenario | Behaviour |
|---|---|
| ESPN timeout, network error, non-2xx, bad JSON | `502` with a friendly message; logged |
| **One malformed game** | **Skipped and logged; the rest of the slate still renders** |
| No games on that date | `200` with an empty list → "No games scheduled for this date." |
| Team with a 0-0 record | `win_pct = null` → flag N/A |
| Invalid date parameter | `400`, validated *before* any network call |

Every one of these has a test. `2026-12-25` is a real date with no MLB games, useful for demoing the empty state without mocking anything.

Team names come from an external API and are inserted with `textContent`, never `innerHTML`.

---

## Deployment

### Docker

Separate dev and prod stacks. Host port is configurable via `WEB_PORT` (port 8000 is often already taken).

```bash
# Development: source bind-mounted, hot reload
docker compose -f docker-compose.dev.yml up --build

# Run the test suite inside the shipped image
docker compose -f docker-compose.dev.yml run --rm test

# Production: baked image, read-only filesystem, resource limits
docker compose -f docker-compose.prod.yml up --build -d

WEB_PORT=8100 docker compose -f docker-compose.prod.yml up -d   # different port
```

| | Dev | Prod |
|---|---|---|
| Source | bind-mounted, read-only | baked into the image |
| Reload | `--reload` on | off |
| Filesystem | writable | read-only |
| Extras | `test` service | restart policy, CPU/memory limits |

Both use the same multi-stage [`Dockerfile`](Dockerfile): builder compiles wheels, runtime carries only the installed packages. Runs as non-root (`appuser`, uid 1000), healthcheck on `/health`, final image **278 MB**.

### Vercel

```bash
vercel          # preview deployment
vercel --prod   # production
```

[`api/index.py`](api/index.py) exposes the ASGI app; [`vercel.json`](vercel.json) routes everything to it.

**One caveat:** Vercel's free tier has a 10-second function timeout. The 5s ESPN timeout plus a 1–3s cold start fits, but not comfortably — a slow upstream response would produce a hard `504` that bypasses the friendly `502` page. A container host avoids this.

---

## Documentation

| File | For whom |
|---|---|
| **[NON_TECH_GUIDE.md](NON_TECH_GUIDE.md)** | Anyone. Explains betting odds, the flag logic, and every calculation from scratch — no background assumed. Every figure verified against a live run. |
| [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) | Architecture and module-level detail. |
| [PRD.md](PRD.md) | Product requirements, scope, and build plan. |
| [GENERAL_GUIDE.md](GENERAL_GUIDE.md) | Earlier non-technical overview, superseded by NON_TECH_GUIDE.md. |

---

## Known limitations

- **ESPN's endpoint is unofficial** and can change without notice. All field paths were verified against a live response and that response is saved as a fixture, so the suite keeps passing even if the API moves.
- **Odds are mocked.** The flags demonstrate the logic; they are not real betting signals.
- **Win percentage is a crude quality measure.** It ignores injuries, schedule strength and — significantly in baseball — the starting pitcher, which can swing a game's real odds more than a ten-game difference in record.
- **No caching**: one upstream request per page load.
- **Not betting advice.** A flag means "this looks unusual", not "bet this".
- `today` uses the server's local date, while ESPN's day boundaries follow US time.

---

## What I'd do next

1. **Real odds** behind the existing provider interface, matching games on team and start time.
2. **Caching** — a ~5 minute TTL on scoreboard responses.
3. **Better ratings** — run differential, Pythagorean win %, or Elo instead of raw win %. This addresses the biggest weakness above.
4. **More leagues** — parameterise the ESPN path. College football is the interesting one: it has real AP rankings, so no win-% proxy is needed.
5. **Backtesting** — store daily flags and measure how flagged games actually resolved. This is what would turn the tool from a highlighter into something with a track record.
