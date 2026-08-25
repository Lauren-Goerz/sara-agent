"""Fetch employer benefits and perks from the designated Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_benefits_and_perks = notion_page_tool(
    name="get_benefits_and_perks",
    source="benefits",
    description=(
        "Fetch Rasa employer benefits and perks for 2026 from the designated "
        "Notion page - gym, wellness, equipment, learning, and similar. Call "
        "for every benefits or perks question."
    ),
    docstring="Return live benefits/perks guidance from Notion.",
    query_doc=(
        "The benefit or perk the person asked about, when known "
        "(e.g. gym membership, wellness, learning budget)."
    ),
    instruction=(
        "Answer the benefits/perks question using only source_content. Keep it "
        "short and Slack-friendly. Use exact amounts, eligibility, and country "
        "notes from the page - never invent or combine them. Always share "
        "source_url. If content_truncated is true and the answer is not here, "
        "check other_sections and say what you could not confirm. If the answer "
        "is not on the page, say so and point to source_url / People Ops."
    ),
    failure_instruction=(
        "Share source_url and say you cannot load benefits right now. Do not "
        "invent benefit amounts, eligibility, or country rules."
    ),
)
