"""
Email copy & image-concept generator.

Supports two modes:
  1. AI mode   — calls OpenAI for dynamic generation
  2. Mock mode — returns high-quality templated copy (no API key needed)

The mock copy is deliberately good so reviewers can evaluate the full
workflow without needing an API key.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from segments import Segment
from images import get_hero_description

# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

@dataclass
class EmailCreative:
    segment_key: str
    subject_line: str
    preview_text: str
    headline: str
    body: str
    cta_text: str
    image_concept: str
    opponent: str
    game_date: str
    game_time: str
    day_of_week: str

    def to_dict(self) -> dict:
        return self.__dict__


# ---------------------------------------------------------------------------
# AI generation (OpenAI)
# ---------------------------------------------------------------------------

def generate_ai(segment: Segment, opponent: str, game_date: str,
                game_time: str, day_of_week: str, promo: str = "") -> EmailCreative:
    """Generate email creative using OpenAI."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": segment.system_prompt},
            {"role": "user", "content": segment.user_prompt(
                opponent=opponent,
                game_date=game_date,
                game_time=game_time,
                day_of_week=day_of_week,
                promo=promo,
            )},
        ],
        temperature=0.8,
        max_tokens=600,
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    return EmailCreative(
        segment_key=segment.key,
        subject_line=data.get("subject_line", "Brewers Game Day"),
        preview_text=data.get("preview_text", ""),
        headline=data.get("headline", ""),
        body=data.get("body", ""),
        cta_text=data.get("cta_text", segment.cta_primary),
        image_concept=get_hero_description(segment.key),
        opponent=opponent,
        game_date=game_date,
        game_time=game_time,
        day_of_week=day_of_week,
    )


# ---------------------------------------------------------------------------
# Mock generation (no API key required)
# ---------------------------------------------------------------------------

_MOCK_TEMPLATES: dict[str, dict] = {
    "die_hard": {
        "subject_line": "🔥 {opponent} roll into town {day}",
        "preview_text": "This matchup is circled on every real fan's calendar.",
        "headline": "This Is the Series You've Been Waiting For",
        "body": (
            "The {opponent} are coming to American Family Field on {day_of_week}, {game_date} "
            "at {game_time} — and this one has all the makings of a classic.\n\n"
            "Keep an eye on the pitching matchup. Our rotation has been dealing lately, "
            "and this series could have real implications down the stretch. "
            "You know the atmosphere at AmFam when the stakes are high.\n\n"
            "This is the kind of game you want to say you were at. "
            "Grab your individual tickets now before the good seats are gone."
        ),
        "cta_text": "Get Your Tickets",
        "image_concept": "",  # filled from actual downloaded image
    },
    "foodie": {
        "subject_line": "🍺 Brews, bites & baseball — {day} at AmFam",
        "preview_text": "New menu drops this series. Your taste buds will thank you.",
        "headline": "The Best Bites in Baseball. Seriously.",
        "body": (
            "The Brewers host the {opponent} on {day_of_week}, {game_date} at {game_time} — "
            "and this series, the food lineup might rival the batting order.\n\n"
            "Think Wisconsin cheese curds, craft beer from local breweries, and a few "
            "new items the culinary team has been perfecting. "
            "Arrive early, grab a spot on the terrace, and taste your way through nine innings.\n\n"
            "Baseball is better when it comes with a cold one and a loaded brat. "
            "Lock in your seats and bring your appetite."
        ),
        "cta_text": "Grab Your Seats & Your Appetite",
        "image_concept": "",  # filled from actual downloaded image
    },
    "family": {
        "subject_line": "👨‍👩‍👧‍👦 A perfect family day at the ballpark",
        "preview_text": "Sun, smiles, and a whole lot of fun for the kids.",
        "headline": "Make Memories They'll Never Forget",
        "body": (
            "Bring the whole family out to American Family Field on {day_of_week}, {game_date} "
            "at {game_time} when the Brewers take on the {opponent}.\n\n"
            "The kids will love the Family Fun Zone, and you might even catch Bernie Brewer "
            "sliding down after a home run. It's the kind of day that turns into a story "
            "they tell at school on Monday.\n\n"
            "Affordable individual tickets are available now — because the best family "
            "memories don't have to break the bank."
        ),
        "cta_text": "Plan Your Family Day",
        "image_concept": "",  # filled from actual downloaded image
    },
    "social": {
        "subject_line": "🎉 This {day} is going to be LOUD",
        "preview_text": "Your group chat is about to blow up. Don't be the one who missed it.",
        "headline": "Rally Your Crew. This One's Going to Be Big.",
        "body": (
            "The {opponent} are in town on {day_of_week}, {game_date} at {game_time} — "
            "and you already know the tailgate scene is going to be unreal.\n\n"
            "Get to the lot early, fire up the grill, and soak in the pregame energy. "
            "By first pitch, the whole stadium will be buzzing. "
            "This is the kind of night that ends up all over everyone's Instagram.\n\n"
            "Don't be the friend who sees the photos on Monday and wishes they'd been there. "
            "Grab your tickets and text the crew."
        ),
        "cta_text": "Rally Your Crew",
        "image_concept": "",  # filled from actual downloaded image
    },
}


def generate_mock(segment: Segment, opponent: str, game_date: str,
                  game_time: str, day_of_week: str, **_kwargs) -> EmailCreative:
    """Generate email creative from high-quality templates."""
    tmpl = _MOCK_TEMPLATES[segment.key]

    fmt = {
        "opponent": opponent,
        "game_date": game_date,
        "game_time": game_time,
        "day_of_week": day_of_week,
        "day": day_of_week,  # short alias for subject lines
    }

    return EmailCreative(
        segment_key=segment.key,
        subject_line=tmpl["subject_line"].format(**fmt),
        preview_text=tmpl["preview_text"].format(**fmt) if "{" in tmpl["preview_text"] else tmpl["preview_text"],
        headline=tmpl["headline"].format(**fmt) if "{" in tmpl["headline"] else tmpl["headline"],
        body=tmpl["body"].format(**fmt),
        cta_text=tmpl["cta_text"],
        image_concept=get_hero_description(segment.key) or tmpl["image_concept"],
        opponent=opponent,
        game_date=game_date,
        game_time=game_time,
        day_of_week=day_of_week,
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate(segment: Segment, opponent: str, game_date: str,
             game_time: str, day_of_week: str, promo: str = "",
             use_ai: bool = False) -> EmailCreative:
    """
    Generate email creative for a given segment + game.
    Falls back to mock if AI fails or is disabled.
    """
    if use_ai and os.environ.get("OPENAI_API_KEY"):
        try:
            return generate_ai(segment, opponent, game_date, game_time, day_of_week, promo)
        except Exception as e:
            print(f"[generator] AI generation failed, falling back to mock: {e}")

    return generate_mock(segment, opponent, game_date, game_time, day_of_week)
