"""Fetch Rasa board membership from the designated Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_rasa_board = notion_page_tool(
    name="get_rasa_board",
    source="board",
    description=(
        "Fetch who is on the Rasa board from the designated Notion Board "
        "page. Call for every board-membership question."
    ),
    docstring="Return live board membership information.",
    query_doc="Optional focus, e.g. a specific director name or role.",
    instruction=(
        "List who is on the Rasa board using only source_content. Include "
        "roles/affiliations when present. Keep it short and Slack-friendly. "
        "Never invent people or titles. Always share source_url."
    ),
    failure_instruction="Share source_url. Do not invent board members.",
    char_limit=8000,
)
