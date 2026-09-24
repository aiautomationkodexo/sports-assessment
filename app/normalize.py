"""Turns ESPN's raw JSON into a clean list of Game objects.

The governing rule is that one malformed game must never break the whole
slate. Anything unparseable is skipped and logged.
"""

import logging

from app.models import Game, Team

log = logging.getLogger(__name__)


def parse_record(summary: str | None) -> tuple[int | None, int | None, float | None]:
    """Parse a record like "85-70" into (wins, losses, win_pct).

    Returns Nones when the record is absent or unparseable. A 0-0 record
    yields a None win_pct rather than a divide-by-zero: a team that has not
    played has no win percentage, which is different from a 0% one.
    """
    if not summary:
        return None, None, None
    parts = summary.split("-")
    if len(parts) < 2:
        return None, None, None
    try:
        wins, losses = int(parts[0]), int(parts[1])
    except ValueError:
        return None, None, None
    if wins < 0 or losses < 0:
        return None, None, None
    played = wins + losses
    return wins, losses, (wins / played if played else None)


def _overall_record(competitor: dict) -> str | None:
    """Pull the season-total record out of a competitor's records list.

    ESPN returns several records per team (total / home / road); we want the
    one marked type "total" (equivalently, name "overall").
    """
    for rec in competitor.get("records") or []:
        if rec.get("type") == "total" or rec.get("name") == "overall":
            return rec.get("summary")
    return None


def _team(competitor: dict) -> Team:
    t = competitor["team"]
    summary = _overall_record(competitor)
    wins, losses, pct = parse_record(summary)
    return Team(
        id=str(t["id"]),
        name=t.get("displayName", "Unknown"),
        abbr=t.get("abbreviation", ""),
        record=summary,
        wins=wins,
        losses=losses,
        win_pct=pct,
    )


def normalize_scoreboard(raw: dict) -> list[Game]:
    """Convert a raw ESPN scoreboard payload into a list of Games."""
    games: list[Game] = []
    for event in raw.get("events") or []:
        try:
            comp = event["competitions"][0]
            by_side = {c["homeAway"]: c for c in comp["competitors"]}
            games.append(
                Game(
                    id=str(event["id"]),
                    start_time=event.get("date", ""),
                    status=(
                        event.get("status", {})
                        .get("type", {})
                        .get("detail", "Unknown")
                    ),
                    home=_team(by_side["home"]),
                    away=_team(by_side["away"]),
                )
            )
        except (KeyError, IndexError, TypeError) as exc:
            log.warning(
                "Skipping malformed event %s: %s",
                (event or {}).get("id", "<no id>"),
                exc,
            )
    return games
