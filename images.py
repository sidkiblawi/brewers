"""
Image crawler for Milwaukee Brewers marketing assets.

Downloads real Brewers photos from Wikimedia Commons (CC-licensed),
organized by fan segment. These are used as hero images in email previews.

Run: uv run python images.py
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets" / "images"

# ---------------------------------------------------------------------------
# Curated image sources — real Brewers / American Family Field photos
# All from Wikimedia Commons (Creative Commons licensed)
#
# URL format: Special:FilePath redirects to the actual hosted image
# at the requested width.
# ---------------------------------------------------------------------------

_WC = "https://commons.wikimedia.org/wiki/Special:FilePath"

IMAGE_SOURCES: dict[str, list[dict[str, str]]] = {
    "die_hard": [
        {
            "url": f"{_WC}/Sold_Out_Miller_Park_(11669999).jpg?width=800",
            "desc": "Sold out crowd at Miller Park",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Celebration_(573458897).jpg?width=800",
            "desc": "Brewers celebration on the field",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/View_behind_home_plate_at_Miller_Park.jpg?width=800",
            "desc": "View from behind home plate at Miller Park",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Brewers_game_Sept_2022.jpg?width=800",
            "desc": "Brewers game night September 2022",
            "credit": "Wikimedia Commons / CC",
        },
    ],
    "foodie": [
        {
            "url": f"{_WC}/Sausage_race.jpg?width=800",
            "desc": "Famous Brewers sausage race",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Sausages_(510428640).jpg?width=800",
            "desc": "Racing sausages at American Family Field",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Bernies_chalet_in_front_of_the_Miller_Park_Clock_Tower_(4288151729).jpg?width=800",
            "desc": "Bernie Brewer chalet and clock tower",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Inside_Miller_Park_(4952578819).jpg?width=800",
            "desc": "Inside Miller Park concourse",
            "credit": "Wikimedia Commons / CC",
        },
    ],
    "family": [
        {
            "url": f"{_WC}/Helfaer_Field%2C_Little_League_Field%2C_April_2012.jpg?width=800",
            "desc": "Helfaer Field little league park at AmFam",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/American_Family_Field_(October_2023)_01.jpg?width=800",
            "desc": "American Family Field exterior 2023",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Miller_Park_(16180192112).jpg?width=800",
            "desc": "Bright sunny day inside Miller Park",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Barrelman_Mascot_June_2015.jpg?width=800",
            "desc": "Brewers Barrelman mascot for the kids",
            "credit": "Wikimedia Commons / CC",
        },
    ],
    "social": [
        {
            "url": f"{_WC}/Fireworks_(573138034).jpg?width=800",
            "desc": "Fireworks night at Miller Park",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Miller_Park_at_Night_(31239729).jpg?width=800",
            "desc": "Miller Park glowing at night",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Cheerleaders_at_a_Milwaukee_Brewers_game.jpg?width=800",
            "desc": "Entertainment at a Brewers game",
            "credit": "Wikimedia Commons / CC",
        },
        {
            "url": f"{_WC}/Bad_Dance_(31239332).jpg?width=800",
            "desc": "Fun crowd moments at a Brewers game",
            "credit": "Wikimedia Commons / CC",
        },
    ],
    "branding": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b8/Milwaukee_Brewers_logo.svg/800px-Milwaukee_Brewers_logo.svg.png",
            "desc": "Milwaukee Brewers logo",
            "credit": "Wikimedia Commons",
        },
        {
            "url": f"{_WC}/American_Family_Field_(October_2023)_02.jpg?width=1200",
            "desc": "American Family Field panoramic exterior",
            "credit": "Wikimedia Commons / CC",
        },
    ],
}


def _sanitize_filename(desc: str) -> str:
    """Turn a description into a safe filename slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", desc.lower()).strip("_")
    return slug[:60]


def download_images(overwrite: bool = False) -> dict[str, list[Path]]:
    """
    Download all curated images, organized into segment subdirectories.
    Returns a mapping of segment_key -> list of local file paths.
    """
    downloaded: dict[str, list[Path]] = {}

    for segment, sources in IMAGE_SOURCES.items():
        seg_dir = ASSETS_DIR / segment
        seg_dir.mkdir(parents=True, exist_ok=True)
        downloaded[segment] = []

        print(f"\n📂 {segment.upper()}")

        for i, src in enumerate(sources):
            filename = f"{_sanitize_filename(src['desc'])}.jpg"
            filepath = seg_dir / filename

            if filepath.exists() and not overwrite:
                print(f"  ⏭️  Already exists: {filepath.name}")
                downloaded[segment].append(filepath)
                continue

            try:
                print(f"  ⬇️  Downloading: {src['desc']}...")
                time.sleep(3)  # Respect Wikimedia rate limits

                # Use curl because Wikimedia blocks Python requests User-Agent
                result = subprocess.run(
                    ["curl", "-sL", "-o", str(filepath), "-w", "%{http_code}",
                     src["url"]],
                    capture_output=True, text=True, timeout=30,
                )
                status_code = result.stdout.strip()
                if status_code != "200" or not filepath.exists():
                    filepath.unlink(missing_ok=True)
                    raise ValueError(f"HTTP {status_code}")

                size_kb = filepath.stat().st_size // 1024
                if size_kb < 2:
                    filepath.unlink(missing_ok=True)
                    raise ValueError("File too small, likely not an image")

                downloaded[segment].append(filepath)
                print(f"     ✅ Saved: {filepath.name} ({size_kb}KB)")

            except Exception as e:
                print(f"     ❌ Failed: {src['desc']} — {e}")

        # Write a credits.json file for attribution
        credits = [
            {
                "file": _sanitize_filename(s["desc"]) + ".jpg",
                "description": s["desc"],
                "credit": s["credit"],
                "url": s["url"],
            }
            for s in sources
        ]
        (seg_dir / "credits.json").write_text(json.dumps(credits, indent=2))

    return downloaded


def get_segment_images(segment_key: str) -> list[Path]:
    """Return list of downloaded image paths for a segment."""
    seg_dir = ASSETS_DIR / segment_key
    if not seg_dir.exists():
        return []
    return sorted(seg_dir.glob("*.jpg")) + sorted(seg_dir.glob("*.png"))


def get_hero_image(segment_key: str, index: int = 0) -> Path | None:
    """Get the primary hero image for a segment."""
    images = get_segment_images(segment_key)
    if not images:
        return None
    return images[index % len(images)]


def get_hero_description(segment_key: str, index: int = 0) -> str:
    """Get the description of the hero image actually used for a segment."""
    sources = IMAGE_SOURCES.get(segment_key, [])
    if not sources:
        return ""
    src = sources[index % len(sources)]
    return src["desc"]


def get_branding_image(name: str = "logo") -> Path | None:
    """Get a branding asset (logo or stadium exterior)."""
    seg_dir = ASSETS_DIR / "branding"
    if not seg_dir.exists():
        return None
    if name == "logo":
        # Look for the logo PNG specifically
        logos = list(seg_dir.glob("*logo*"))
        return logos[0] if logos else None
    # Otherwise return the first non-logo image (stadium exterior, etc.)
    images = sorted(seg_dir.glob("*.jpg"))
    return images[0] if images else None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🍺 Brewers Image Downloader")
    print("=" * 50)
    results = download_images(overwrite=True)
    print("\n" + "=" * 50)
    total = sum(len(v) for v in results.values())
    print(f"✅ Downloaded {total} images across {len(results)} categories")
    for seg, paths in results.items():
        print(f"   {seg}: {len(paths)} images")
