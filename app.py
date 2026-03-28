"""
Brewers Tailored Marketing Engine — Streamlit UI

Main entry point: `uv run streamlit run app.py`
"""

from __future__ import annotations

import base64
import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st
from jinja2 import Template

from segments import list_segments, get_segment, Segment
from schedule import get_upcoming_home_games, Game
from generator import generate, EmailCreative
from export import build_crm_dataframe, build_full_export, dataframe_to_csv_bytes
from images import get_hero_image, get_branding_image

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Brewers Tailored Marketing Engine",
    page_icon="⚾",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Load static assets
# ---------------------------------------------------------------------------

@st.cache_data
def load_fan_data() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).parent / "sample_fan_data.csv")

@st.cache_data
def load_email_template() -> str:
    return (Path(__file__).parent / "email_template.html").read_text()

@st.cache_data(ttl=3600)
def load_schedule() -> list[dict]:
    games = get_upcoming_home_games(limit=40)
    return [g.__dict__ for g in games]

# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

_logo_path = get_branding_image("logo")
if _logo_path and _logo_path.exists():
    st.sidebar.image(str(_logo_path), width=120)
else:
    st.sidebar.markdown("## ⚾ Milwaukee Brewers")
st.sidebar.title("Marketing Engine")
st.sidebar.caption("Generate personalized email creative for Individual ticket campaigns.")

# AI toggle
use_ai = st.sidebar.toggle(
    "🤖 Use AI Generation (OpenAI)",
    value=False,
    help="Requires OPENAI_API_KEY in .env. When off, uses high-quality templated copy.",
)
if use_ai and not os.environ.get("OPENAI_API_KEY"):
    st.sidebar.warning("No OPENAI_API_KEY found. Set it in a `.env` file or export it.")

st.sidebar.divider()

# Game selection
st.sidebar.subheader("1️⃣ Select a Game")

games_raw = load_schedule()
if not games_raw:
    st.sidebar.error("Could not load schedule. Using fallback.")
    games_raw = load_schedule()

# Build display labels
game_options = {}
for g in games_raw:
    d = g["date"] if isinstance(g["date"], datetime.date) else datetime.date.fromisoformat(str(g["date"]))
    ha = "vs." if g["home_away"] == "home" else "@"
    label = f"{g['day_of_week']} {d.strftime('%b %-d')} — {ha} {g['opponent']} ({g['time']})"
    game_options[label] = g

selected_label = st.sidebar.selectbox("Upcoming Home Games", list(game_options.keys()))
selected_game = game_options[selected_label]

st.sidebar.divider()

# Segment selection
st.sidebar.subheader("2️⃣ Select a Segment")

segments = list_segments()
segment_options = {f"{s.emoji} {s.name}": s.key for s in segments}
selected_seg_label = st.sidebar.selectbox("Target Segment", list(segment_options.keys()))
selected_seg_key = segment_options[selected_seg_label]
selected_segment = get_segment(selected_seg_key)

st.sidebar.divider()

# Generate button
generate_single = st.sidebar.button("⚡ Generate Email", type="primary")
generate_all = st.sidebar.button("📦 Generate All 4 Segments")

# ---------------------------------------------------------------------------
# Helper: render email preview
# ---------------------------------------------------------------------------

def render_email_html(creative: EmailCreative, segment: Segment) -> str:
    """Render the Jinja2 email template with creative + segment data."""
    template_str = load_email_template()
    tmpl = Template(template_str)

    body_paragraphs = [p.strip() for p in creative.body.split("\n\n") if p.strip()]

    # Load hero image as base64 data URI for inline embedding
    hero_image_data = ""
    hero_path = get_hero_image(segment.key)
    if hero_path and hero_path.exists():
        hero_image_data = base64.b64encode(hero_path.read_bytes()).decode()

    return tmpl.render(
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
        color_accent=segment.color_accent,
        segment_name=segment.name,
        segment_key=segment.key,
        segment_tagline=segment.tagline,
        segment_emoji=segment.emoji,
    )


