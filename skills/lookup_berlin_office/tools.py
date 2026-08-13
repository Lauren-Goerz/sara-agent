"""Fetch Rasa Berlin office guidance from Notion."""

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
    "Answer the Berlin-office question using only source_content. Keep it "
    "short and Slack-friendly. Use exact "
    "office/access details from the page - never invent them. Always share "
    "source_url. If content_truncated is true and the answer is not here, "
    "check other_sections and say what you could not confirm. If the answer "
    "is not on the page, say so and point to source_url."
)
_FAILURE = (
    "Share source_url and ask them to check Working from Berlin Office "
    "there. Do not invent access rules, desk policies, or office details."
)


@tool(
    description=(
        "Fetch Rasa's Working from Berlin Office page from Notion. Call for "
        "Berlin HQ desks, access, wifi, visitors, or day-to-day office "
        "guidance."
    )
)
async def get_berlin_office(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live Berlin office guidance for employee questions.

    Args:
        query: The topic (e.g. access, desk, wifi, visitors).
    """
    payload = await notion_sources.load("berlin_office", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
