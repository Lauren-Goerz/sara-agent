"""Fetch employer benefits and perks from the designated Notion page."""

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
    "Answer the benefits/perks question using only source_content. Keep it "
    "short and Slack-friendly. Use exact amounts, eligibility, and country "
    "notes from the page - never invent or combine them. Always share "
    "source_url. If content_truncated is true and the answer is not here, "
    "check other_sections and say what you could not confirm. If the answer "
    "is not on the page, say so and point to source_url / People Ops."
)
_FAILURE = (
    "Share source_url and say you cannot load benefits right now. Do not "
    "invent benefit amounts, eligibility, or country rules."
)


@tool(
    description=(
        "Fetch Rasa employer benefits and perks for 2026 from the designated "
        "Notion page - gym, wellness, equipment, learning, and similar. Call "
        "for every benefits or perks question."
    )
)
async def get_benefits_and_perks(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live benefits/perks guidance from Notion.

    Args:
        query: The benefit or perk the person asked about, when known
            (e.g. gym membership, wellness, learning budget).
    """
    payload = await notion_sources.load("benefits", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
