"""Convert brief.md to a styled PDF. Run: uv run python make_pdf.py"""

from __future__ import annotations
import re
from fpdf import FPDF

NAVY = (18, 40, 75)     # Brewers navy
GOLD = (255, 199, 44)   # Brewers gold
BLACK = (34, 34, 34)
GRAY = (100, 100, 100)


def sanitize(text: str) -> str:
    """Replace Unicode chars that latin-1 can't encode."""
    return (
        text
        .replace("\u2014", "--")   # em dash
        .replace("\u2013", "-")    # en dash
        .replace("\u2018", "'")    # left single quote
        .replace("\u2019", "'")    # right single quote
        .replace("\u201c", '"')    # left double quote
        .replace("\u201d", '"')    # right double quote
        .replace("\u2026", "...")  # ellipsis
        .replace("\u2022", "-")    # bullet (we add our own)
    )


class BriefPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "Milwaukee Brewers  |  Tailored Marketing Engine  |  Technical Brief", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def render_brief():
    md_text = open("brief.md").read()
    md_text = sanitize(md_text)
    lines = md_text.split("\n")

    pdf = BriefPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            pdf.ln(3)
            continue

        # Horizontal rules
        if stripped.startswith("---"):
            y = pdf.get_y()
            pdf.set_draw_color(*GRAY)
            pdf.line(10, y, 200, y)
            pdf.ln(6)
            continue

        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(0, 9, stripped.lstrip("# "))
            pdf.ln(2)
            continue

        # H2
        if stripped.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(0, 8, stripped.lstrip("# "))
            pdf.ln(2)
            continue

        # Bold paragraph headers like **Something:**
        if stripped.startswith("**") and stripped.endswith("**"):
            text = stripped.strip("*")
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(0, 6, text)
            pdf.ln(1)
            continue

        # Bullet points
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:]
            pdf.set_x(15)
            # Handle bold prefix in bullets like **Word.** rest
            bold_match = re.match(r"\*\*(.+?)\*\*\s*(.*)", text, re.DOTALL)
            if bold_match:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*NAVY)
                pdf.write(6, "-  " + bold_match.group(1) + " ")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*BLACK)
                pdf.multi_cell(0, 6, bold_match.group(2))
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*BLACK)
                pdf.multi_cell(0, 6, "-  " + text)
            pdf.ln(1)
            continue

        # Numbered lists
        num_match = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.*)", stripped)
        if num_match:
            pdf.set_x(15)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*NAVY)
            pdf.write(6, f"{num_match.group(1)}. {num_match.group(2)} ")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.multi_cell(0, 6, num_match.group(3))
            pdf.ln(1)
            continue

        # Regular paragraph — strip markdown bold/italic markers for clean text
        text = stripped
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
        text = re.sub(r"\*(.+?)\*", r"\1", text)       # italic
        text = re.sub(r"`(.+?)`", r"\1", text)         # code
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*BLACK)
        pdf.multi_cell(0, 6, text)
        pdf.ln(1)

    pdf.output("brief.pdf")
    print("brief.pdf created")


if __name__ == "__main__":
    render_brief()
