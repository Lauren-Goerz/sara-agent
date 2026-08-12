"""Look up official company details from the designated Notion page."""

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
    "Answer only the requested item using the exact value in source_content. "
    "Include enough entity, office, or country context to disambiguate it. "
    "Never infer or complete a value. Then tell the user to double-check it "
    "on source_url."
)
_FAILURE = (
    "Share source_url and tell them to check the details there. Never guess "
    "an address, VAT number, IBAN, or phone number."
)


@tool(
    description=(
        "Fetch live official Rasa company details from the designated Notion "
        "page, including addresses, VAT numbers, IBANs, banking details, and "
        "phone numbers. Call for every company-information request."
    )
)
async def lookup_company_information(
    query: str,
    context: ToolContext = None,
) -> ToolResult:
    """Fetch the authoritative company-information page.

    Args:
        query: The exact company detail requested, including an office, country,
            or legal entity when the user specified one.
    """
    payload = await notion_sources.load(
        "company_info",
        query=query,
        char_limit=8000,
    )
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
