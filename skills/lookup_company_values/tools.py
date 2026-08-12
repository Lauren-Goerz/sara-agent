"""Fetch official Rasa company values from the designated Notion page."""

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
    "List every company value from source_content with its short "
    "description. Use the exact value names from the page. Do not invent "
    "values or paraphrase them into new ones. Always share source_url."
)
_FAILURE = (
    "Share source_url and say you cannot load the values right now. Do not "
    "guess or quote an outdated list."
)


@tool(
    description=(
        "Fetch Rasa's official company values from the designated Notion page. "
        "Call for every company-values request."
    )
)
async def get_company_values(context: ToolContext = None) -> ToolResult:
    """Return the live company-values page content."""
    payload = await notion_sources.load("company_values", char_limit=8000)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
