# Sports Odds Research Tool

Shows a day's MLB games and flags the ones where **the team with the better record is priced as the underdog** — a quick way to spot games where the betting market disagrees with team quality.

Game and record data is **real** (ESPN's public API). Betting odds are **mocked**, and labelled as such everywhere they appear.

- **[PRD.md](PRD.md)** — product requirements
- **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** — architecture and module detail
- **[GENERAL_GUIDE.md](GENERAL_GUIDE.md)** — plain-English explanation, no technical background needed

---

## Run it

```bash
python -m venv .venv
.venv/Scripts/activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

| URL | What |
|---|---|
| <http://localhost:8000> | the UI |
| <http://localhost:8000/api/games?date=2026-09-25> | raw JSON |
| <http://localhost:8000/docs> | interactive API docs |

**Try `2026-09-25`** — 16 games, 3 flagged, including a doubleheader. No API key is needed.

Tests:

```bash
pytest -q        # 40 tests, no network access required
```

Requires **Python 3.10+** (the reference docs say 3.11; the `X | None` syntax used here landed in 3.10, and the suite passes on 3.10.10).

---

## How the flag works

1. **Rank the teams.** MLB has no official ranking, so the better team is the one with the higher season win percentage (`wins ÷ games played`), read from ESPN's season-total record.
2. **Convert odds to probabilities.** Negative odds `-X → X/(X+100)`; positive `+X → 100/(X+100)`. So `-150` implies 60%, `+130` implies 43%.
3. **Compare.** If the higher-ranked team's implied probability is *strictly lower* than its opponent's, the game is flagged.

Example from the demo date:

> **CHC has the better record (87-71) but the market gives them 45% vs BOS's 58%.**

### Deliberate edge-case decisions

| Case | Result | Why |
|---|---|---|
| Equal win percentages | not flagged | There is no "better" team to undervalue |
| Equal odds (pick'em) | not flagged | The comparison is strict `<` |
| Missing record or odds | **N/A** (`null`) | A data gap must never render as "checked and fine" |
| Bookmaker margin (vig) | not removed | It scales both sides by the same factor, so it cannot change which is larger — and the displayed numbers stay the ones a book would actually post |

The `null`-vs-`false` distinction is enforced by a test (`test_na_is_distinguishable_from_false`), because collapsing the two would be the easy bug here.

---

## Architecture

```
ESPN API → espn_client → normalize → odds provider → flags → /api/games → index.html
  (real)     (fetch)      (→ Game)      (mock)      (compute)   (JSON)      (render)
```

Each stage has one job. Three things this buys:

- **`flags.py` never sees raw ESPN JSON.** It takes clean `Game` objects, so the most heavily reviewed logic is pure and trivially testable.
- **The odds provider is swappable.** Write `odds_real.py` exposing `get_odds(game, date) -> Odds | None` and point `main.py` at it. `flags.py` and the UI are untouched.
- **Messy upstream data is contained** in `normalize.py` alone.

```
app/
  config.py        constants and every tuning knob
  models.py        Team, Odds, FlagResult, Game dataclasses
  espn_client.py   HTTP fetch; raises UpstreamError and nothing else
  normalize.py     ESPN JSON → list[Game]; skips malformed games
  odds_mock.py     deterministic mock odds
  flags.py         implied_prob() and favorite_undervalued()
  main.py          FastAPI routes
static/index.html  single-page UI, no build step
tests/             40 tests incl. a real saved ESPN response
```

---

## Mock odds

Realistic enough to be plausible, imperfect enough to actually produce disagreements, and reproducible so a demo gives the same answer every run.

Per game: seed a RNG from `sha256(date:game_id)` → log5 base probability from both win percentages → `+0.04` home-field bump → gaussian noise → clamp to `[0.25, 0.75]` → scale to a 4.5% overround → convert to American odds rounded to 5.

Python's built-in `hash()` is deliberately **not** used: it is salted per process, so odds would change on every restart.

**Noise σ = 0.08** (`config.NOISE_SD`). Measured across five dates on a 12-game slate this averages **2.8 flags per slate** — inside the 2–4 target. Raising σ further does not help: past ≈0.10 the `[0.25, 0.75]` clamp binds and extra noise just pins probabilities to the rails rather than producing more flips.

---

## Error handling

| Scenario | Behaviour |
|---|---|
| ESPN timeout, network error, non-2xx, bad JSON | `502` → "Couldn't reach the sports data provider. Try again." |
| One malformed game | Skipped and logged; **the rest of the slate still renders** |
| No games that date | `200` with an empty list → "No games scheduled for this date." |
| Team with a 0-0 record | `win_pct = null` → flag N/A |
| Invalid date parameter | `400` "Invalid date. Use YYYY-MM-DD." — validated before any network call |

Every one of these is covered by a test. `2026-12-25` is a real date with no games, useful for demoing the empty state without mocking anything.

Team names come from an external API and are inserted with `textContent`, never `innerHTML`.

---

## Known limitations

- **ESPN's endpoint is unofficial** and can change without notice. All field paths were verified against a live response on 2026-09-24 and that response is saved as a test fixture, so the suite keeps passing even if the API moves.
- **Odds are mocked.** The flags demonstrate the logic; they are not real betting signals.
- **Win percentage is a crude quality measure.** It ignores injuries, schedule strength and — significantly in baseball — the starting pitcher.
- **No caching**: one upstream request per page load.
- **Not betting advice.** A flag means "this looks unusual", not "bet this".
- `today` uses the server's local date, while ESPN's day boundaries follow US time.

---

## What I'd do next

1. **Real odds** behind the existing provider interface (The Odds API has a free tier), matching games on team and start time.
2. **Caching** — a ~5 minute TTL on scoreboard responses.
3. **Better ratings** — run differential, Pythagorean win %, or Elo instead of raw win %.
4. **More leagues** — parameterise the ESPN path. College football is the interesting one, since it has real AP rankings and needs no win-% proxy.
5. **Backtesting** — store daily flags and measure how flagged games actually resolved. This is what would turn the tool from a highlighter into something with a track record.
