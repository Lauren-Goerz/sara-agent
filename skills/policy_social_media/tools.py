"""Fetch Rasa social media policy guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_social_media_policy = notion_page_tool(
    name="get_social_media_policy",
    source="social_media",
    description=(
        "Fetch Rasa's Social Media Policy from Notion. Call for questions "
        "about posting on LinkedIn, X/Twitter, private accounts, or other "
        "employee social media rules."
    ),
    docstring="Return the live social media policy for answering employee questions.",
    query_doc=(
        "The social media question or topic (e.g. LinkedIn post about "
        "Rasa, private Twitter/X account)."
    ),
    instruction=(
        "Answer the social media question using only source_content. Keep it "
        "short and Slack-friendly. Never invent permissions or prohibitions. "
        "Always share source_url. If the answer is not on the page, say so and "
        "point to source_url or whoever the policy names."
    ),
    failure_instruction=(
        "Share source_url and ask them to follow the policy there. Do not invent "
        "posting rules."
    ),
)
