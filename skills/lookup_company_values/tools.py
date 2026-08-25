"""Fetch official Rasa company values from the designated Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_company_values = notion_page_tool(
    name="get_company_values",
    source="company_values",
    description=(
        "Fetch Rasa's official company values from the designated Notion page. "
        "Call for every company-values request."
    ),
    docstring="Return the live company-values page content.",
    query_doc=None,
    instruction=(
        "List every company value from source_content with its short "
        "description. Use the exact value names from the page. Do not invent "
        "values or paraphrase them into new ones. Always share source_url."
    ),
    failure_instruction=(
        "Share source_url and say you cannot load the values right now. Do not "
        "guess or quote an outdated list."
    ),
    char_limit=8000,
)
