"""Fetch working-from-other-countries guidance from Notion."""

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
    "Answer whether / how they can work from another country using only "
    "source_content. Keep it short and Slack-friendly. Never invent day "
    "limits, approval steps, visa, immigration, or tax advice beyond the "
    "page. Always share source_url. If the page says to ask People Ops or a "
    "manager, say that clearly."
)
_FAILURE = (
    "Share source_url and ask them to follow the policy there. Do not invent "
    "approval rules, day limits, visa, or tax advice."
)


@tool(
    description=(
        "Fetch Rasa policy on working from other countries / working abroad "
        "from the designated Notion page. Call for every work-abroad request."
    )
)
async def get_work_abroad_guidance(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live working-abroad guidance from Notion.

    Args:
        query: The destination and duration when known
            (e.g. "a few weeks in Denmark", "one month in South Africa").
    """
    payload = await notion_sources.load("work_abroad", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
