"""Fetch Rasa sexual harassment policy guidance from Notion."""

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
    "Answer the sexual-harassment-policy question using only source_content. "
    "Keep it short and Slack-friendly. Use exact definitions, reporting "
    "paths, and process details from the page - never invent or combine "
    "them. Do not pressure the person to share private details in Slack; "
    "point them to the official path on the page. Always share source_url. "
    "If content_truncated is true and the answer is not here, check "
    "other_sections and say what you could not confirm. If the answer is "
    "not on the page, say so and point to source_url."
)
_FAILURE = (
    "Share source_url and ask them to follow the Sexual Harassment Policy "
    "there. Do not invent reporting channels, timelines, or outcomes."
)


@tool(
    description=(
        "Fetch Rasa's Sexual Harassment Policy from Notion. Call for "
        "definitions, how to report, investigation process, or related "
        "workplace sexual harassment questions."
    )
)
async def get_sexual_harassment_policy(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the live sexual harassment policy for employee questions.

    Args:
        query: The topic (e.g. definition, how to report, investigation).
    """
    payload = await notion_sources.load("sexual_harassment", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
