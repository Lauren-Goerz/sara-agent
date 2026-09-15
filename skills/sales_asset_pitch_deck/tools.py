"""Fetch the standard pitch deck link from the Pitch Decks Notion page."""

from __future__ import annotations

import re

import httpx
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import notion_client

PITCH_DECKS_PAGE_ID = "24db9c0d544a80278370e2d100f4e3d4"
PITCH_DECKS_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Pitch-Decks-24db9c0d544a80278370e2d100f4e3d4"
)

_SLIDES_RE = re.compile(
    r"https://docs\.google\.com/presentation/d/[^\s\]>?]+",
    re.IGNORECASE,
)
_FAILURE = (
    "Share source_url and say the live pitch-deck link is unavailable right "
    "now. Do not invent a Google Slides URL."
)


def _clean_url(url: str) -> str:
    return url.rstrip(").,]>\"'")


def _section_slides(body: str) -> list[tuple[str, str]]:
    """Return [(section_title, slides_url), ...] in page order."""
    current = "Pitch Decks"
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in (body or "").splitlines():
        if line.startswith("## "):
            current = line[3:].strip() or current
            continue
        for match in _SLIDES_RE.finditer(line):
            url = _clean_url(match.group(0))
            if url in seen:
                continue
            seen.add(url)
            found.append((current, url))
    return found


def _pick_standard(sections: list[tuple[str, str]]) -> tuple[str, str] | None:
    """Prefer the L1 / standard deck; otherwise the first Google Slides link."""
    for title, url in sections:
        low = title.lower()
        if "l1" in low or "standard" in low:
            return title, url
    return sections[0] if sections else None


@tool(
    description=(
        "Fetch Rasa's standard (L1) pitch deck Google Slides link from the "
        "Pitch Decks Notion page, plus the Notion page URL for talk tracks "
        "and other decks."
    )
)
async def get_pitch_deck(context: ToolContext = None) -> ToolResult:
    """Return the standard pitch deck URL and Pitch Decks Notion page."""
    try:
        page = await notion_client.get_page_with_body(
            PITCH_DECKS_PAGE_ID,
            max_blocks=200,
        )
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "source_url": PITCH_DECKS_PAGE_URL,
                "instruction": _FAILURE,
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_page_unavailable",
                "status_code": exc.response.status_code,
                "message": (
                    "The Pitch Decks page is not visible to Sara's Notion "
                    "integration. Share the page with the integration and retry."
                ),
                "source_url": PITCH_DECKS_PAGE_URL,
                "instruction": _FAILURE,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "message": str(exc),
                "source_url": PITCH_DECKS_PAGE_URL,
                "instruction": _FAILURE,
            }
        )

    sections = _section_slides(str(page.get("body") or ""))
    if not sections:
        # Fallback: attachment list from Notion file/link blocks.
        for item in page.get("attachments") or []:
            url = _clean_url(str(item.get("url") or ""))
            if "docs.google.com/presentation" in url.lower():
                sections.append((str(item.get("name") or "Pitch deck"), url))

    chosen = _pick_standard(sections)
    if not chosen:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "deck_link_missing",
                "message": "No Google Slides pitch deck link found on the page.",
                "source_url": PITCH_DECKS_PAGE_URL,
                "instruction": _FAILURE,
            }
        )

    title, deck_url = chosen
    other = [
        {"title": section_title, "url": url}
        for section_title, url in sections
        if url != deck_url
    ]
    return ToolResult(
        llm_response={
            "ok": True,
            "page_title": page.get("title") or "Pitch Decks",
            "standard_deck_label": title,
            "standard_deck_url": deck_url,
            "other_decks": other,
            "source_url": PITCH_DECKS_PAGE_URL,
            "instruction": (
                "Share standard_deck_url as the main pitch deck, then "
                "source_url for talk tracks and additional decks. Keep it to "
                "one short Slack message. Do not invent extra slide links."
            ),
        }
    )
