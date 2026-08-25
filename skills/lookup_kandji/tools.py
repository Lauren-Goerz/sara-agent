"""Fetch Rasa Kandji / Iru FAQ guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_kandji_info = notion_page_tool(
    name="get_kandji_info",
    source="kandji",
    description=(
        "Fetch Rasa's Kandji / Iru Notion page. Call for what Kandji/Iru is, "
        "keystroke tracking concerns, who has access, or Mac MDM questions."
    ),
    docstring="Return live Kandji/Iru FAQ content for employee questions.",
    query_doc="Topic (e.g. what is it, keystrokes, who has access).",
    instruction=(
        "Answer the Kandji/Iru question using only source_content. Keep it "
        "short and Slack-friendly. Never invent "
        "what is monitored or who has access. Always share source_url. If "
        "content_truncated is true and the answer is not here, check "
        "other_sections and say what you could not confirm. If the answer is "
        "not on the page, say so and point to source_url (and #security if "
        "useful)."
    ),
    failure_instruction=(
        "Share source_url and ask them to check the Kandji / Iru page there. Do "
        "not invent monitoring scope or access lists."
    ),
)
