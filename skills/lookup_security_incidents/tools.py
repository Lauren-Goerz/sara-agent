"""Fetch Rasa security-incident status from the designated Notion source."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_security_incident_status = notion_page_tool(
    name="get_security_incident_status",
    source="security_incidents",
    description=(
        "Fetch Rasa's security incidents / vulnerability-impact tracker from "
        "Notion. Call for questions like whether Rasa had security incidents, "
        "was affected by Trivy/supply-chain compromises, RCE CVEs, or similar."
    ),
    docstring="Return live security-incident records for answering impact questions.",
    query_doc=(
        "The incident, CVE, vendor, or vulnerability the person asked "
        "about (e.g. 'Trivy supply chain', 'remote code execution')."
    ),
    instruction=(
        "Answer only from source_content. If query names a specific "
        "incident/CVE/vendor (e.g. Trivy, supply chain, RCE), say whether it "
        "appears in the tracker and what the record says about Rasa impact or "
        "status. If nothing matches, say it is not listed in the tracker and "
        "share source_url - never invent an all-clear or a breach. For broad "
        "'any security incidents' asks, summarize only what the tracker contains "
        "at a high level. Keep it short and factual. Always share source_url."
    ),
    failure_instruction=(
        "Share source_url and say you cannot confirm impact from the tracker "
        "right now. Do not invent incidents or say Rasa was or was not affected."
    ),
    char_limit=7000,
)
