"""
Fetch and parse the 2026 Milwaukee Brewers regular-season schedule
from the MLB Stats API (public, no auth required).
"""

from __future__ import annotations

import datetime
import requests
from dataclasses import dataclass

BREWERS_TEAM_ID = 158  # MLB team ID for Milwaukee Brewers
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"


@dataclass
class Game:
    game_pk: int
    date: datetime.date
    time: str           # e.g. "7:10 PM"
    day_of_week: str    # e.g. "Friday"
    opponent: str       # e.g. "Chicago Cubs"
    home_away: str      # "home" or "away"
    venue: str
    promo: str = ""     # placeholder for promo-night info

    @property
    def display_label(self) -> str:
        ha = "vs." if self.home_away == "home" else "@"
        return f"{self.day_of_week} {self.date.strftime('%b %-d')} — {ha} {self.opponent} ({self.time})"

    @property
    def date_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")


def fetch_schedule(
    season: int = 2025,
    start_date: str | None = None,
    end_date: str | None = None,
    home_only: bool = True,
) -> list[Game]:
    """
    Fetch Brewers games from the MLB Stats API.
    Defaults to upcoming home games (since we're selling individual tickets
    at American Family Field).
    """
    params: dict = {
        "teamId": BREWERS_TEAM_ID,
        "season": season,
        "sportId": 1,
        "gameType": "R",  # regular season
        "hydrate": "team,venue,promotions",
    }
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    try:
        resp = requests.get(MLB_SCHEDULE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        # Fallback to hardcoded sample if API is unavailable
        return _fallback_schedule()

    games: list[Game] = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            away_team = g.get("teams", {}).get("away", {}).get("team", {}).get("name", "TBD")
            home_team = g.get("teams", {}).get("home", {}).get("team", {}).get("name", "TBD")

            is_home = home_team == "Milwaukee Brewers"
            if home_only and not is_home:
                continue

            opponent = away_team if is_home else home_team

            # Parse date / time
            game_date_str = g.get("gameDate", "")  # ISO format
            try:
                dt = datetime.datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                # Convert to Central Time (rough: UTC-5 / UTC-6)
                dt_central = dt - datetime.timedelta(hours=5)
                game_date = dt_central.date()
                game_time = dt_central.strftime("%-I:%M %p")
                day_of_week = dt_central.strftime("%A")
            except (ValueError, AttributeError):
                game_date = datetime.date.fromisoformat(date_entry.get("date", "2026-06-01"))
                game_time = "TBD"
                day_of_week = game_date.strftime("%A")

            venue = g.get("venue", {}).get("name", "American Family Field")

            # Promo info (if hydrated)
            promos = g.get("promotions", [])
            promo_text = promos[0].get("name", "") if promos else ""

            games.append(Game(
                game_pk=g.get("gamePk", 0),
                date=game_date,
                time=game_time,
                day_of_week=day_of_week,
                opponent=opponent,
                home_away="home" if is_home else "away",
                venue=venue,
                promo=promo_text,
            ))

    games.sort(key=lambda g: g.date)
    return games


def get_upcoming_home_games(limit: int = 30) -> list[Game]:
    """
    Return upcoming home games. Tries the current MLB season first,
    then falls back to showing the full fallback schedule if all games
    are in the past (useful for prototype / demo purposes).
    """
    today = datetime.date.today()
    # Try current season
    all_games = fetch_schedule(season=today.year, home_only=True)
    upcoming = [g for g in all_games if g.date >= today]

    # If no future games (offseason or API miss), show full fallback for demo
    if not upcoming:
        all_games = _fallback_schedule()
        upcoming = all_games  # show all for demo purposes

    return upcoming[:limit]


# ---------------------------------------------------------------------------
# Fallback schedule when API is unavailable
# ---------------------------------------------------------------------------

def _fallback_schedule() -> list[Game]:
    """
    Hardcoded sample of ~20 Brewers home games so the prototype
    works even without network access.
    """
    raw = [
        (718001, "2026-04-02", "1:10 PM", "Chicago Cubs"),
        (718002, "2026-04-03", "7:10 PM", "Chicago Cubs"),
        (718003, "2026-04-04", "6:10 PM", "Chicago Cubs"),
        (718004, "2026-04-05", "1:10 PM", "Chicago Cubs"),
        (718010, "2026-04-10", "7:10 PM", "St. Louis Cardinals"),
        (718011, "2026-04-11", "6:10 PM", "St. Louis Cardinals"),
        (718012, "2026-04-12", "1:10 PM", "St. Louis Cardinals"),
        (718020, "2026-04-24", "7:10 PM", "Cincinnati Reds"),
        (718021, "2026-04-25", "6:10 PM", "Cincinnati Reds"),
        (718022, "2026-04-26", "1:10 PM", "Cincinnati Reds"),
        (718030, "2026-05-08", "7:10 PM", "Pittsburgh Pirates"),
        (718031, "2026-05-09", "6:10 PM", "Pittsburgh Pirates"),
        (718032, "2026-05-10", "1:10 PM", "Pittsburgh Pirates"),
        (718040, "2026-05-22", "7:10 PM", "Los Angeles Dodgers"),
        (718041, "2026-05-23", "3:10 PM", "Los Angeles Dodgers"),
        (718042, "2026-05-24", "1:10 PM", "Los Angeles Dodgers"),
        (718050, "2026-06-05", "7:10 PM", "New York Mets"),
        (718051, "2026-06-06", "6:10 PM", "New York Mets"),
        (718052, "2026-06-07", "1:10 PM", "New York Mets"),
        (718060, "2026-06-19", "7:10 PM", "Minnesota Twins"),
        (718061, "2026-06-20", "6:10 PM", "Minnesota Twins"),
        (718062, "2026-06-21", "1:10 PM", "Minnesota Twins"),
        (718070, "2026-07-03", "1:10 PM", "San Francisco Giants"),
        (718071, "2026-07-04", "6:10 PM", "San Francisco Giants"),
        (718080, "2026-07-17", "7:10 PM", "Atlanta Braves"),
        (718081, "2026-07-18", "6:10 PM", "Atlanta Braves"),
        (718082, "2026-07-19", "1:10 PM", "Atlanta Braves"),
        (718090, "2026-07-31", "7:10 PM", "Philadelphia Phillies"),
        (718091, "2026-08-01", "6:10 PM", "Philadelphia Phillies"),
        (718092, "2026-08-02", "1:10 PM", "Philadelphia Phillies"),
    ]

    games = []
    for pk, ds, time, opp in raw:
        d = datetime.date.fromisoformat(ds)
        games.append(Game(
            game_pk=pk,
            date=d,
            time=time,
            day_of_week=d.strftime("%A"),
            opponent=opp,
            home_away="home",
            venue="American Family Field",
        ))
    return games
