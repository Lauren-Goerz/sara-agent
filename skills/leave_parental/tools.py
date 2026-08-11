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

from lib import notion_client, slack_client  # noqa: E402

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

_TIMEZONE_TO_GEO: dict[str, str] = {
    "Europe/Berlin": "germany",
    "Europe/Busingen": "germany",
    "Europe/London": "uk",
    "Europe/Belfast": "uk",
    "Europe/Guernsey": "uk",
    "Europe/Isle_of_Man": "uk",
    "Europe/Jersey": "uk",
    "Europe/Belgrade": "serbia",
    "Europe/Paris": "france",
    "America/New_York": "us",
    "America/Detroit": "us",
    "America/Kentucky/Louisville": "us",
    "America/Kentucky/Monticello": "us",
    "America/Indiana/Indianapolis": "us",
    "America/Indiana/Vincennes": "us",
    "America/Indiana/Winamac": "us",
    "America/Indiana/Marengo": "us",
    "America/Indiana/Petersburg": "us",
    "America/Indiana/Vevay": "us",
    "America/Chicago": "us",
    "America/Indiana/Tell_City": "us",
    "America/Indiana/Knox": "us",
    "America/Menominee": "us",
    "America/North_Dakota/Center": "us",
    "America/North_Dakota/New_Salem": "us",
    "America/North_Dakota/Beulah": "us",
    "America/Denver": "us",
    "America/Boise": "us",
    "America/Phoenix": "us",
    "America/Los_Angeles": "us",
    "America/Anchorage": "us",
    "America/Juneau": "us",
    "America/Sitka": "us",
    "America/Metlakatla": "us",
    "America/Yakutat": "us",
    "America/Nome": "us",
    "America/Adak": "us",
    "Pacific/Honolulu": "us",
}

_COUNTRY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "germany",
        re.compile(
            r"\b(germany|deutschland|berlin|munich|m[uü]nchen|hamburg|"
            r"cologne|k[oö]ln|frankfurt)\b",
            re.I,
        ),
    ),
    (
        "uk",
        re.compile(
            r"\b(uk|u\.k\.|united kingdom|britain|england|scotland|wales|"
            r"london|manchester|edinburgh)\b",
            re.I,
        ),
    ),
    (
        "serbia",
        re.compile(r"\b(serbia|serbian|belgrade|beograd)\b", re.I),
    ),
    (
        "france",
        re.compile(r"\b(france|french|paris|lyon|marseille)\b", re.I),
    ),
    (
        "us",
        re.compile(
            r"\b(usa|u\.s\.a\.|u\.s\.|united states|america|"
            r"san francisco|new york|nyc|seattle|austin|boston)\b",
            re.I,
        ),
    ),
]

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


def _slack_user_id(context: ToolContext) -> str | None:
    for event in reversed(context.events):
        metadata = getattr(event, "metadata", None) or {}
        candidate = metadata.get("slack_user_id")
        if isinstance(candidate, str) and candidate.startswith("U"):
            return candidate
        for user in metadata.get("users") or []:
            if isinstance(user, str) and user.startswith("U"):
                return user
    return None


def _geo_from_text(value: str | None) -> str | None:
    if not value:
        return None
    for geography, pattern in _COUNTRY_PATTERNS:
        if pattern.search(value):
            return geography
    return None


def _normalize_country(value: str | None) -> str | None:
    raw = (value or "").strip().lower()
    if not raw:
        return None
    if raw in _SUPPORTED or raw == "other":
        return raw
    mapped = _geo_from_text(raw)
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


def _detect_from_profile(
    profile_location: str | None,
    timezone: str | None,
) -> tuple[str | None, str | None, str]:
    """Return (geography, location_source, display_label)."""
    if profile_location:
        geography = _geo_from_text(str(profile_location))
        if geography:
            return geography, "slack_profile", _GEO_LABELS[geography]
        return None, "slack_profile", str(profile_location)

    if timezone:
        geography = _TIMEZONE_TO_GEO.get(str(timezone))
        if geography:
            return geography, "slack_timezone", _GEO_LABELS[geography]
        return None, "slack_timezone", str(timezone)

    return None, None, ""


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

    timezone: str | None = None
    profile_location: str | None = None
    geography: str | None = None
    location_source: str | None = None
    display_label = ""

    slack_user_id = _slack_user_id(context)
    if slack_user_id and slack_client.configured():
        profile = await slack_client.get_user_location(slack_user_id)
        timezone = profile.get("timezone")
        profile_location = profile.get("location")
        geography, location_source, display_label = _detect_from_profile(
            profile_location,
            timezone,
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
                "France. After they confirm or correct, set parental_country "
                "and location_confirmed=true, then call "
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

    confirmed = context.memory.get("location_confirmed")
    if not confirmed:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "location_not_confirmed",
                "instruction": (
                    "Location is not confirmed yet. Call "
                    "detect_parental_leave_location if needed, ask the user "
                    "to confirm their employment country, set "
                    "location_confirmed=true, then retry."
                ),
            }
        )

    geography = _normalize_country(
        country or str(context.memory.get("parental_country") or "")
    )
    if geography:
        context.memory.set("parental_country", geography)

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
