# 🍺 Brewers Tailored Marketing Engine

A prototype tool that helps the Milwaukee Brewers marketing team generate personalized email creative for four fan segments, targeting **Individual ticket** sales.

| Segment | Persona | Focus |
|---|---|---|
| Die-Hard Baseball Fan | "Die-Hard Danny" | Stats, matchups, pitching duels |
| Ballpark Food & Beverage | "Foodie Frank" | Concessions, craft beer, dining |
| Family-Focused | "Parent Patty" | Kids zone, family value, wholesome fun |
| Social / Tailgate | "Tailgate Tammy" | Group energy, pregame scene, FOMO |

## What It Does

1. **Select an upcoming game** from the real 2026 Brewers schedule
2. **Pick a fan segment** to target
3. **Generate personalized email creative** — copy, subject line, and image concept tailored to that audience
4. **Export a CRM-ready CSV** structured for Salesforce Marketing Cloud upload

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

### Install uv (if you don't have it)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone & Run

```bash
# Clone the repository
git clone https://github.com/sidkiblawi/brewers.git
cd brewers

# Install dependencies (uv reads pyproject.toml automatically)
uv sync

# Launch the app
uv run streamlit run app.py
```

That's it. `uv sync` creates the virtual environment and installs everything in one step.

### Optional: Enable AI Generation

By default the app runs with built-in templated copy (no API key needed). To enable live OpenAI generation:

```bash
# Create a .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

Then toggle "Use AI Generation" in the app sidebar.

---

## Project Structure

```
brewers/
├── app.py                  # Streamlit UI — main entry point
├── segments.py             # Persona definitions & prompt templates
├── schedule.py             # Fetches 2026 Brewers schedule from MLB API
├── generator.py            # LLM copy generation (with mock fallback)
├── export.py               # CRM-ready CSV export for Salesforce
├── images.py               # Downloads real Brewers photos from Wikimedia Commons
├── email_template.html     # Jinja2 email template with hero image support
├── sample_fan_data.csv     # Simulated fan database with segment scores
├── assets/images/          # Downloaded Brewers photos organized by segment
├── sample_outputs/         # Pre-generated email samples for all 4 segments
├── generate_samples.py     # Script to regenerate sample outputs
├── brief.md                # Written brief — how to build the real thing
├── pyproject.toml          # Project config & dependencies
└── README.md
```

## Tech Stack

| Tool | Role |
|---|---|
| [Streamlit](https://streamlit.io/) | Interactive UI for marketers |
| [OpenAI API](https://platform.openai.com/) | Email copy generation (optional) |
| [Pandas](https://pandas.pydata.org/) | Data handling & CSV export |
| [Jinja2](https://jinja.palletsprojects.com/) | Email HTML templating |
| [uv](https://docs.astral.sh/uv/) | Dependency management |

## Image Assets

Hero images are real Milwaukee Brewers / American Family Field photos sourced from **Wikimedia Commons** (Creative Commons licensed). The `images.py` script downloads and organizes them by segment:

- **Die-Hard:** Sold-out crowds, celebration moments, home plate views
- **Foodie:** Famous Sausage Race, Bernie Brewer's chalet, ballpark concourse
- **Family:** Helfaer Field (kids' park), American Family Field exterior, Barrelman mascot
- **Social:** Fireworks night, Miller Park glowing at night, crowd entertainment

To re-download images: `uv run python images.py`

## Integration Notes

- **Salesforce Marketing Cloud**: The CSV export maps directly to a Data Extension that Journey Builder can consume.
- **Adobe Creative Cloud**: The email template is designed to be editable in Adobe Campaign / AEM; image assets are composited from approved public sources.

See [brief.md](brief.md) for the full integration architecture.

---

## License

Internal prototype — Milwaukee Brewers.
