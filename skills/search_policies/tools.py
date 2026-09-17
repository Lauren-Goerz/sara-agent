"""Notion company-doc search for the search_policies skill (live API)."""

from __future__ import annotations

import httpx
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import notion_client


@tool(
    description=(
        "Search Notion for company docs by topic — policies, pitch decks, "
        "handbook pages, etc."
    )
)
async def search_notion_policies(query: str, context: ToolContext = None) -> ToolResult:
    """Search Notion pages shared with the integration.

    Args:
        query: Topic such as pitch deck, PTO, remote work, or onboarding.
    """
    try:
        pages = await notion_client.search_pages(query)
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "hint": str(exc),
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_http_error",
                "status_code": exc.response.status_code,
                "hint": (
                    "Check NOTION_API_KEY and that the pitch deck / handbook "
                    "pages are shared with the Notion integration."
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "hint": str(exc),
            }
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "query": query,
            "result_count": len(pages),
            "pages": pages,
            "hint": (
                None
                if pages
                else (
                    "No matching Notion pages. Share the relevant pages "
                    "(e.g. Pitch Deck) with the Sara integration and retry."
                )
            ),
        }
    )


@tool(
    description=(
        "Fetch the selected Notion page body plus file/link attachments. "
        "Call only after selected_page_id is set."
    )
)
async def get_policy_page(context: ToolContext = None) -> ToolResult:
    """Return live Notion page content and attachments for the selected id."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    page_id = context.memory.get("selected_page_id")
    if not page_id:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_page_selected",
                "hint": "Search Notion and select a page first.",
            }
        )

    try:
        page = await notion_client.get_page_with_body(str(page_id))
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={"ok": False, "error": "not_configured", "hint": str(exc)}
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_http_error",
                "status_code": exc.response.status_code,
                "page_id": page_id,
                "hint": "Confirm the page is shared with the Notion integration.",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={"ok": False, "error": "notion_error", "hint": str(exc)}
        )

    context.memory.set("selected_page_title", page["title"])
    return ToolResult(
        llm_response={
            "ok": True,
            "id": page["id"],
            "title": page["title"],
            "url": page["url"],
            "last_edited_time": page.get("last_edited_time"),
            "body": page["body"],
            "attachments": page.get("attachments") or [],
            "attachment_count": page.get("attachment_count", 0),
        }
    )
