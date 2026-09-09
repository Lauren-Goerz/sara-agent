"""Search Spotify (preferred) or iTunes and post a song link into Slack."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
import structlog
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult
from slack_sdk.web.async_client import AsyncWebClient

structlogger = structlog.get_logger()

_ITUNES_SEARCH = "https://itunes.apple.com/search"
_SPOTIFY_TOKEN = "https://accounts.spotify.com/api/token"
_SPOTIFY_SEARCH = "https://api.spotify.com/v1/search"
_DEFAULT_TIMEZONE = ZoneInfo("Europe/Berlin")
_BLOCKED = re.compile(
    r"\b("
    r"nsfw|porn|sex|nude|naked|xxx|erotic|"
    r"kill|murder|gore|suicide|"
    r"racist|nazi|hate"
    r")\b",
    re.IGNORECASE,
)

# Simple in-process Spotify token cache.
_spotify_token: str | None = None
_spotify_token_expires_at: float = 0.0


def _default_song_query() -> str:
    """Pick Sara's deterministic song for an unspecified music request."""
    if datetime.now(_DEFAULT_TIMEZONE).weekday() == 0:
        return "Manic Monday The Bangles"
    return "Never Gonna Give You Up Rick Astley"


def _spotify_configured() -> bool:
    return bool(
        os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
        and os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    )


def _latest_slack_destination(context: ToolContext) -> tuple[str, str | None] | None:
    for event in reversed(context.events):
        if getattr(event, "input_channel", None) != "slack":
            continue
        metadata = getattr(event, "metadata", None) or {}
        channel = metadata.get("out_channel")
        if channel:
            return str(channel), metadata.get("thread_id")
    return None


async def _spotify_access_token() -> str:
    global _spotify_token, _spotify_token_expires_at
    now = time.time()
    if _spotify_token and now < _spotify_token_expires_at - 30:
        return _spotify_token

    client_id = os.environ["SPOTIFY_CLIENT_ID"].strip()
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"].strip()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _SPOTIFY_TOKEN,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        response.raise_for_status()
        payload = response.json()

    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Spotify token response missing access_token")
    expires_in = int(payload.get("expires_in") or 3600)
    _spotify_token = token
    _spotify_token_expires_at = now + expires_in
    return token


async def _search_spotify(query: str) -> dict[str, Any] | None:
    token = await _spotify_access_token()
    params = {"q": query, "type": "track", "limit": 5, "market": "US"}
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            _SPOTIFY_SEARCH,
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()

    tracks = ((payload.get("tracks") or {}).get("items")) or []
    for hit in tracks:
        external = hit.get("external_urls") or {}
        track_url = str(external.get("spotify") or "").strip()
        if not track_url.startswith("http"):
            continue
        artists = hit.get("artists") or []
        artist_name = ", ".join(
            str(artist.get("name") or "").strip()
            for artist in artists
            if str(artist.get("name") or "").strip()
        ) or "Unknown artist"
        album = hit.get("album") or {}
        return {
            "track_name": str(hit.get("name") or query).strip() or query,
            "artist_name": artist_name,
            "album_name": str(album.get("name") or "").strip() or None,
            "track_url": track_url,
            "preview_url": str(hit.get("preview_url") or "").strip() or None,
            "source": "Spotify",
            "fallback_search_url": (
                "https://open.spotify.com/search/" + quote(query)
            ),
        }
    return None


async def _search_itunes(query: str) -> dict[str, Any] | None:
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 5,
        "country": "us",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_ITUNES_SEARCH, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload.get("results") or []
    for hit in results:
        track_url = str(hit.get("trackViewUrl") or "").strip()
        if not track_url.startswith("http"):
            continue
        return {
            "track_name": str(hit.get("trackName") or query).strip() or query,
            "artist_name": str(hit.get("artistName") or "Unknown artist").strip(),
            "album_name": str(hit.get("collectionName") or "").strip() or None,
            "track_url": track_url,
            "preview_url": str(hit.get("previewUrl") or "").strip() or None,
            "source": "iTunes Search / Apple Music",
            "fallback_search_url": (
                "https://music.apple.com/us/search?term=" + quote(query)
            ),
        }
    return None


