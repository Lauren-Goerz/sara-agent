"""Fetch Rasa Germany/Berlin relocation guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

_RELATED = [
    {
        "key": "relocation_germany",
        "title": "Relocation Guide Germany",
        "url": notion_sources.SOURCES["relocation_germany"].url,
    },
    {
        "key": "welcome_berlin",
        "title": "Welcome to Berlin",
        "url": notion_sources.SOURCES["welcome_berlin"].url,
    },
    {
        "key": "working_in_germany",
        "title": "Overview: Working in Germany",
        "url": notion_sources.SOURCES["working_in_germany"].url,
    },
]

_PAGE_HINTS = (
    (
        "welcome_berlin",
        (
            "berlin",
            "welcome",
            "neighborhood",
            "neighbourhood",
            "apartment",
            "flat",
            "anmeldung",
            "housing",
            "city",
            "life",
        ),
    ),
    (
        "working_in_germany",
        (
            "working",
            "employment",
            "tax",
            "taxes",
            "contract",
            "payroll",
            "social security",
            "insurance",
            "salary",
            "arbeit",
        ),
    ),
    (
        "relocation_germany",
        (
            "relocation",
            "relocate",
            "move",
            "moving",
            "visa",
            "permit",
            "shipping",
            "package",
            "germany",
        ),
    ),
)

_SUCCESS = (
    "Answer the relocation question using only source_content. Keep it "
    "short and Slack-friendly. Always share "
    "all three related_urls at the end. Never invent visa, immigration, "
    "tax, or housing advice. If content_truncated is true and the answer "
    "is not here, check other_sections and say what you could not confirm. "
    "If the answer is not on this page, say so and point people to the "
    "related_urls."
)
_FAILURE = (
    "Share all three related_urls and ask them to start with the Relocation "
    "Guide Germany. Do not invent visa, immigration, tax, or housing advice."
)


def _pick_source_key(query: str) -> str:
    text = (query or "").strip().lower()
    if not text:
        return "relocation_germany"
    for key, hints in _PAGE_HINTS:
        if any(hint in text for hint in hints):
            return key
    return "relocation_germany"


@tool(
    description=(
        "Fetch Rasa Germany/Berlin relocation guidance from Notion. Picks "
        "Relocation Guide, Welcome to Berlin, or Working in Germany based "
        "on the query. Call for relocating to Berlin/Germany."
    )
)
async def get_relocation_germany(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the best-matching Germany relocation page for the question.

    Args:
        query: Topic (e.g. visa, Anmeldung, neighborhoods, taxes, package).
    """
    source_key = _pick_source_key(query)
    payload = await notion_sources.load(source_key, query=query)
    payload["selected_page"] = source_key
    payload["related_urls"] = _RELATED
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
