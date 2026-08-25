"""Fetch Rasa sexual harassment policy guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_sexual_harassment_policy = notion_page_tool(
    name="get_sexual_harassment_policy",
    source="sexual_harassment",
    description=(
        "Fetch Rasa's Sexual Harassment Policy from Notion. Call for "
        "definitions, how to report, investigation process, or related "
        "workplace sexual harassment questions."
    ),
    docstring="Return the live sexual harassment policy for employee questions.",
    query_doc="The topic (e.g. definition, how to report, investigation).",
    instruction=(
        "Answer the sexual-harassment-policy question using only source_content. "
        "Keep it short and Slack-friendly. Use exact definitions, reporting "
        "paths, and process details from the page - never invent or combine "
        "them. Do not pressure the person to share private details in Slack; "
        "point them to the official path on the page. Always share source_url. "
        "If content_truncated is true and the answer is not here, check "
        "other_sections and say what you could not confirm. If the answer is "
        "not on the page, say so and point to source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to follow the Sexual Harassment Policy "
        "there. Do not invent reporting channels, timelines, or outcomes."
    ),
)
