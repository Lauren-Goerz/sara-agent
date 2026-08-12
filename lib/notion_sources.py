"""Shared access layer for Sara's allowlisted Notion sources.

Skills declare which registered source they read; this module owns fetching,
cleaning, caching, and trimming the payload that reaches the LLM. Only the
sections relevant to the user's question are returned, so a large policy page
does not become a large prompt.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from lib import notion_client

# Cleaned page bodies change rarely; re-reading Notion on every turn is slow
# and pointless.
_CACHE_TTL_SECONDS = 300.0
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

_DEFAULT_CHAR_LIMIT = 6000
_PREAMBLE_CHAR_LIMIT = 900

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "are", "can", "you", "our", "with", "what", "how",
        "does", "did", "was", "were", "have", "has", "any", "about", "from",
        "that", "this", "there", "when", "where", "who", "why", "rasa", "please",
        "tell", "give", "need", "want", "into", "out", "get", "got", "would",
        "should", "could", "policy", "page", "info", "information",
    }
)


@dataclass(frozen=True)
class NotionSource:
    """One allowlisted Notion page or database."""

    key: str
    notion_id: str
    url: str
    title: str
    # page, database, or auto (try database rows first, then page body).
    kind: str = "page"
    max_blocks: int = 400
    max_rows: int = 200
    # Extra words that should always count as a match for this source.
    keywords: tuple[str, ...] = field(default_factory=tuple)


SOURCES: dict[str, NotionSource] = {
    "benefits": NotionSource(
        key="benefits",
        notion_id="bd1165c5ece74392917d3b3eaffb4388",
        url=(
            "https://app.notion.com/p/rasa/"
            "Benefits-Perks-2026-bd1165c5ece74392917d3b3eaffb4388"
        ),
        title="Benefits & Perks 2026",
        max_blocks=600,
    ),
    "work_abroad": NotionSource(
        key="work_abroad",
        notion_id="cd21b2caa0214c85aa2410bb0814e446",
        url=(
            "https://app.notion.com/p/rasa/"
            "Working-from-other-Countries-cd21b2caa0214c85aa2410bb0814e446"
        ),
        title="Working from other Countries",
        max_blocks=600,
    ),
    "social_media": NotionSource(
        key="social_media",
        notion_id="39d0d3053dc44c9e89c2baba3230eb4c",
        url=(
            "https://app.notion.com/p/rasa/"
            "Social-Media-Policy-39d0d3053dc44c9e89c2baba3230eb4c"
        ),
        title="Social Media Policy",
    ),
    "company_values": NotionSource(
        key="company_values",
        notion_id="f3afec52e31742f292f9a776d4ef712d",
        url=(
            "https://app.notion.com/p/rasa/"
            "Rasa-s-Company-Values-f3afec52e31742f292f9a776d4ef712d"
        ),
        title="Rasa's Company Values",
        max_blocks=200,
    ),
    "company_info": NotionSource(
        key="company_info",
        notion_id="44a36a2d9f8745adbc7827769f530906",
        url=(
            "https://app.notion.com/p/rasa/"
            "Rasa-Offices-banking-important-info-44a36a2d9f8745adbc7827769f530906"
        ),
        title="Rasa Offices, banking & important info",
        max_blocks=500,
    ),
    "board": NotionSource(
        key="board",
        notion_id="984687d72adb4c0fb459c3e9bb280565",
        url="https://app.notion.com/p/rasa/Board-984687d72adb4c0fb459c3e9bb280565",
        title="Board",
        kind="auto",
        max_blocks=300,
        max_rows=100,
    ),
    "security_incidents": NotionSource(
        key="security_incidents",
        notion_id="202b9c0d544a8143be59e3e3568b1b4d",
        url=(
            "https://app.notion.com/p/rasa/"
            "202b9c0d544a8143be59e3e3568b1b4d"
            "?v=202b9c0d544a816bb595000c37f7dab3"
        ),
        title="Security incidents tracker",
        kind="auto",
        max_blocks=500,
    ),
    "rfp_security": NotionSource(
        key="rfp_security",
        notion_id="2d41a51d8c6d4080b42dc06ce5248cc6",
        url=(
            "https://app.notion.com/p/rasa/"
            "Customer-Information-Security-Questionnaires-"
            "2d41a51d8c6d4080b42dc06ce5248cc6"
        ),
        title="Customer Information Security Questionnaires",
        kind="auto",
        max_blocks=600,
        max_rows=300,
    ),
    "yubikey": NotionSource(
        key="yubikey",
        notion_id="5a3e653ef9f54accb8646444263f5f42",
        url=(
            "https://app.notion.com/p/rasa/"
            "All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42"
        ),
        title="All about Yubikeys / google phones",
    ),
    "yubisneeze": NotionSource(
        key="yubisneeze",
        notion_id="5a3e653ef9f54accb8646444263f5f42",
        url=(
            "https://app.notion.com/p/rasa/"
            "All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42"
            "#e9faa6c469a34069a3f1219bb4bea0f2"
        ),
        title="Undo the Yubisneeze",
        max_blocks=500,
        keywords=("yubisneeze", "sneeze", "undo", "otp"),
    ),
    "laptop_repairs": NotionSource(
        key="laptop_repairs",
        notion_id="ccda2595781346bfb3de7c64d5715ac6",
        url=(
            "https://app.notion.com/p/rasa/"
            "Laptop-issues-repairs-ccda2595781346bfb3de7c64d5715ac6"
        ),
        title="Laptop issues & repairs",
        max_blocks=200,
    ),
    "travel_insurance": NotionSource(
        key="travel_insurance",
        notion_id="fea448cc42fb4348b4a74f12736c1c50",
        url=(
            "https://app.notion.com/p/rasa/"
            "Travel-Insurances-2026-fea448cc42fb4348b4a74f12736c1c50"
        ),
        title="Travel Insurances 2026",
        max_blocks=600,
        keywords=("travel", "insurance", "insurances", "trip", "cover"),
    ),
    "business_travel": NotionSource(
        key="business_travel",
        notion_id="f5c1d8842db048539e065865d0e066cf",
        url=(
            "https://app.notion.com/p/rasa/"
            "Business-Travel-f5c1d8842db048539e065865d0e066cf"
        ),
        title="Business Travel",
        max_blocks=600,
        keywords=(
            "flight",
            "economy",
            "hotel",
            "perdiem",
            "per-diem",
            "receipt",
            "transport",
            "train",
            "expense",
        ),
    ),
    "remote_budget": NotionSource(
        key="remote_budget",
        notion_id="fb07ed3e076f4096a15a1d4fc95091ed",
        url=(
            "https://app.notion.com/p/rasa/"
            "Remote-Budget-2026-fb07ed3e076f4096a15a1d4fc95091ed"
        ),
        title="Remote Budget - 2026",
        max_blocks=600,
        keywords=(
            "remote",
            "budget",
            "home",
            "office",
            "coworking",
            "co-working",
            "internet",
            "utility",
            "payhawk",
        ),
    ),
}


def clean_body(body: str) -> str:
    """Drop file/link lines whose signed URLs crowd out readable text."""
    lines = [
        line
        for line in body.splitlines()
        if not line.startswith("[file]") and not line.startswith("[link]")
    ]
    cleaned = "\n".join(lines).strip()
    if cleaned.endswith("\nUntitled"):
        cleaned = cleaned[: -len("\nUntitled")].rstrip()
    elif cleaned == "Untitled":
        cleaned = ""
    return cleaned


def rows_to_text(rows: list[dict[str, Any]]) -> str:
    """Flatten database rows into the same heading/bullet shape as page text."""
    chunks: list[str] = []
    for row in rows:
        title = row.get("title") or "Untitled"
        fields = row.get("fields") or {}
        lines = [f"## {title}"]
        for key, value in fields.items():
            text = str(value or "").strip()
            if text and text != title:
                lines.append(f"- {key}: {text}")
        url = row.get("url")
        if url:
            lines.append(f"- notion_url: {url}")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks).strip()


def _split_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (preamble, [(heading, section_text), ...])."""
    preamble_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []

    for line in body.splitlines():
        if re.match(r"^#{1,3}\s+\S", line):
            sections.append((line.lstrip("# ").strip(), [line]))
        elif sections:
            sections[-1][1].append(line)
        else:
            preamble_lines.append(line)

    return (
        "\n".join(preamble_lines).strip(),
        [(heading, "\n".join(lines).strip()) for heading, lines in sections],
    )


