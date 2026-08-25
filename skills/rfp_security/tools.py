"""Fetch vendor / RFP security questionnaire answers from the Notion bank."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_rfp_security_answers = notion_page_tool(
    name="get_rfp_security_answers",
    source="rfp_security",
    description=(
        "Fetch Rasa's Vendor Security Questionnaire Bank from Notion. Call "
        "for RFP, RFI, vendor security questionnaire, or security-assurance "
        "wording when no dedicated policy_* skill applies."
    ),
    docstring="Return the vendor security questionnaire bank for answers.",
    query_doc=(
        "The security topic or questionnaire question to look up "
        "(e.g. 'SOC 2', 'encryption at rest', 'penetration testing')."
    ),
    instruction=(
        "Help draft or locate a vendor/RFP/RFI security answer using only "
        "source_content. Quote or lightly adapt approved bank wording; never "
        "invent certifications, controls, timelines, or audit results that are "
        "not in the bank. Always tell them to open source_url and double-check "
        "the source before using the answer externally. If nothing matches, say "
        "so and share source_url or suggest #security. If content_truncated is "
        "true, mention other_sections when relevant. Keep the Slack reply "
        "concise; offer to paste a fuller draft if they want it. Always share "
        "source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to check the Vendor Security Questionnaire "
        "Bank there. Do not invent questionnaire answers or security claims."
    ),
    char_limit=8000,
)