async def _search_track(query: str) -> dict[str, Any] | None:
    """Prefer Spotify when credentials exist; otherwise Apple Music / iTunes."""
    if _spotify_configured():
        try:
            hit = await _search_spotify(query)
            if hit:
                return hit
            structlogger.info("fun_play_music.spotify_no_results", query=query)
        except Exception as error:  # noqa: BLE001
            structlogger.warning(
                "fun_play_music.spotify_failed_falling_back",
                error=str(error),
                query=query,
            )
    return await _search_itunes(query)


@tool(
    description=(
        "Search for a song and post the link into the current Slack thread. "
        "Uses Spotify when configured, otherwise Apple Music / iTunes. Pass a "
        "short query only when the user specified a song, artist, genre, or "
        "vibe. For a generic request such as 'play music' or 'play a song', "
        "leave query empty so Sara selects the weekday default."
    )
)
async def send_slack_song(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Find a song and share it in Slack.

    Args:
        query: Song title, artist, genre, or vibe (e.g. 'Dancing Queen ABBA',
            'jazz piano', 'upbeat pop'). Leave empty for a generic music request.
    """
    search = str(query or "").strip()
    if not search:
        search = _default_song_query()

    if _BLOCKED.search(search):
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "blocked_query",
                "instruction": (
                    "Refuse briefly - that search is not workplace-safe. Offer "
                    "a tame alternative."
                ),
            }
        )

    try:
        hit = await _search_track(search)
    except Exception as error:  # noqa: BLE001
        structlogger.error("fun_play_music.search_failed", error=str(error), query=search)
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "search_failed",
                "message": str(error),
                "instruction": "Say music search failed; ask them to try again.",
            }
        )

    if not hit:
        fallback = (
            "https://open.spotify.com/search/" + quote(search)
            if _spotify_configured()
            else "https://music.apple.com/us/search?term=" + quote(search)
        )
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_results",
                "query": search,
                "fallback_search_url": fallback,
                "instruction": (
                    "Say no track matched; share fallback_search_url or ask for "
                    "a clearer title/artist."
                ),
            }
        )

    destination = _latest_slack_destination(context) if context else None
    posted = False
    post_error: str | None = None
    label = f"{hit['track_name']} — {hit['artist_name']}"
    slack_link = f"<{hit['track_url']}|{label}>"

    if destination and os.environ.get("SLACK_BOT_TOKEN", "").strip():
        channel, thread_ts = destination
        client = AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"].strip())
        text = f":notes: {slack_link}"
        kwargs: dict[str, Any] = {
            "channel": channel,
            "text": text,
            "unfurl_links": True,
            "unfurl_media": True,
        }
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        try:
            await client.chat_postMessage(**kwargs)
            posted = True
        except Exception as error:  # noqa: BLE001
            post_error = str(error)
            structlogger.error(
                "fun_play_music.slack_post_failed",
                channel=channel,
                thread_ts=thread_ts,
                error=post_error,
            )
    else:
        post_error = "No Slack destination for this conversation."

    source = str(hit.get("source") or "music search")
    return ToolResult(
        llm_response={
            "ok": posted,
            "posted_to_slack": posted,
            "query": search,
            "track_name": hit["track_name"],
            "artist_name": hit["artist_name"],
            "album_name": hit.get("album_name"),
            "track_url": hit["track_url"],
            "preview_url": hit.get("preview_url"),
            "post_error": post_error,
            "source": source,
            "spotify_configured": _spotify_configured(),
            "instruction": (
                f"The song link ({source}) is already in the Slack thread "
                "(Slack may unfurl a player). Confirm in one short playful "
                "line naming track and artist. Do not dump the raw URL."
                if posted
                else (
                    "Slack posting failed. Share track_url so they can open "
                    "it, and apologize briefly."
                )
            ),
        }
    )
