"""Fetch Rasa social media policy guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

_SUCCESS = (
    "Answer the social media question using only source_content. Keep it "
    "short and Slack-friendly. Never invent permissions or prohibitions. "
    "Always share source_url. If the answer is not on the page, say so and "
    "point to source_url or whoever the policy names."
)
_FAILURE = (
    "Share source_url and ask them to follow the policy there. Do not invent "
    "posting rules."
)


@tool(
    description=(
        "Fetch Rasa's Social Media Policy from Notion. Call for questions "
        "about posting on LinkedIn, X/Twitter, private accounts, or other "
        "employee social media rules."
    )
)
async def get_social_media_policy(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the live social media policy for answering employee questions.

    Args:
        query: The social media question or topic (e.g. LinkedIn post about
            Rasa, private Twitter/X account).
    """
    payload = await notion_sources.load("social_media", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
