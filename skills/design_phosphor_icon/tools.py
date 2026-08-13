"""Search official Phosphor assets and upload a colored PNG or SVG to Slack."""

from __future__ import annotations

import difflib
import os
import re
from typing import Any

import httpx
import resvg_py
import structlog
from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult
from slack_sdk.web.async_client import AsyncWebClient

structlogger = structlog.get_logger()

CATALOG_URL = "https://raw.githubusercontent.com/phosphor-icons/core/main/src/icons.ts"
ASSET_URL = (
    "https://raw.githubusercontent.com/phosphor-icons/core/main/"
    "assets/{weight}/{name}{suffix}.svg"
)
PHOSPHOR_SEARCH_URL = "https://phosphoricons.com/?q={name}"
WEIGHT = "regular"

_catalog_cache: list[dict[str, Any]] | None = None

_COLOR_NAMES = {
    # Rasa palette. Bare "purple" deliberately means Rasa Purple.
    "purple": "#5A17EE",
    "rasa purple": "#5A17EE",
    "brand purple": "#5A17EE",
    "navy": "#080327",
    "dark": "#080327",
    "rasa navy": "#080327",
    "white": "#FFFFFF",
    "rasa grey": "#DFE8FF",
    "rasa gray": "#DFE8FF",
    "rasa light grey": "#EFF1FF",
    "rasa light gray": "#EFF1FF",
    "light purple": "#7E7AF4",
    "orange": "#FFD594",
    "aqua": "#71EFF3",
    "lilac": "#A6AAF3",
    "light lilac": "#DADCFB",
    # Useful basic choices outside the brand palette.
    "black": "#000000",
    "red": "#FF0000",
    "green": "#008000",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "pink": "#FFC0CB",
    "grey": "#808080",
    "gray": "#808080",
}

_STOP_WORDS = {
    "a",
    "an",
    "for",
    "icon",
    "icons",
    "of",
    "phosphor",
    "symbol",
    "the",
}

_PREFERRED_CONCEPTS = {
    "account": "user-circle",
    "add": "plus",
    "close": "x",
    "complete": "check-circle",
    "delete": "trash",
    "edit": "pencil-simple",
    "error": "warning-circle",
    "home": "house",
    "location": "map-pin",
    "location pin": "map-pin",
    "map": "map-pin",
    "map pin": "map-pin",
    "menu": "list",
    "notification": "bell",
    "notifications": "bell",
    "pin": "map-pin",
    "profile": "user-circle",
    "remove": "trash",
    "search": "magnifying-glass",
    "send": "paper-plane-tilt",
    "settings": "gear",
    "success": "check-circle",
    "warning": "warning",
    # Abstract concepts have no literal icon name; map them to the closest
    # official icon so fuzzy matching cannot pick something unrelated.
    "confusion": "question-mark",
    "confused": "question-mark",
    "uncertainty": "question-mark",
    "unsure": "question-mark",
    "puzzled": "question-mark",
    "idea": "lightbulb",
    "inspiration": "lightbulb",
    "brainstorm": "brain",
    "thinking": "brain",
    "learning": "graduation-cap",
    "education": "graduation-cap",
    "celebration": "confetti",
    "party": "confetti",
    "help": "lifebuoy",
    "support": "lifebuoy",
    "question": "question",
    "collaboration": "handshake",
    "partnership": "handshake",
    "teamwork": "users-three",
    "team": "users-three",
    "growth": "chart-line",
    "launch": "rocket",
    "speed": "rocket",
    "goal": "target",
    "goals": "target",
    "win": "trophy",
    "achievement": "trophy",
    "security": "shield-check",
    "privacy": "lock",
    "time": "clock",
    "deadline": "clock",
    "bug": "bug",
    "fix": "wrench",
    "magic": "sparkle",
    "favorite": "star",
    "love": "heart",
    "approval": "thumbs-up",
    "urgent": "fire",
    "documentation": "books",
    "sad": "smiley-sad",
    "sadness": "smiley-sad",
    "happy": "smiley",
    "happiness": "smiley",
    "angry": "smiley-angry",
    "frustration": "smiley-angry",
    "overwhelmed": "smiley-melting",
    "burnout": "smiley-melting",
    "welcome": "hand-waving",
    "greeting": "hand-waving",
    "onboarding": "hand-waving",
    "budget": "money",
    "cost": "currency-dollar",
    "payroll": "money",
    "email": "envelope",
    "feedback": "chat-circle",
    "milestone": "flag",
    "global": "globe",
    "remote": "globe",
    "data": "database",
    "cloud": "cloud-arrow-up",
    "ai": "robot",
    "automation": "robot",
    "voice": "microphone",
    "meeting": "calendar-check",
    "roadmap": "path",
    "workflow": "tree-structure",
    "strategy": "strategy",
    "integration": "puzzle-piece",
    "visibility": "eye",
    "risk": "shield-warning",
    "compliance": "scales",
    "legal": "gavel",
}

