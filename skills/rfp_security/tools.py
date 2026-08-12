"""Fetch RFP/RFI security questionnaire answers from the Notion bank."""

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
    "Help draft or locate an RFP/RFI security answer using only "
    "source_content. Quote or lightly adapt approved bank wording; never "
    "invent certifications, controls, timelines, or audit results that are "
    "not in the bank. If nothing matches, say so and share source_url or "
    "suggest Security / the questionnaire owners. If content_truncated is "
    "true, mention other_sections when relevant. Keep the Slack reply "
    "concise; offer to paste a fuller draft if they want it. Always share "
    "source_url."
)
_FAILURE = (
    "Share source_url. Do not invent questionnaire answers or security "
    "claims."
)


@tool(
    description=(
        "Fetch Rasa's Customer Information Security Questionnaires / RFP "
        "security question bank from Notion. Call for RFP, RFI, security "
        "questionnaire, or customer security-assurance answer requests."
    )
)
async def get_rfp_security_answers(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the security questionnaire bank for RFP/RFI answers.

    Args:
        query: The security topic or questionnaire question to look up
            (e.g. 'SOC 2', 'encryption at rest', 'penetration testing').
    """
    payload = await notion_sources.load(
        "rfp_security",
        query=query,
        char_limit=8000,
    )
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
