"""Fetch Rasa CrowdStrike FAQ guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_crowdstrike_info = notion_page_tool(
    name="get_crowdstrike_info",
    source="crowdstrike",
    description=(
        "Fetch Rasa's Crowdstrike Notion page. Call for what CrowdStrike is, "
        "whether it tracks web browsing, who has access, or related EDR "
        "questions."
    ),
    docstring="Return live CrowdStrike FAQ content for employee questions.",
    query_doc="Topic (e.g. what is it, web browsing, who has access).",
    instruction=(
        "Answer the CrowdStrike question using only source_content. Keep it "
        "short and Slack-friendly. Never invent "
        "what is monitored or who has access. Always share source_url. If "
        "content_truncated is true and the answer is not here, check "
        "other_sections and say what you could not confirm. If the answer is "
        "not on the page, say so and point to source_url (and #security if "
        "useful)."
    ),
    failure_instruction=(
        "Share source_url and ask them to check the Crowdstrike page there. Do "
        "not invent monitoring scope or access lists."
    ),
)
