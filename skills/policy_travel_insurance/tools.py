"""Fetch Rasa travel insurance policy guidance from Notion."""

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
    "Answer the travel insurance question using only source_content. Keep it "
    "short and Slack-friendly. Use exact coverage, eligibility, claim, and "
    "certificate details from the page - never invent or combine them. Always "
    "share source_url. If content_truncated is true and the answer is not "
    "here, check other_sections and say what you could not confirm. If the "
    "answer is not on the page, say so and point to source_url."
)
_FAILURE = (
    "Share source_url and ask them to follow the travel insurance policy "
    "there. Do not invent coverage, claim steps, or certificates."
)


@tool(
    description=(
        "Fetch Rasa's Travel Insurances 2026 policy from Notion. Call for "
        "business travel cover, claims, certificates, or other travel "
        "insurance questions."
    )
)
async def get_travel_insurance_policy(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the live travel insurance policy for employee questions.

    Args:
        query: The travel insurance topic (e.g. business trip cover, claim,
            certificate).
    """
    payload = await notion_sources.load("travel_insurance", query=query)
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
