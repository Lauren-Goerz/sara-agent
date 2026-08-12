"""Fetch Rasa board membership from the designated Notion page."""

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
    "List who is on the Rasa board using only source_content. Include "
    "roles/affiliations when present. Keep it short and Slack-friendly. "
    "Never invent people or titles. Always share source_url."
)
_FAILURE = "Share source_url. Do not invent board members."


@tool(
    description=(
        "Fetch who is on the Rasa board from the designated Notion Board "
        "page. Call for every board-membership question."
    )
)
async def get_rasa_board(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live board membership information.

    Args:
        query: Optional focus, e.g. a specific director name or role.
    """
    payload = await notion_sources.load("board", query=query, char_limit=8000)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
