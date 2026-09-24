# PRD: Sports Odds Research Tool (Prototype)

| | |
|---|---|
| **Status** | Draft v1.0 |
| **Scope** | Take-home prototype (4–6 hour time box) |
| **League** | MLB (Major League Baseball) |
| **Stack** | Python 3.11+, FastAPI, plain HTML/JS |
| **Data** | ESPN public scoreboard API (real) + mock odds (clearly labeled) |

---

## 1. Summary

A small web tool that shows a given day's MLB games, attaches betting odds to each game, and flags games where the betting market disagrees with team quality. Specifically, the flag fires when the better team (by record) is priced as the underdog.

This is a thin slice of a larger research tool for sports bettors. The goal is a clean, working, well-explained prototype. It is not meant to be a production system.

## 2. Problem

Bettors look for games where the market's pricing seems "wrong." One simple signal is when the market favors the weaker team. Spotting this by hand means cross-checking standings against odds for every game on the slate. The tool automates that comparison and highlights the interesting games.

## 3. Goals and Non-Goals

### Goals
- **G1.** Retrieve a real day's games for one league from a live, free, public API.
- **G2.** Attach an odds signal to each game, labeled as mock where applicable.
- **G3.** Correctly compute and display the **Favorite Undervalued** flag.
- **G4.** Show results on a simple web page with flagged games visually highlighted.
- **G5.** Handle errors and missing data gracefully, without crashes or misleading output.
- **G6.** Keep the code easy for a reviewer to read, run, and follow.

### Non-Goals (explicitly out of scope)
- Real-money betting integration or real sportsbook accounts
- User accounts, authentication, or saved preferences
- Multiple leagues
- Team, player, or coach drill-down pages (future work)
- Database, caching layer, or deployment infrastructure
- Visual design polish
- Predictive modeling or betting recommendations

## 4. Target User

A **sports bettor** researching the day's slate who wants a fast, scannable list of games where the market pricing looks off relative to team quality.

For this prototype, the secondary audience is **the hiring reviewers**, who need to understand what was built and why.

## 5. Key Definitions and Assumptions

| Term | Definition used in this prototype |
|---|---|
| **Ranking** | MLB has no official ranking. **Higher-ranked = higher season win percentage** (wins ÷ games played), taken from each team's overall record in the ESPN response. |
| **Implied probability** | The win chance implied by American moneyline odds. Negative odds: `-X → X / (X + 100)`. Positive odds: `+X → 100 / (X + 100)`. |
| **Favorite Undervalued** | A game where the **higher-ranked team's implied probability is strictly lower** than the lower-ranked team's. |
| **Tie in ranking** | Equal win percentages mean there is no higher-ranked team, so the game is **not flagged**. |
| **Missing data** | If either team's record or the game's odds are missing, the flag is **N/A** (not "false"). This avoids hiding data gaps. |
| **Vig (bookmaker margin)** | Ignored for the flag. It inflates both sides' probabilities, so it does not change which one is larger. |
| **Mock odds** | Generated deterministically per date and game so results are reproducible. Always labeled "MOCK" in the UI and API. |

## 6. Functional Requirements

### FR1: Fetch games (real data)
- **FR1.1** The system fetches the MLB scoreboard from ESPN for a requested date (`YYYY-MM-DD`). The default is today.
- **FR1.2** For each game it extracts: game ID, start time, status, and for each team the ID, display name, abbreviation, home/away side, and overall record.
- **FR1.3** It computes each team's win percentage from the record.
- **FR1.4** Requests use a timeout of 5 seconds or less.

### FR2: Odds signal
- **FR2.1** Each game receives American moneyline odds for both teams.
- **FR2.2** Odds come from a pluggable **odds provider**. The default is a mock provider.
- **FR2.3** Mock odds are deterministic for the same date and game.
- **FR2.4** Mock odds are loosely based on team strength plus random noise, so that some games produce upsets and the flag can be demonstrated.
- **FR2.5** Every odds object carries `source: "mock"` or the real provider's name.

### FR3: Favorite Undervalued flag
- **FR3.1** For each game, the system determines the higher-ranked team by win percentage.
- **FR3.2** It converts both teams' odds to implied probabilities.
- **FR3.3** It sets `favorite_undervalued = true` if the higher-ranked team's implied probability is less than the lower-ranked team's.
- **FR3.4** Tie in win percentage → `false`. Missing record or odds → `null` (N/A).
- **FR3.5** Each flag result includes a short plain-English reason string.

### FR4: API
- **FR4.1** `GET /api/games?date=YYYY-MM-DD` returns normalized games with odds, implied probabilities, and flags.
- **FR4.2** An invalid date format returns `400` with a clear message.
- **FR4.3** Upstream API failure returns `502` with a clear message.
- **FR4.4** `GET /health` returns `200 OK`.

### FR5: User interface
- **FR5.1** A single page lists the day's games in a table.
- **FR5.2** Columns: matchup, records, win %, odds, implied %, flag.
- **FR5.3** Flagged rows have a highlighted background and a "⚠ Favorite Undervalued" badge.
- **FR5.4** A persistent banner reads: **"Odds are MOCKED for demonstration."**
- **FR5.5** A date picker reloads the data for the selected date.
- **FR5.6** Empty, loading, and error states are shown as friendly messages.
- **FR5.7** A summary line appears, for example: "12 games · 3 flagged."

