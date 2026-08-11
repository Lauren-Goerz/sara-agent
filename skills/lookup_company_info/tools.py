"""Look up official company details from the designated Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_client  # noqa: E402

COMPANY_INFO_PAGE_ID = "44a36a2d9f8745adbc7827769f530906"
COMPANY_INFO_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Rasa-Offices-banking-important-info-44a36a2d9f8745adbc7827769f530906"
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
    try:
        page = await notion_client.get_page_with_body(
            COMPANY_INFO_PAGE_ID,
            max_blocks=500,
        )
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "source_url": COMPANY_INFO_PAGE_URL,
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_page_unavailable",
                "status_code": exc.response.status_code,
                "message": (
                    "The company information page is not visible to Sara's "
                    "Notion integration. Share the page with the integration "
                    "and retry."
                ),
                "source_url": COMPANY_INFO_PAGE_URL,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "message": str(exc),
                "source_url": COMPANY_INFO_PAGE_URL,
            }
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "query": query,
            "page_title": page["title"],
            "last_edited_time": page.get("last_edited_time"),
            "source_url": COMPANY_INFO_PAGE_URL,
            "source_content": page["body"],
            "instruction": (
                "Answer only the requested item using the exact value in "
                "source_content. Include enough entity, office, or country "
                "context to disambiguate it. Never infer or complete a value. "
                "Then tell the user to double-check it on source_url."
            ),
        }
    )
