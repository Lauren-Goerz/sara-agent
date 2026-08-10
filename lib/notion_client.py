"""Live Notion API helpers for company docs (policies, pitch decks, etc.).

Env:
  NOTION_API_KEY              — workspace integration token (required)
  NOTION_VERSION              — optional API version (default 2022-06-28)

Share every page Sara should see with the integration (⋯ → Connections).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

NOTION_BASE = "https://api.notion.com/v1"
DEFAULT_VERSION = "2022-06-28"


class NotionConfigError(RuntimeError):
    """Missing or invalid Notion configuration."""


def _headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_KEY", "").strip()
    if not token:
        raise NotionConfigError(
            "NOTION_API_KEY is not set. Add your Rasa Notion integration "
            "token to .env (workspace-scoped access token)."
        )
    version = os.environ.get("NOTION_VERSION", DEFAULT_VERSION).strip() or DEFAULT_VERSION
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": version,
        "Content-Type": "application/json",
    }


def configured() -> bool:
    return bool(os.environ.get("NOTION_API_KEY", "").strip())


def _plain_rich_text(rich: list[dict[str, Any]] | None) -> str:
    if not rich:
        return ""
    return "".join(part.get("plain_text", "") for part in rich)


def _page_title(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    for prop in props.values():
        if prop.get("type") == "title":
            return _plain_rich_text(prop.get("title")) or "Untitled"
    # Some pages only expose title via properties with other shapes
    return "Untitled"


def _file_from_payload(payload: dict[str, Any], *, name_hint: str = "") -> dict[str, str] | None:
    """Normalize Notion file / pdf / video / bookmark payloads into a link."""
    caption = _plain_rich_text(payload.get("caption"))
    name = caption or name_hint or "Attachment"

    if payload.get("type") == "file" and isinstance(payload.get("file"), dict):
        url = payload["file"].get("url")
        if url:
            return {"name": name, "url": url, "kind": "file"}
    if payload.get("type") == "external" and isinstance(payload.get("external"), dict):
        url = payload["external"].get("url")
        if url:
            return {"name": name, "url": url, "kind": "external"}

    # bookmark / embed / link_preview
    url = payload.get("url")
    if url:
        return {"name": name or url, "url": url, "kind": "link"}
    return None


async def search_pages(query: str, *, page_size: int = 10) -> list[dict[str, Any]]:
    """Search pages visible to the integration (Notion POST /v1/search).

    Results are sorted with most recently edited first so \"latest\" queries
    prefer current pages.
    """
    payload: dict[str, Any] = {
        "query": query,
        "page_size": page_size,
        "filter": {"property": "object", "value": "page"},
        "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{NOTION_BASE}/search",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    results: list[dict[str, Any]] = []
    for page in data.get("results", []):
        if page.get("object") != "page":
            continue
        results.append(
            {
                "id": page.get("id"),
                "title": _page_title(page),
                "url": page.get("url"),
                "last_edited_time": page.get("last_edited_time"),
                "summary": "Open the page for full content and any attached files.",
            }
        )
    return results


async def _block_to_text(block: dict[str, Any]) -> str:
    btype = block.get("type")
    if not btype:
        return ""
    payload = block.get(btype) or {}
    if "rich_text" in payload:
        text = _plain_rich_text(payload.get("rich_text"))
        if btype.startswith("heading"):
            return f"## {text}" if text else ""
        if btype == "bulleted_list_item":
            return f"- {text}" if text else ""
        if btype == "numbered_list_item":
            return f"1. {text}" if text else ""
        if btype == "to_do":
            mark = "x" if payload.get("checked") else " "
            return f"- [{mark}] {text}" if text else ""
        if btype == "quote":
            return f"> {text}" if text else ""
        if btype == "code":
            return f"```\n{text}\n```" if text else ""
        return text
    if btype == "divider":
        return "---"
    if btype in {"child_page", "child_database"}:
        title = payload.get("title") or "Untitled"
        return f"[{btype}: {title}]"
    if btype in {"file", "pdf", "video", "audio", "image"}:
        info = _file_from_payload(payload, name_hint=btype.upper())
        if info:
            return f"[file] {info['name']}: {info['url']}"
    if btype in {"bookmark", "embed", "link_preview"}:
        info = _file_from_payload(payload, name_hint=btype)
        if info:
            return f"[link] {info['name']}: {info['url']}"
    return ""


def _extract_attachments(blocks: list[dict[str, Any]]) -> list[dict[str, str]]:
    attachments: list[dict[str, str]] = []
    for block in blocks:
        btype = block.get("type")
        if btype not in {
            "file",
            "pdf",
            "video",
            "audio",
            "image",
            "bookmark",
            "embed",
            "link_preview",
        }:
            continue
        payload = block.get(btype) or {}
        info = _file_from_payload(payload, name_hint=(btype or "file").upper())
        if info:
            attachments.append(info)
    return attachments


async def get_page_with_body(page_id: str, *, max_blocks: int = 100) -> dict[str, Any]:
    """Fetch page metadata, flatten text, and collect file/link attachments."""
    headers = _headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        page_resp = await client.get(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=headers,
        )
        page_resp.raise_for_status()
        page = page_resp.json()

        blocks_resp = await client.get(
            f"{NOTION_BASE}/blocks/{page_id}/children",
            headers=headers,
            params={"page_size": max_blocks},
        )
        blocks_resp.raise_for_status()
        blocks = blocks_resp.json().get("results", [])

    lines: list[str] = []
    for block in blocks:
        line = await _block_to_text(block)
        if line:
            lines.append(line)

    attachments = _extract_attachments(blocks)
    body = "\n".join(lines).strip() or "(No readable text blocks on this page.)"
    return {
        "id": page.get("id"),
        "title": _page_title(page),
        "url": page.get("url"),
        "last_edited_time": page.get("last_edited_time"),
        "body": body,
        "attachments": attachments,
        "attachment_count": len(attachments),
    }