# Fuzzy similarity below this is noise (e.g. "confusion" vs "construction"
# scores ~0.67), so it must not decide a match on its own.
_MIN_FUZZY_RATIO = 0.8

# Anything under this means no token, substring, or strong fuzzy hit.
_MIN_CONFIDENT_SCORE = 80.0


def _parse_catalog(source: str) -> list[dict[str, Any]]:
    """Extract searchable fields from Phosphor's TypeScript catalog."""
    entries: list[dict[str, Any]] = []
    object_pattern = re.compile(
        r'\n  \{\n    name: "(?P<name>[^"]+)",'
        r"(?P<body>.*?)(?=\n  \{\n    name: |\n\]\s+as const)",
        re.DOTALL,
    )
    for match in object_pattern.finditer(source):
        body = match.group("body")
        pascal_match = re.search(r'pascal_name: "([^"]+)"', body)
        tags_match = re.search(r"tags:\s*\[(.*?)\],\n", body, re.DOTALL)
        tags = (
            re.findall(r'"([^"]+)"', tags_match.group(1))
            if tags_match
            else []
        )
        entries.append(
            {
                "name": match.group("name"),
                "pascal_name": (
                    pascal_match.group(1)
                    if pascal_match
                    else match.group("name").replace("-", " ").title().replace(" ", "")
                ),
                "tags": [tag for tag in tags if not tag.startswith("*")],
            }
        )
    return entries


async def _catalog() -> list[dict[str, Any]]:
    global _catalog_cache
    if _catalog_cache is None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(CATALOG_URL)
            response.raise_for_status()
        _catalog_cache = _parse_catalog(response.text)
        if not _catalog_cache:
            raise RuntimeError("The official Phosphor catalog could not be parsed.")
    return _catalog_cache


