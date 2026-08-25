"""Fetch working-from-other-countries guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_work_abroad_guidance = notion_page_tool(
    name="get_work_abroad_guidance",
    source="work_abroad",
    description=(
        "Fetch Rasa policy on working from other countries / working abroad "
        "from the designated Notion page. Call for every work-abroad request."
    ),
    docstring="Return live working-abroad guidance from Notion.",
    query_doc=(
        'The destination and duration when known '
        '(e.g. "a few weeks in Denmark", "one month in South Africa").'
    ),
    instruction=(
        "Answer whether / how they can work from another country using only "
        "source_content. Keep it short and Slack-friendly. Never invent day "
        "limits, approval steps, visa, immigration, or tax advice beyond the "
        "page. Always share source_url. If the page says to ask People Ops or a "
        "manager, say that clearly."
    ),
    failure_instruction=(
        "Share source_url and ask them to follow the policy there. Do not invent "
        "approval rules, day limits, visa, or tax advice."
    ),
)
