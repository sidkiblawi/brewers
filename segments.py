"""
Fan segment definitions, prompt templates, and creative rules.

Each segment encodes:
- Persona description & motivations
- Tone / voice guidelines
- Preferred imagery direction
- CTA language
- System + user prompt templates for LLM generation
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Segment dataclass
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    key: str
    name: str
    persona: str
    tagline: str
    description: str
    tone: str
    imagery: list[str]
    cta_primary: str
    cta_secondary: str
    color_accent: str  # hex
    emoji: str
    # Prompt building blocks
    copy_angles: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    @property
    def system_prompt(self) -> str:
        return (
            f"You are a senior sports-marketing copywriter for the Milwaukee Brewers. "
            f"You are writing a promotional email targeting Individual game ticket sales. "
            f"The audience is: {self.persona} — {self.description} "
            f"Tone: {self.tone}. "
            f"Avoid: {', '.join(self.avoid)}. "
            f"Keep subject lines under 60 characters. Keep body copy under 120 words. "
            f"Always include a clear call-to-action using language like: '{self.cta_primary}'."
        )

    def user_prompt(self, opponent: str, game_date: str, game_time: str,
                    day_of_week: str, promo: str = "") -> str:
        promo_line = f" Special promo: {promo}." if promo else ""
        return (
            f"Write a marketing email for the Milwaukee Brewers vs. {opponent} "
            f"on {day_of_week}, {game_date} at {game_time}.{promo_line}\n\n"
            f"Angle options to consider: {', '.join(self.copy_angles)}.\n\n"
            f"Return JSON with these exact keys:\n"
            f"  subject_line: string\n"
            f"  preview_text: string (under 90 chars)\n"
            f"  headline: string\n"
            f"  body: string (the email body, 2-3 short paragraphs)\n"
            f"  cta_text: string (button label)\n"
            f"Only return valid JSON — no markdown, no extra text."
        )


# ---------------------------------------------------------------------------
# The four segments
# ---------------------------------------------------------------------------

DIE_HARD = Segment(
    key="die_hard",
    name="Die-Hard Danny",
    persona="Die-Hard Danny",
    tagline="This Is Your Game",
    description=(
        "A passionate, knowledgeable baseball fan who follows stats, prospects, "
        "and matchups. Watches every game, knows the rotation, and values the "
        "competitive product on the field above all else."
    ),
    tone="Confident, insider-ish, stats-aware. Speak to them like a fellow fan, not a customer.",
    imagery=["pitching duels", "game action shots", "scoreboard", "packed stadium"],
    cta_primary="Get Your Tickets",
    cta_secondary="Don't Miss This Matchup",
    color_accent="#12284B",  # Brewers navy
    emoji="⚾",
    copy_angles=[
        "Pitching matchup & probable starters",
        "Season series history",
        "Playoff implications / standings context",
        "Milestone watch for players",
        "Rivalry narrative",
    ],
    avoid=["Overly salesy language", "food/drink focus", "kids activities", "generic hype"],
)

FOODIE = Segment(
    key="foodie",
    name="Foodie Frank",
    persona="Foodie Frank",
    tagline="Taste the Ballpark",
    description=(
        "Loves the ballpark experience beyond the game — craft beer, local food vendors, "
        "new menu items, and the full sensory experience. The game is the backdrop; "
        "the food and drink are the main event."
    ),
    tone="Indulgent, sensory, playful. Make their mouth water.",
    imagery=["craft beer pours", "loaded nachos", "ballpark food spread", "sunset over the stadium"],
    cta_primary="Grab Your Seats & Your Appetite",
    cta_secondary="See What's On the Menu",
    color_accent="#FFC72C",  # Brewers gold
    emoji="🍔",
    copy_angles=[
        "New or featured menu items for the series",
        "Craft beer specials or local brewery partnerships",
        "Food vendor spotlights",
        "Best bites at AmFam Field",
        "Pairing the experience: what to eat at a night game",
    ],
    avoid=["Heavy stats talk", "playoff jargon", "kids zone mentions", "generic ticket push"],
)

FAMILY = Segment(
    key="family",
    name="Parent Patty",
    persona="Parent Patty",
    tagline="Make It a Family Day",
    description=(
        "A parent looking for a fun, affordable, wholesome outing for the family. "
        "Cares about kid-friendly activities, value pricing, and creating memories. "
        "The game is part of a bigger family experience."
    ),
    tone="Warm, inviting, reassuring. Emphasize ease and value.",
    imagery=["families in the stands", "kids zone", "mascot interactions", "family smiling at game"],
    cta_primary="Plan Your Family Day",
    cta_secondary="Get Family-Friendly Seats",
    color_accent="#0A2240",  # dark blue
    emoji="👨‍👩‍👧‍👦",
    copy_angles=[
        "Sunday family games or day games",
        "Kids zone & family-friendly areas",
        "Affordable ticket + food bundles",
        "Mascot appearances (Bernie Brewer)",
        "Creating memories / first-game moments",
    ],
    avoid=["Late-night game hype", "beer-focused messaging", "intense rivalry language", "FOMO tactics"],
)

SOCIAL = Segment(
    key="social",
    name="Tailgate Tammy",
    persona="Tailgate Tammy",
    tagline="Rally Your Crew",
    description=(
        "A social fan who loves the pregame scene, the energy of the crowd, "
        "and going out with friends. The ballpark is a social venue first. "
        "Motivated by FOMO, group energy, and shareable moments."
    ),
    tone="Energetic, fun, FOMO-driven. Make them want to text their group chat immediately.",
    imagery=["tailgate setup", "friends cheering", "crowd energy", "pregame scene in the lot"],
    cta_primary="Rally Your Crew",
    cta_secondary="Grab Tickets Before They're Gone",
    color_accent="#B6922E",  # gold accent
    emoji="🎉",
    copy_angles=[
        "Weekend games & Friday night energy",
        "Tailgate scene & pregame atmosphere",
        "Group ticket deals / bring-a-friend",
        "Social media moments / shareable experiences",
        "Post-game events or concert nights",
    ],
    avoid=["Stats-heavy language", "family/kids focus", "quiet weeknight framing", "discount-only messaging"],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SEGMENTS: dict[str, Segment] = {
    "die_hard": DIE_HARD,
    "foodie": FOODIE,
    "family": FAMILY,
    "social": SOCIAL,
}


def get_segment(key: str) -> Segment:
    """Return a segment by key, or raise KeyError."""
    return SEGMENTS[key]


def list_segments() -> list[Segment]:
    """Return all segments in display order."""
    return list(SEGMENTS.values())