def _clean_query(query: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    meaningful = [token for token in tokens if token not in _STOP_WORDS]
    return " ".join(meaningful) or query.strip().lower()


def _score(entry: dict[str, Any], query: str) -> float:
    name = entry["name"].replace("-", " ")
    pascal = re.sub(r"(?<!^)(?=[A-Z])", " ", entry["pascal_name"]).lower()
    tags = [str(tag).lower() for tag in entry["tags"]]

    if name == query or pascal == query:
        return 1000.0
    if query in tags:
        return 900.0

    score = 0.0
    if query in name or query in pascal:
        score += 300.0
    if any(query in tag for tag in tags):
        score += 250.0

    query_tokens = set(query.split())
    searchable_tokens = set(name.split()) | set(pascal.split())
    for tag in tags:
        searchable_tokens.update(tag.split())
    score += 80.0 * len(query_tokens & searchable_tokens)

    candidates = [name, pascal, *tags]
    best_ratio = max(
        difflib.SequenceMatcher(None, query, candidate).ratio()
        for candidate in candidates
    )
    # Only credit fuzzy similarity when it is close enough to be a real
    # typo/variant. Weak similarity used to tie hundreds of icons together
    # and hand the win to whichever appeared first in the catalog.
    if best_ratio >= _MIN_FUZZY_RATIO:
        score += 100.0 * best_ratio
    return score


async def _search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    cleaned = _clean_query(query)
    entries = await _catalog()
    # Break score ties toward the plainest icon ("check" over "calendar-check")
    # instead of whatever happens to come first in the catalog.
    ranked = sorted(
        entries,
        key=lambda entry: (-_score(entry, cleaned), len(entry["name"]), entry["name"]),
    )
    preferred_name = _PREFERRED_CONCEPTS.get(cleaned)
    if preferred_name:
        preferred = next(
            (entry for entry in entries if entry["name"] == preferred_name),
            None,
        )
        if preferred:
            ranked = [preferred, *[entry for entry in ranked if entry is not preferred]]
    return ranked[:limit]


def _is_confident(entry: dict[str, Any], query: str) -> bool:
    cleaned = _clean_query(query)
    if _PREFERRED_CONCEPTS.get(cleaned) == entry["name"]:
        return True
    return _score(entry, cleaned) >= _MIN_CONFIDENT_SCORE


def _normalize_color(raw_color: str) -> tuple[str, str]:
    value = raw_color.strip()
    named = _COLOR_NAMES.get(value.lower())
    if named:
        label = "Rasa Purple" if value.lower() in {
            "purple",
            "rasa purple",
            "brand purple",
        } else value
        return named, label

    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.upper(), value.upper()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        expanded = "#" + "".join(character * 2 for character in value[1:])
        return expanded.upper(), expanded.upper()

    available = ", ".join(sorted(_COLOR_NAMES))
    raise ValueError(
        f"I don't recognize {raw_color!r} as a safe color name or hex value. "
        f"Try a hex value or one of: {available}."
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


def _requested_format(context: ToolContext) -> str:
    """Use SVG only when the user explicitly requested it; otherwise use PNG."""
    for event in reversed(context.events):
        text = str(getattr(event, "text", None) or "").lower()
        if re.search(r"\bsvg\b", text):
            return "svg"
        if re.search(r"\bpng\b", text):
            return "png"
    return "png"


async def _fetch_svg(name: str, color: str) -> tuple[str, str]:
    suffix = "" if WEIGHT == "regular" else f"-{WEIGHT}"
    url = ASSET_URL.format(
        weight=WEIGHT,
        name=name,
        suffix=suffix,
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
    return response.text.replace("currentColor", color), url


def _render_file(svg: str, file_format: str) -> str | bytes:
    if file_format == "svg":
        return svg
    return resvg_py.svg_to_bytes(
        svg_string=svg,
        width=512,
        height=512,
    )


_FAILURE_INSTRUCTION = (
    "This tool is the only way to deliver an icon. Say plainly what went wrong "
    "in one line and, when a color was not recognized, name a color or hex you "
    "can accept. Never invent a Slack slash command, app, website, or any other "
    "route for the user to fetch the icon themselves - no such command exists."
)


@tool(
    description=(
        "Find the best official Phosphor icon for a concept, color it, and "
        "upload a PNG by default or SVG when explicitly requested. Pass "
        "icon_query and icon_color on every call, including follow-ups where "
        "the user asks for a different icon or color - do not rely on earlier "
        "values."
    )
)
async def generate_phosphor_icon(
    icon_query: str = "",
    icon_color: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Generate and deliver the requested Phosphor icon.

    Args:
        icon_query: The concept the icon should represent for THIS request
            (e.g. "location pin", "navigation arrow"). Always pass the user's
            most recent request, not a previous one.
        icon_color: The color name or hex for this icon (e.g. "rasa purple",
            "#5A17EE").
    """
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    # Prefer the values the LLM passed this turn; fall back to memory only when
    # an argument is omitted. This lets follow-up requests change the icon.
    query = str(icon_query or context.memory.get("icon_query") or "").strip()
    raw_color = str(icon_color or context.memory.get("icon_color") or "").strip()
    if not query or not raw_color:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "missing_icon_query_or_color",
                "hint": "Collect both the icon concept and color first.",
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    # Keep memory in sync with the latest request.
    context.memory.set("icon_query", query)
    context.memory.set("icon_color", raw_color)

    try:
        color, color_label = _normalize_color(raw_color)
        matches = await _search(query)
        chosen = matches[0]
        if not _is_confident(chosen, query):
            return ToolResult(
                llm_response={
                    "ok": False,
                    "error": "no_confident_match",
                    "query": query,
                    "instruction": (
                        f"Phosphor has no icon that clearly means {query!r}, so "
                        "nothing was uploaded. Do NOT guess or upload a "
                        "loosely-related icon. Suggest two or three concrete "
                        "Phosphor icons that could represent the idea and ask "
                        "the user to pick one, or ask them for a more literal "
                        "object (e.g. 'question mark' instead of 'confusion')."
                    ),
                }
            )
        svg, source_url = await _fetch_svg(chosen["name"], color)
        file_format = _requested_format(context)
        rendered_file = _render_file(svg, file_format)
    except (httpx.HTTPError, RuntimeError, ValueError, OSError) as error:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "icon_generation_failed",
                "message": str(error),
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    destination = _latest_slack_destination(context)
    filename = (
        f"{chosen['name']}-{WEIGHT}-{color.lstrip('#').lower()}.{file_format}"
    )
    upload_error: str | None = None

    if destination and os.environ.get("SLACK_BOT_TOKEN", "").strip():
        channel, thread_ts = destination
        client = AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"].strip())
        try:
            await client.files_upload_v2(
                channel=channel,
                thread_ts=thread_ts,
                content=rendered_file,
                filename=filename,
                title=f"{chosen['pascal_name']} — {color_label}",
                alt_txt=f"{chosen['pascal_name']} Phosphor icon in {color_label}",
                initial_comment=(
                    f"*{chosen['pascal_name']}* in {color_label} ({color}) — "
                    f"<{PHOSPHOR_SEARCH_URL.format(name=chosen['name'])}|"
                    "view in Phosphor>"
                ),
            )
        except Exception as error:  # Slack SDK raises several API/transport types.
            upload_error = str(error)
            structlogger.error(
                "phosphor_icon.slack_upload_failed",
                channel=channel,
                thread_ts=thread_ts,
                filename=filename,
                error=upload_error,
            )
    else:
        upload_error = "This conversation is not connected to Slack file uploads."
        structlogger.error(
            "phosphor_icon.no_slack_destination",
            has_destination=destination is not None,
            has_token=bool(os.environ.get("SLACK_BOT_TOKEN", "").strip()),
        )

    missing_scope = upload_error is not None and (
        "missing_scope" in upload_error or "not_allowed_token_type" in upload_error
    )

    alternatives = [
        {
            "name": match["pascal_name"],
            "slug": match["name"],
        }
        for match in matches[1:4]
    ]
    return ToolResult(
        llm_response={
            "ok": upload_error is None,
            "icon": chosen["pascal_name"],
            "slug": chosen["name"],
            "color": color,
            "color_label": color_label,
            "weight": WEIGHT,
            "format": file_format,
            "filename": filename,
            "uploaded_to_slack": upload_error is None,
            "upload_error": upload_error,
            "missing_files_write_scope": missing_scope,
            "source_svg": source_url,
            "phosphor_page": PHOSPHOR_SEARCH_URL.format(name=chosen["name"]),
            "alternatives": alternatives,
            "instruction": (
                "The icon itself was found and rendered successfully — never say "
                "icon generation failed. If uploaded_to_slack is true, confirm it "
                "in one line. Otherwise say the file could not be attached, and "
                "when missing_files_write_scope is true state plainly that the "
                "Slack app is missing the files:write scope and an admin needs to "
                "add it and reinstall the app. Always share the icon name, hex, "
                "and phosphor_page so the person is unblocked. Do not retry this "
                "tool and do not ask the user to re-pick the color."
            ),
        }
    )
