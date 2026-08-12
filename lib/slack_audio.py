"""Transcribe Slack voice messages / audio files with Deepgram."""

from __future__ import annotations

import os
from typing import Any

import httpx
import structlog

from lib.media_vision import download_slack_media

structlogger = structlog.get_logger()

_MAX_BYTES = 25 * 1024 * 1024
_DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"
_DEFAULT_MODEL = "nova-2"

_AUDIO_FILETYPES = {
    "webm",
    "mp3",
    "mp4",
    "m4a",
    "wav",
    "ogg",
    "oga",
    "flac",
    "aac",
    "opus",
}


def _deepgram_key() -> str:
    return os.environ.get("DEEPGRAM_API_KEY", "").strip()


def _deepgram_model() -> str:
    return (
        os.environ.get("DEEPGRAM_MODEL", "").strip()
        or _DEFAULT_MODEL
    )


def audio_from_slack_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract Slack voice clips / audio file payloads from a message event."""
    audio: list[dict[str, Any]] = []

    for file_info in event.get("files") or []:
        if not isinstance(file_info, dict):
            continue
        mimetype = str(file_info.get("mimetype") or "").lower()
        filetype = str(file_info.get("filetype") or "").lower()
        subtype = str(file_info.get("subtype") or "").lower()
        media_display = str(file_info.get("media_display_type") or "").lower()

        is_slack_voice = subtype == "slack_audio" or media_display == "audio"
        is_audio_mime = mimetype.startswith("audio/")
        # Slack often serves native voice notes as video/webm or video/mp4.
        is_voice_video = (
            is_slack_voice
            and mimetype.startswith("video/")
        )
        is_known_audio_file = filetype in _AUDIO_FILETYPES

        if not (is_slack_voice or is_audio_mime or is_voice_video or is_known_audio_file):
            continue

        url = (
            file_info.get("url_private_download")
            or file_info.get("url_private")
            or file_info.get("aac")
        )
        if not url:
            continue

        content_type = mimetype or "audio/webm"
        if is_slack_voice and content_type.startswith("video/"):
            content_type = content_type.replace("video/", "audio/", 1)

        audio.append(
            {
                "kind": "voice_message" if is_slack_voice else "audio",
                "url": str(url),
                "name": str(
                    file_info.get("title")
                    or file_info.get("name")
                    or "voice message"
                ),
                "content_type": content_type,
                "needs_auth": True,
            }
        )

    return audio


async def transcribe_bytes(
    data: bytes,
    content_type: str,
) -> str | None:
    """Send audio bytes to Deepgram and return the transcript text."""
    api_key = _deepgram_key()
    if not api_key:
        structlogger.warning("slack_audio.missing_deepgram_key")
        return None

    if len(data) > _MAX_BYTES:
        structlogger.warning(
            "slack_audio.too_large",
            size=len(data),
            limit=_MAX_BYTES,
        )
        return None

    params = {
        "model": _deepgram_model(),
        "smart_format": "true",
        "punctuate": "true",
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": content_type or "application/octet-stream",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                _DEEPGRAM_URL,
                params=params,
                headers=headers,
                content=data,
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as error:  # noqa: BLE001
        structlogger.error("slack_audio.deepgram_failed", error=str(error))
        return None

    try:
        transcript = (
            payload["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
    except (KeyError, IndexError, TypeError):
        structlogger.error("slack_audio.unexpected_deepgram_payload")
        return None

    text = (transcript or "").strip()
    return text or None


async def transcribe_slack_audio(item: dict[str, Any]) -> str | None:
    """Download one Slack audio item and transcribe it."""
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
            "slack_audio.download_failed",
            error=str(error),
            url=url[:80],
        )
        return None
    if not downloaded:
        return None

    data, fetched_type = downloaded
    content_type = str(item.get("content_type") or fetched_type or "audio/webm")
    if content_type.startswith("video/") and item.get("kind") == "voice_message":
        content_type = content_type.replace("video/", "audio/", 1)

    return await transcribe_bytes(data, content_type)