## 7. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Readability** | Small modules with a single responsibility each. Type hints. No unnecessary abstractions. |
| **Testability** | Flag logic and odds math are pure functions with unit tests. |
| **Reliability** | The page never crashes from a single malformed game. Bad games are skipped and logged. |
| **Performance** | One upstream call per page load is acceptable at prototype scale. |
| **Setup** | Runs locally in 3 commands or fewer. No API keys required. |
| **Transparency** | Mocked data is labeled everywhere it appears. |

## 8. Error Handling Matrix

| Scenario | Behavior |
|---|---|
| ESPN timeout or network error | API returns `502`. UI shows "Couldn't reach the sports data provider. Try again." |
| ESPN returns non-JSON or an unexpected shape | Returns `502`. The error is logged. |
| A single game has malformed data | That game is skipped and logged. The remaining games still render. |
| No games on the date | Returns `200` with an empty list. UI shows "No games scheduled for this date." |
| A team has 0 games played | Win % is `null`. Flag is N/A. |
| Invalid date parameter | Returns `400`. UI shows the message. |
| Equal win % | Flag is `false`, with reason "Teams have equal records." |
| Equal odds (pick'em) | Flag is `false`, because the comparison is strict. |

## 9. Build Plan

Total estimate: **about 5 hours.**

| # | Milestone | Time | Output | Done when |
|---|---|---|---|---|
| M0 | **Explore the API** | 30 min | Notes on the field paths; a saved sample JSON fixture | The needed fields are located in a real response |
| M1 | **Scaffold** | 15 min | Repo, virtual environment, `requirements.txt`, FastAPI "hello" | `uvicorn` serves `/health` |
| M2 | **ESPN client and normalizer** | 60 min | `espn_client.py`, `normalize.py`, `models.py` | A clean `list[Game]` is printed for today |
| M3 | **Mock odds provider** | 30 min | `odds_mock.py` | Deterministic odds, with some upsets |
| M4 | **Flag logic and tests** | 45 min | `flags.py`, `tests/` | All tests pass, including edge cases |
| M5 | **API endpoint** | 20 min | `/api/games` | The JSON contract is met, with error codes |
| M6 | **UI** | 45 min | `static/index.html` | Table, highlights, banner, date picker, all states |
| M7 | **Hardening and README** | 30 min | README, logging, final error checks | A fresh clone runs by following the README |
| M8 | **Walkthrough video** | 45 min | 5–7 min Loom | Recorded, following the outline in §12 |

**Suggested order of risk:** do M0 first, because the ESPN response shape is the biggest unknown. Do M4 early, because correctness of the flag is the most heavily graded item.

## 10. Acceptance Criteria

- [ ] Running the app shows real MLB games for today, or for a chosen date.
- [ ] Every game displays both teams, their records, odds, and implied probabilities.
- [ ] Flagged games are visibly highlighted, and the flag matches the definition in §5.
- [ ] The mock-odds banner is visible at all times.
- [ ] Disconnecting the network (or breaking the URL) produces a friendly error, not a crash.
- [ ] A date with no games shows the empty state.
- [ ] `pytest` passes.
- [ ] The README lets a reviewer run the project in under 5 minutes.

## 11. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The ESPN API is unofficial and may change | Data fetch breaks | Defensive parsing; a saved fixture for tests; documented as a known risk |
| Late-September slate is thin or ends (postseason gaps) | Empty demo | The date picker allows choosing a date with games; the empty state is handled |
| Mock odds produce zero flags on demo day | Flag can't be shown | Noise level tuned so upsets are common; the seed is deterministic per date |
| Win % is a crude quality measure | Weak signal | Stated openly as an assumption; better ratings listed as future work |
| Over-building within the time box | Missed deadline | Non-goals list enforced; single league, no database |

## 12. Deliverables

1. **GitHub repository** with source code, tests, and README.
2. **Walkthrough video (5–7 min)**:
   1. The problem, in one sentence (0:30)
   2. Live demo, including one flagged game explained in plain English and one error state (1:30)
   3. Architecture and data flow (1:30)
   4. Key decisions and assumptions: MLB, win % as ranking, mock odds, ties, missing data (1:30)
   5. Tradeoffs and what's next (1:00)
3. **"Next 2-week sprint" note** (see §13).

## 13. Future Work (2-Week Sprint Candidates)

1. **Real odds:** integrate a real odds API (for example, The Odds API free tier) behind the existing provider interface.
2. **Caching:** cache scoreboard and odds responses for a short time (such as 5 minutes) to reduce upstream calls.
3. **Better ratings:** use run differential, Pythagorean win %, or Elo instead of raw win %.
4. **Multi-league support:** add a league parameter, starting with NFL and NCAA football (which has real AP rankings).
5. **Drill-down pages:** team, player, and coach detail views, as mentioned in the original brief.
6. **Flag history and backtesting:** store daily flags and measure how flagged games actually turned out.
7. **More flags:** line movement, public-betting splits, rest-day disadvantages.
8. **Deployment and CI:** containerize, add GitHub Actions for tests, and deploy a demo URL.
