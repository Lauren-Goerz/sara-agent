"""Fetch Rasa employee handbooks (by country) from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_employee_handbooks = notion_page_tool(
    name="get_employee_handbooks",
    source="employee_handbooks",
    description=(
        "Fetch Rasa's Employee Handbooks Notion page (official handbooks "
        "by country). Call when someone asks for an employee/staff handbook "
        "or whether their country has one."
    ),
    docstring="Return the live employee handbooks index for country lookups.",
    query_doc="Country or topic (e.g. Germany, US, Ireland, handbook).",
    instruction=(
        "Answer using only source_content. Official employee handbooks exist "
        "only for countries listed on the page - share the matching country "
        "link(s) when present. If their country is not listed, say so clearly. "
        "Never invent a handbook or country. Always share source_url. Do not "
        "append a follow-up question or offer other topics. If "
        "content_truncated is true and the answer is not here, check "
        "other_sections and say what you could not confirm."
    ),
    failure_instruction=(
        "Share source_url and ask them to check which countries have an "
        "official handbook there. Do not invent countries or handbook links. "
        "Do not append a follow-up question or offer other topics."
    ),
)
