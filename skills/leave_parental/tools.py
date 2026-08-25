"""Parental leave guidance from the approved Notion guide, gated on location."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import httpx
from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_client, user_location  # noqa: E402

POLICY_PAGE_ID = "153b9c0d544a806a9753f70723a1d47a"
POLICY_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Parental-Leave-Guide-153b9c0d544a806a9753f70723a1d47a"
)
POLICY_SLACK_LINK = (
    "<https://app.notion.com/p/rasa/"
    "Parental-Leave-Guide-153b9c0d544a806a9753f70723a1d47a|Parental Leave Guide>"
)
BAMBOO_SLACK_LINK = "<https://rasa.bamboohr.com/home/|rasa.bamboohr.com>"

_SUPPORTED = ("uk", "us", "germany", "serbia", "france")

_GEO_LABELS = {
    "uk": "the UK",
    "us": "the US",
    "germany": "Germany",
    "serbia": "Serbia",
    "france": "France",
    "other": "another country",
}

_SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "eligibility": ("who has the eligibility to go on parental leave",),
    "duration": ("how long can i go on paid parental leave",),
    "notify": (
        "i plan to go on parental leave",
        "who do i inform and when",
    ),
    "uk": (
        "4.1. information for employees based in the uk",
        "information for employees based in the uk",
    ),
    "us": (
        "4.2. information for employees based in the us",
        "information for employees based in the us",
    ),
    "germany": (
        "4.3. information for employees based in germany",
        "information for employees based in germany",
    ),
    "serbia": (
        "4.4. information for employees based in serbia",
        "information for employees based in serbia",
    ),
    "france": (
        "4.5. information for employees based in france",
        "information for employees based in france",
    ),
    "return": ("return to work",),
    "faq": ("faq",),
}

_BOUNDARY_MARKERS = tuple(
    marker for markers in _SECTION_MARKERS.values() for marker in markers
) + ("what are the regulations for rasa",)


def _normalize_country(value: str | None) -> str | None:
    raw = (value or "").strip().lower()
    if not raw:
        return None
    if raw in _SUPPORTED or raw == "other":
        return raw
    mapped = user_location.from_text(raw)
    return mapped or "other"


def _clean_line(line: str) -> str:
    return re.sub(r"^[\s#>*\-\d.)\[\]xX]+", "", line).strip().lower()


def _is_marker(line: str, markers: tuple[str, ...]) -> bool:
    cleaned = _clean_line(line)
    return any(marker in cleaned for marker in markers)


def _extract_section(body: str, section: str) -> str | None:
    markers = _SECTION_MARKERS[section]
    lines = body.splitlines()
    start: int | None = None

    for index, line in enumerate(lines):
        if _is_marker(line, markers):
            start = index + 1
            break

    if start is None:
        return None

    selected: list[str] = []
    for line in lines[start:]:
        cleaned = _clean_line(line)
        if any(marker in cleaned for marker in _BOUNDARY_MARKERS):
            break
        if line.startswith("[file]") or line.startswith("[link]"):
            continue
        selected.append(line)

    text = "\n".join(selected).strip()
    return text or None


@tool(
    description=(
        "Read the Slack user's location/timezone guess for parental leave. "
        "Call this first so you can ask them to confirm before giving any "
        "parental leave advice."
    )
)
async def detect_parental_leave_location(
    context: ToolContext = None,
) -> ToolResult:
    """Return the Slack-derived employment location for confirmation."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    # Reuse the country already established this conversation, but never skip
    # the confirmation step below - parental leave is too consequential.
    location = await user_location.resolve(context, remember=False)
    geography = location["country"]
    timezone = location["timezone"]
    profile_location = location["profile_location"]
    location_source = location["location_source"]
    display_label = (
        location["country_label"]
        or (str(profile_location) if profile_location else "")
        or (str(timezone) if timezone else "")
    )

    return ToolResult(
        llm_response={
            "ok": True,
            "detected_country": geography,
            "detected_label": display_label or None,
            "profile_location": profile_location,
            "timezone": timezone,
            "location_source": location_source,
            "supported_countries": list(_SUPPORTED),
            "source_slack_link": POLICY_SLACK_LINK,
            "instruction": (
                "Do NOT give parental leave advice yet. Ask the user to "
                "confirm whether detected_label (or profile_location/"
                "timezone) is their employment country for parental leave. "
                "If nothing was detected, ask which country they work in. "
                "Supported country sections are UK, US, Germany, Serbia, and "
                "France. After they confirm or correct, set user_country and "
                "user_country_confirmed=true, then call "
                "get_parental_leave_guidance."
            ),
        }
    )


@tool(
    description=(
        "Fetch parental leave guidance from the approved Notion guide for a "
        "confirmed employment country. Call only after the user confirmed or "
        "corrected their location."
    )
)
async def get_parental_leave_guidance(
    country: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return global + country parental leave sections.

    Args:
        country: Confirmed employment country (uk, us, germany, serbia,
            france, or other). Prefer the value after location confirmation.
    """
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    confirmed = context.memory.get(user_location.MEMORY_CONFIRMED)
    if not confirmed:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "location_not_confirmed",
                "instruction": (
                    "Location is not confirmed yet. Call "
                    "detect_parental_leave_location if needed, ask the user "
                    "to confirm their employment country, set "
                    "user_country_confirmed=true, then retry."
                ),
            }
        )

    geography = _normalize_country(
        country or str(context.memory.get(user_location.MEMORY_COUNTRY) or "")
    )
    if geography:
        context.memory.set(user_location.MEMORY_COUNTRY, geography)
        context.memory.set(user_location.MEMORY_SOURCE, "user_override")

    try:
        page = await notion_client.get_page_with_body(
            POLICY_PAGE_ID,
            max_blocks=500,
        )
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "source_url": POLICY_PAGE_URL,
                "source_slack_link": POLICY_SLACK_LINK,
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_page_unavailable",
                "status_code": exc.response.status_code,
                "source_url": POLICY_PAGE_URL,
                "source_slack_link": POLICY_SLACK_LINK,
                "message": (
                    "The Parental Leave Guide is not visible to Sara's Notion "
                    "integration."
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "message": str(exc),
                "source_url": POLICY_PAGE_URL,
                "source_slack_link": POLICY_SLACK_LINK,
            }
        )

    body = page.get("body") or ""
    local_section = (
        _extract_section(body, geography) if geography in _SUPPORTED else None
    )

    return ToolResult(
        llm_response={
            "ok": True,
            "geography": geography,
            "geography_label": _GEO_LABELS.get(geography or "", geography),
            "eligibility_section": _extract_section(body, "eligibility"),
            "duration_section": _extract_section(body, "duration"),
            "notify_section": _extract_section(body, "notify"),
            "local_section": local_section,
            "return_section": _extract_section(body, "return"),
            "faq_section": _extract_section(body, "faq"),
            "source_title": page.get("title"),
            "source_url": page.get("url") or POLICY_PAGE_URL,
            "source_slack_link": POLICY_SLACK_LINK,
            "bamboo_slack_link": BAMBOO_SLACK_LINK,
            "source_last_edited_time": page.get("last_edited_time"),
            "instruction": (
                "Answer only from these sections. Lead with the global "
                "policy (eligibility/duration/notify) as relevant to the "
                "question, then include local_section only when geography is "
                "supported and the question needs country rules. If "
                "local_section is null, say the guide has no dedicated "
                "section for that country and point them to People Ops via "
                "the guide. Always end with source_slack_link. Use "
                "bamboo_slack_link when mentioning BambooHR. Never invent "
                "country rules."
            ),
        }
    )
