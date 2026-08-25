"""Look up official company details from the designated Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

lookup_company_information = notion_page_tool(
    name="lookup_company_information",
    source="company_info",
    description=(
        "Fetch live official Rasa company details from the designated Notion "
        "page, including addresses, VAT numbers, IBANs, banking details, and "
        "phone numbers. Call for every company-information request."
    ),
    docstring="Fetch the authoritative company-information page.",
    query_doc=(
        "The exact company detail requested, including an office, country, "
        "or legal entity when the user specified one."
    ),
    query_required=True,
    instruction=(
        "Answer only the requested item using the exact value in source_content. "
        "Include enough entity, office, or country context to disambiguate it. "
        "Never infer or complete a value. Then tell the user to double-check it "
        "on source_url."
    ),
    failure_instruction=(
        "Share source_url and tell them to check the details there. Never guess "
        "an address, VAT number, IBAN, or phone number."
    ),
    char_limit=8000,
)
