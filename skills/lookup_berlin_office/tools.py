"""Fetch Rasa Berlin office guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_berlin_office = notion_page_tool(
    name="get_berlin_office",
    source="berlin_office",
    description=(
        "Fetch Rasa's Working from Berlin Office page from Notion. Call for "
        "Berlin HQ desks, access, wifi, visitors, or day-to-day office "
        "guidance."
    ),
    docstring="Return live Berlin office guidance for employee questions.",
    query_doc="The topic (e.g. access, desk, wifi, visitors).",
    instruction=(
        "Answer the Berlin-office question using only source_content. Keep it "
        "short and Slack-friendly. Use exact "
        "office/access details from the page - never invent them. Always share "
        "source_url. If content_truncated is true and the answer is not here, "
        "check other_sections and say what you could not confirm. If the answer "
        "is not on the page, say so and point to source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to check Working from Berlin Office "
        "there. Do not invent access rules, desk policies, or office details."
    ),
)
