"""
Generate sample email outputs for all 4 segments and save as HTML files.
Run: uv run python generate_samples.py
"""

import base64
from pathlib import Path
from jinja2 import Template

from segments import list_segments
from schedule import get_upcoming_home_games
from generator import generate
from images import get_hero_image

OUTPUT_DIR = Path(__file__).parent / "sample_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    template_str = (Path(__file__).parent / "email_template.html").read_text()
    tmpl = Template(template_str)

    games = get_upcoming_home_games(5)
    game = games[0]  # Use first upcoming game
    print(f"Generating samples for: Brewers vs. {game.opponent} on {game.date_str}")

    for seg in list_segments():
        creative = generate(
            segment=seg,
            opponent=game.opponent,
            game_date=game.date_str,
            game_time=game.time,
            day_of_week=game.day_of_week,
            use_ai=False,
        )

        body_paragraphs = [p.strip() for p in creative.body.split("\n\n") if p.strip()]

        # Load hero image as base64 for embedding in HTML
        hero_image_data = ""
        hero_path = get_hero_image(seg.key)
        if hero_path and hero_path.exists():
            hero_image_data = base64.b64encode(hero_path.read_bytes()).decode()

        html = tmpl.render(
            subject_line=creative.subject_line,
            preview_text=creative.preview_text,
            headline=creative.headline,
            body_paragraphs=body_paragraphs,
            cta_text=creative.cta_text,
            image_concept=creative.image_concept,
            hero_image_data=hero_image_data,
            opponent=creative.opponent,
            game_date=creative.game_date,
            game_time=creative.game_time,
            day_of_week=creative.day_of_week,
            color_accent=seg.color_accent,
            segment_name=seg.name,
            segment_key=seg.key,
            segment_tagline=seg.tagline,
            segment_emoji=seg.emoji,
        )

        out_path = OUTPUT_DIR / f"email_{seg.key}.html"
        out_path.write_text(html)
        print(f"  ✅ {seg.emoji} {seg.name} → {out_path.name}")

        # Also save a text summary
        summary = (
            f"SEGMENT: {seg.name} ({seg.key})\n"
            f"GAME: Brewers vs. {game.opponent} — {game.day_of_week}, {game.date_str} at {game.time}\n"
            f"{'='*60}\n\n"
            f"SUBJECT LINE: {creative.subject_line}\n"
            f"PREVIEW TEXT: {creative.preview_text}\n\n"
            f"HEADLINE: {creative.headline}\n\n"
            f"BODY:\n{creative.body}\n\n"
            f"CTA: {creative.cta_text}\n\n"
            f"IMAGE CONCEPT:\n{creative.image_concept}\n"
        )
        txt_path = OUTPUT_DIR / f"email_{seg.key}.txt"
        txt_path.write_text(summary)

    print(f"\n📁 All samples saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