def show_creative(creative: EmailCreative, segment: Segment):
    """Display a single creative in the main area."""

    col_preview, col_data = st.columns([3, 2])

    with col_preview:
        st.subheader(f"{segment.emoji} Email Preview — {segment.name}")
        html = render_email_html(creative, segment)
        st.components.v1.html(html, height=800, scrolling=True)

    with col_data:
        st.subheader("📋 Creative Details")

        st.markdown(f"**Subject Line:** {creative.subject_line}")
        st.markdown(f"**Preview Text:** {creative.preview_text}")
        st.divider()

        st.markdown("**Headline:**")
        st.info(creative.headline)

        st.markdown("**Body Copy:**")
        st.text_area("Body", creative.body, height=200, disabled=True, label_visibility="collapsed")

        st.markdown(f"**CTA:** `{creative.cta_text}`")
        st.divider()

        st.markdown("**🖼️ Hero Image:**")
        st.caption(creative.image_concept)
        st.divider()

        # CRM Export for this segment
        st.subheader("📤 CRM Export")
        fan_df = load_fan_data()
        crm_df = build_crm_dataframe(creative, fan_df, segment.key)

        st.metric("Recipients", len(crm_df))
        st.dataframe(crm_df[["email", "first_name", "segment", "subject_line", "send_date"]].head(10))

        csv_bytes = dataframe_to_csv_bytes(crm_df)
        st.download_button(
            label=f"⬇️ Download CRM CSV ({segment.name})",
            data=csv_bytes,
            file_name=f"brewers_crm_{segment.key}_{creative.game_date}.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Main content area
# ---------------------------------------------------------------------------

st.title("⚾ Brewers Tailored Marketing Engine")
st.caption("Generate personalized email creative for Individual ticket campaigns across four fan segments.")

# Game context bar
game_date = selected_game["date"] if isinstance(selected_game["date"], datetime.date) else datetime.date.fromisoformat(str(selected_game["date"]))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Opponent", selected_game["opponent"])
col2.metric("Date", game_date.strftime("%b %-d, %Y"))
col3.metric("Time", selected_game["time"])
col4.metric("Day", selected_game["day_of_week"])

if selected_game.get("promo"):
    st.info(f"🎁 **Promotion:** {selected_game['promo']}")

st.divider()

# ---------------------------------------------------------------------------
# Single segment generation
# ---------------------------------------------------------------------------

if generate_single:
    with st.spinner(f"Generating creative for {selected_segment.name}..."):
        creative = generate(
            segment=selected_segment,
            opponent=selected_game["opponent"],
            game_date=game_date.isoformat(),
            game_time=selected_game["time"],
            day_of_week=selected_game["day_of_week"],
            promo=selected_game.get("promo", ""),
            use_ai=use_ai,
        )
    show_creative(creative, selected_segment)

# ---------------------------------------------------------------------------
# All-segments generation
# ---------------------------------------------------------------------------

elif generate_all:
    creatives: dict[str, EmailCreative] = {}

    for seg in segments:
        with st.spinner(f"Generating creative for {seg.name}..."):
            c = generate(
                segment=seg,
                opponent=selected_game["opponent"],
                game_date=game_date.isoformat(),
                game_time=selected_game["time"],
                day_of_week=selected_game["day_of_week"],
                promo=selected_game.get("promo", ""),
                use_ai=use_ai,
            )
            creatives[seg.key] = c

    # Tabs for each segment
    tab_labels = [f"{seg.emoji} {seg.name}" for seg in segments]
    tabs = st.tabs(tab_labels)

    for tab, seg in zip(tabs, segments):
        with tab:
            show_creative(creatives[seg.key], seg)

    # Combined export
    st.divider()
    st.subheader("📦 Combined CRM Export — All Segments")

    fan_df = load_fan_data()
    full_df = build_full_export(creatives, fan_df)

    col_a, col_b, col_c, col_d = st.columns(4)
    for col, seg in zip([col_a, col_b, col_c, col_d], segments):
        count = len(full_df[full_df["segment"] == seg.key])
        col.metric(f"{seg.emoji} {seg.name}", count)

    st.dataframe(full_df.head(20))

    csv_bytes = dataframe_to_csv_bytes(full_df)
    st.download_button(
        label="⬇️ Download Full CRM Export (All Segments)",
        data=csv_bytes,
        file_name=f"brewers_crm_all_segments_{game_date.isoformat()}.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Default state — show segment overview
# ---------------------------------------------------------------------------

else:
    st.info("👈 Select a game and segment, then click **Generate Email** to get started.")

    st.subheader("Fan Segments")
    cols = st.columns(4)
    for col, seg in zip(cols, segments):
        with col:
            st.markdown(f"### {seg.emoji} {seg.name}")
            # Show hero image if available
            hero = get_hero_image(seg.key)
            if hero and hero.exists():
                st.image(str(hero), width="stretch")
            st.caption(seg.tagline)
            st.markdown(f"*{seg.description[:120]}...*")
            st.markdown(f"**Tone:** {seg.tone[:80]}...")
            st.markdown(f"**CTA:** {seg.cta_primary}")

    st.divider()

    # Show fan data summary
    st.subheader("📊 Sample Fan Database")
    fan_df = load_fan_data()

    col_a, col_b = st.columns([1, 2])
    with col_a:
        seg_counts = fan_df["segment_primary"].value_counts()
        st.dataframe(seg_counts.rename("Fans"))
    with col_b:
        st.dataframe(fan_df.head(10))
