"""Fetch Rasa security-incident status from the designated Notion source."""

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
    "Answer only from source_content. If query names a specific "
    "incident/CVE/vendor (e.g. Trivy, supply chain, RCE), say whether it "
    "appears in the tracker and what the record says about Rasa impact or "
    "status. If nothing matches, say it is not listed in the tracker and "
    "share source_url - never invent an all-clear or a breach. For broad "
    "'any security incidents' asks, summarize only what the tracker contains "
    "at a high level. Keep it short and factual. Always share source_url."
)
_FAILURE = (
    "Share source_url and say you cannot confirm impact from the tracker "
    "right now. Do not invent incidents or say Rasa was or was not affected."
)


@tool(
    description=(
        "Fetch Rasa's security incidents / vulnerability-impact tracker from "
        "Notion. Call for questions like whether Rasa had security incidents, "
        "was affected by Trivy/supply-chain compromises, RCE CVEs, or similar."
    )
)
async def get_security_incident_status(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return live security-incident records for answering impact questions.

    Args:
        query: The incident, CVE, vendor, or vulnerability the person asked
            about (e.g. 'Trivy supply chain', 'remote code execution').
    """
    payload = await notion_sources.load(
        "security_incidents",
        query=query,
        char_limit=7000,
    )
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
