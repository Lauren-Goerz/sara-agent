"""Fetch official Rasa company values from the designated Notion page."""

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

COMPANY_VALUES_PAGE_ID = "f3afec52e31742f292f9a776d4ef712d"
COMPANY_VALUES_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Rasa-s-Company-Values-f3afec52e31742f292f9a776d4ef712d"
)


def _clean_body(body: str) -> str:
    """Drop file/link lines whose signed URLs crowd out readable text."""
    lines = [
        line
        for line in body.splitlines()
        if not line.startswith("[file]") and not line.startswith("[link]")
    ]
    return "\n".join(lines).strip()


@tool(
    description=(
        "Fetch Rasa's official company values from the designated Notion page. "
        "Call for every company-values request."
    )
)
async def get_company_values(context: ToolContext = None) -> ToolResult:
    """Return the live company-values page content."""
    try:
        page = await notion_client.get_page_with_body(
            COMPANY_VALUES_PAGE_ID,
            max_blocks=200,
        )
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "source_url": COMPANY_VALUES_PAGE_URL,
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_page_unavailable",
                "status_code": exc.response.status_code,
                "message": (
                    "The company values page is not visible to Sara's Notion "
                    "integration. Share the page with the integration and retry."
                ),
                "source_url": COMPANY_VALUES_PAGE_URL,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "message": str(exc),
                "source_url": COMPANY_VALUES_PAGE_URL,
            }
        )

    source_content = _clean_body(page.get("body") or "")
    return ToolResult(
        llm_response={
            "ok": True,
            "page_title": page["title"],
            "last_edited_time": page.get("last_edited_time"),
            "source_url": COMPANY_VALUES_PAGE_URL,
            "source_content": source_content,
            "instruction": (
                "List every company value from source_content with its short "
                "description. Use the exact value names from the page. Do not "
                "invent values or paraphrase them into new ones. Always share "
                "source_url."
            ),
        }
    )
