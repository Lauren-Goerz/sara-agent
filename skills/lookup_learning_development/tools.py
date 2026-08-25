"""Fetch Rasa Learning & Development guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_learning_development = notion_page_tool(
    name="get_learning_development",
    source="learning_development",
    description=(
        "Fetch Rasa's Learning & Development page from Notion. Call for "
        "education days, learning/L&D budget, recommended budget uses, "
        "courses, training, or conferences."
    ),
    docstring="Return live Learning & Development guidance for employee questions.",
    query_doc="The topic (e.g. education days, budget, recommended uses).",
    instruction=(
        "Answer the Learning & Development question using only source_content. "
        "Keep it short and Slack-friendly. Use exact education-day counts, "
        "budget amounts, eligibility, and recommended uses from the page - "
        "never invent or combine them. Always share source_url. If "
        "content_truncated is true and the answer is not here, check "
        "other_sections and say what you could not confirm. If the answer is "
        "not on the page, say so and point to source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to check Learning & Development there. "
        "Do not invent education days, budget amounts, or approved uses."
    ),
)