def _query_terms(query: str, extra: tuple[str, ...]) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", (query or "").lower())
    terms = [word for word in words if word not in _STOPWORDS]
    return list(dict.fromkeys(terms + list(extra)))


def _score(text: str, heading: str, terms: list[str]) -> int:
    if not terms:
        return 0
    body_lower = text.lower()
    heading_lower = heading.lower()
    score = 0
    for term in terms:
        score += body_lower.count(term)
        if term in heading_lower:
            score += 5
    return score


def select_relevant(
    body: str,
    *,
    query: str = "",
    char_limit: int = _DEFAULT_CHAR_LIMIT,
    extra_keywords: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Trim a source body down to the parts that answer the question."""
    body = body.strip()
    if len(body) <= char_limit:
        return {
            "content": body,
            "truncated": False,
            "matched_headings": [],
            "other_headings": [],
        }

    preamble, sections = _split_sections(body)
    terms = _query_terms(query, extra_keywords)

    if not sections:
        return {
            "content": body[:char_limit].rstrip(),
            "truncated": True,
            "matched_headings": [],
            "other_headings": [],
        }

    scored = [
        (_score(text, heading, terms), index, heading, text)
        for index, (heading, text) in enumerate(sections)
    ]
    matching = sorted(
        (item for item in scored if item[0] > 0),
        key=lambda item: (-item[0], item[1]),
    )
    # With no query match, fall back to document order so the answer still
    # starts from the top of the page rather than an arbitrary section.
    chosen = matching or sorted(scored, key=lambda item: item[1])

    head = preamble[:_PREAMBLE_CHAR_LIMIT].rstrip() if preamble else ""
    used = len(head)

    # Pick by relevance, but emit in document order so the page still reads
    # top to bottom.
    picked: list[tuple[int, str, str]] = []
    for _, index, heading, text in chosen:
        if used + len(text) > char_limit:
            continue
        picked.append((index, heading, text))
        used += len(text)

    if not picked:
        # Single oversized section: keep a prefix rather than returning nothing.
        _, index, heading, text = chosen[0]
        picked.append(
            (index, heading, text[: max(char_limit - used, 500)].rstrip())
        )

    picked.sort(key=lambda item: item[0])
    matched_headings = [heading for _, heading, _ in picked]
    parts = [head, *(text for _, _, text in picked)]

    other = [
        heading for _, _, heading, _ in scored if heading not in matched_headings
    ]
    return {
        "content": "\n\n".join(part for part in parts if part).strip(),
        "truncated": True,
        "matched_headings": matched_headings,
        "other_headings": other[:25],
    }


async def _load_raw(source: NotionSource) -> dict[str, Any]:
    """Fetch and clean a source, using the short-lived cache when warm."""
    cached = _cache.get(source.key)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    raw: dict[str, Any] | None = None
    db_error: Exception | None = None

    if source.kind in {"database", "auto"}:
        try:
            rows = await notion_client.query_database(
                source.notion_id,
                max_rows=source.max_rows,
            )
            text = rows_to_text(rows)
            if text:
                raw = {
                    "ok": True,
                    "source_kind": "database",
                    "title": source.title,
                    "last_edited_time": None,
                    "row_count": len(rows),
                    "body": text,
                }
        except notion_client.NotionConfigError:
            raise
        except Exception as error:  # noqa: BLE001
            db_error = error

    if raw is None and source.kind in {"page", "auto"}:
        page = await notion_client.get_page_with_body(
            source.notion_id,
            max_blocks=source.max_blocks,
        )
        raw = {
            "ok": True,
            "source_kind": "page",
            "title": page.get("title") or source.title,
            "last_edited_time": page.get("last_edited_time"),
            "row_count": None,
            "body": clean_body(page.get("body") or ""),
        }

    if raw is None:
        raise db_error or RuntimeError(f"Could not load Notion source {source.key}")

    _cache[source.key] = (time.monotonic(), raw)
    return raw


async def load(
    key: str,
    *,
    query: str = "",
    char_limit: int = _DEFAULT_CHAR_LIMIT,
    fallback_content: str | None = None,
) -> dict[str, Any]:
    """Return a normalized payload for a registered source.

    On success: ok=True with source_content trimmed to the relevant sections.
    On failure: ok=False with an error code and the source_url to share, unless
    fallback_content is supplied.
    """
    source = SOURCES[key]
    base = {"query": query, "source_url": source.url, "page_title": source.title}

    def _failed(error: str, message: str, **extra: Any) -> dict[str, Any]:
        if fallback_content:
            selected = select_relevant(
                fallback_content,
                query=query,
                char_limit=char_limit,
                extra_keywords=source.keywords,
            )
            return {
                **base,
                "ok": True,
                "used_fallback": True,
                "source_kind": "fallback",
                "last_edited_time": None,
                "source_content": selected["content"],
                "content_truncated": selected["truncated"],
                "other_sections": selected["other_headings"],
            }
        return {**base, "ok": False, "error": error, "message": message, **extra}

    try:
        raw = await _load_raw(source)
    except notion_client.NotionConfigError as exc:
        return _failed("not_configured", str(exc))
    except httpx.HTTPStatusError as exc:
        return _failed(
            "notion_page_unavailable",
            (
                f"'{source.title}' is not visible to Sara's Notion integration. "
                "Share it with the Sara-Agent integration and retry."
            ),
            status_code=exc.response.status_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _failed("notion_error", str(exc))

    body = raw.get("body") or ""
    if not body:
        return _failed("empty_source", "The Notion source had no readable text.")

    selected = select_relevant(
        body,
        query=query,
        char_limit=char_limit,
        extra_keywords=source.keywords,
    )
    return {
        **base,
        "ok": True,
        "used_fallback": False,
        "source_kind": raw.get("source_kind"),
        "page_title": raw.get("title") or source.title,
        "last_edited_time": raw.get("last_edited_time"),
        "row_count": raw.get("row_count"),
        "source_content": selected["content"],
        "content_truncated": selected["truncated"],
        "other_sections": selected["other_headings"],
    }
