"""Fetch Rasa travel insurance policy guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_travel_insurance_policy = notion_page_tool(
    name="get_travel_insurance_policy",
    source="travel_insurance",
    description=(
        "Fetch Rasa's Travel Insurances 2026 policy from Notion. Call for "
        "business travel cover, claims, certificates, or other travel "
        "insurance questions."
    ),
    docstring="Return the live travel insurance policy for employee questions.",
    query_doc=(
        "The travel insurance topic (e.g. business trip cover, claim, "
        "certificate)."
    ),
    instruction=(
        "Answer the travel insurance question using only source_content. Keep it "
        "short and Slack-friendly. Use exact coverage, eligibility, claim, and "
        "certificate details from the page - never invent or combine them. Always "
        "share source_url. If content_truncated is true and the answer is not "
        "here, check other_sections and say what you could not confirm. If the "
        "answer is not on the page, say so and point to source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to follow the travel insurance policy "
        "there. Do not invent coverage, claim steps, or certificates."
    ),
)
