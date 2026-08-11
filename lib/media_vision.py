"""Describe Slack images/GIFs with OpenAI vision so Maestro can reply in text."""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx
import structlog
from openai import AsyncOpenAI

structlogger = structlog.get_logger()

_MAX_BYTES = 8 * 1024 * 1024
_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4.1-mini").strip()


def _openai_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


async def download_slack_media(url: str, *, needs_auth: bool) -> tuple[bytes, str] | None:
    """Download image bytes from Slack (private URLs need the bot token)."""
    headers: dict[str, str] = {}
    if needs_auth:
        token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
        if not token:
            return None
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.content
        if len(data) > _MAX_BYTES:
            structlogger.warning(
                "media_vision.download_too_large",
                size=len(data),
                limit=_MAX_BYTES,
            )
            return None
        content_type = (
            response.headers.get("content-type") or "image/gif"
        ).split(";")[0].strip()
        return data, content_type


async def describe_image_bytes(
    data: bytes,
    content_type: str,
    *,
    kind: str = "image",
) -> str | None:
    """Return a short plain-English description of an image/GIF."""
    api_key = _openai_key()
    if not api_key:
        return None

    encoded = base64.b64encode(data).decode("ascii")
    data_url = f"data:{content_type};base64,{encoded}"
    prompt = (
        "Describe this Slack GIF or image in one short sentence so an Ops "
        "assistant can react playfully. Focus on the main subject, action, "
        "and mood. Do not invent text that is not visible. Keep it under 25 "
        f"words. This is a {kind}."
    )

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=_VISION_MODEL or "gpt-4.1-mini",
            max_tokens=80,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }
            ],
        )
    except Exception as error:  # noqa: BLE001
        structlogger.error("media_vision.describe_failed", error=str(error))
        return None

    text = (response.choices[0].message.content or "").strip()
    return text or None


async def describe_slack_media(item: dict[str, Any]) -> str | None:
    """Download and describe one Slack media item."""
    url = str(item.get("url") or "").strip()
    if not url:
        return None
    try:
        downloaded = await download_slack_media(
            url,
            needs_auth=bool(item.get("needs_auth")),
        )
    except Exception as error:  # noqa: BLE001
        structlogger.error(
            "media_vision.download_failed",
            error=str(error),
            url=url[:80],
        )
        return None
    if not downloaded:
        return None
    data, content_type = downloaded
    return await describe_image_bytes(
        data,
        content_type,
        kind=str(item.get("kind") or "image"),
    )


def media_from_slack_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract image/GIF payloads from a Slack message event."""
    media: list[dict[str, Any]] = []

    for file_info in event.get("files") or []:
        if not isinstance(file_info, dict):
            continue
        mimetype = str(file_info.get("mimetype") or "").lower()
        filetype = str(file_info.get("filetype") or "").lower()
        is_image = mimetype.startswith("image/") or filetype in {
            "gif",
            "png",
            "jpg",
            "jpeg",
            "webp",
        }
        if not is_image:
            continue
        url = (
            file_info.get("url_private_download")
            or file_info.get("url_private")
            or file_info.get("thumb_video")
        )
        if not url:
            continue
        kind = "gif" if "gif" in mimetype or filetype == "gif" else "image"
        media.append(
            {
                "kind": kind,
                "url": str(url),
                "name": str(
                    file_info.get("title")
                    or file_info.get("name")
                    or kind
                ),
                "needs_auth": True,
            }
        )

    for attachment in event.get("attachments") or []:
        if not isinstance(attachment, dict):
            continue
        url = attachment.get("image_url") or attachment.get("thumb_url")
        if not url:
            continue
        url_text = str(url)
        kind = "gif" if ".gif" in url_text.lower() else "image"
        media.append(
            {
                "kind": kind,
                "url": url_text,
                "name": str(attachment.get("title") or kind),
                "needs_auth": False,
            }
        )

    for block in event.get("blocks") or []:
        if not isinstance(block, dict) or block.get("type") != "image":
            continue
        url = block.get("image_url")
        if not url:
            continue
        url_text = str(url)
        kind = "gif" if ".gif" in url_text.lower() else "image"
        media.append(
            {
                "kind": kind,
                "url": url_text,
                "name": str(block.get("alt_text") or kind),
                "needs_auth": False,
            }
        )

    return media
