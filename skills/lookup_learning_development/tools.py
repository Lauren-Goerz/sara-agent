"""Fetch Rasa Learning & Development guidance from Notion."""

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
    "Answer the Learning & Development question using only source_content. "
    "Keep it short and Slack-friendly. Use exact education-day counts, "
    "budget amounts, eligibility, and recommended uses from the page - "
    "never invent or combine them. Always share source_url. If "
    "content_truncated is true and the answer is not here, check "
    "other_sections and say what you could not confirm. If the answer is "
    "not on the page, say so and point to source_url."
)
_FAILURE = (
    "Share source_url and ask them to check Learning & Development there. "
    "Do not invent education days, budget amounts, or approved uses."
)


@tool(
    description=(
        "Fetch Rasa's Learning & Development page from Notion. Call for "
        "education days, learning/L&D budget, recommended budget uses, "
        "courses, training, or conferences."
    )
)
async def get_learning_development(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live Learning & Development guidance for employee questions.

    Args:
        query: The topic (e.g. education days, budget, recommended uses).
    """
    payload = await notion_sources.load("learning_development", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
