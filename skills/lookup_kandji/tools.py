"""Fetch Rasa Kandji / Iru FAQ guidance from Notion."""

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
    "Answer the Kandji/Iru question using only source_content. Keep it "
    "short and Slack-friendly. Never invent "
    "what is monitored or who has access. Always share source_url. If "
    "content_truncated is true and the answer is not here, check "
    "other_sections and say what you could not confirm. If the answer is "
    "not on the page, say so and point to source_url (and #security if "
    "useful)."
)
_FAILURE = (
    "Share source_url and ask them to check the Kandji / Iru page there. Do "
    "not invent monitoring scope or access lists."
)


@tool(
    description=(
        "Fetch Rasa's Kandji / Iru Notion page. Call for what Kandji/Iru is, "
        "keystroke tracking concerns, who has access, or Mac MDM questions."
    )
)
async def get_kandji_info(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live Kandji/Iru FAQ content for employee questions.

    Args:
        query: Topic (e.g. what is it, keystrokes, who has access).
    """
    payload = await notion_sources.load("kandji", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
