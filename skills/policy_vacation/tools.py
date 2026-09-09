"""Vacation policy from Notion, personalized from the shared work country."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import httpx
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_client, notion_sources, user_location  # noqa: E402

POLICY_PAGE_ID = "137b9c0d544a80f3aae3eaaec6a7cf0a"
POLICY_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a"
)
POLICY_SLACK_LINK = (
    "<https://app.notion.com/p/rasa/"
    "Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a|Vacation and Sick days>"
)
HANDBOOKS_SLACK_LINK = (
    "<https://app.notion.com/p/rasa/"
    "Employee-Handbooks-defd5187553d4e8598e412a115679b40|Employee Handbooks>"
)
BENEFITS_SLACK_LINK = (
    "<https://app.notion.com/p/rasa/"
    "Benefits-Perks-2026-bd1165c5ece74392917d3b3eaffb4388|Benefits & Perks 2026>"
)

# Used only when the Notion page is not yet shared with Sara-Agent.
_FALLBACK_POLICY_BODY = """
## Carry-over
You can carry over vacation days to the next year, with a maximum of 10 days.
We highly recommend not carrying over more than 5 days. Use carried-over days
in BambooHR by March 31st of the following year; otherwise they are removed
from your vacation balance.

## Half days around holidays
On December 24th and 31st you only need to take half a day off to have a full
day off if it falls on a business day. Same applies to Orthodox Christmas Eve
on January 6th.
You can only take a half day on December 24th or January 6th - not both.

## Offline days
You can use up to 3 offline days per year.

## FAQ - What if I get sick during my vacation?
If you get sick during vacation for more than two days in a row, provide a
doctor's note and those vacation days can be returned to your vacation
balance so you don’t lose them.
"""

_SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "carry_over": ("carry-over", "carry over"),
    "half_days": ("half days around holidays", "half days around holiday"),
    "offline": ("offline days",),
    "sick_during_vacation": (
        "sick during my vacation",
        "sick during vacation",
    ),
}
_BOUNDARY_MARKERS = (
    "plan your vacation",
    "for everyone",
    "for employees in germany",
    "for employees in the uk",
    "for employees in uk",
    "for employees in serbia",
    "for employees in france",
    "for employees in the us",
    "for employees in us",
    "surgery leave",
    "hospital stay",
    "faq - ooo",
    "my kid got sick",
    *(
        marker
        for markers in _SECTION_MARKERS.values()
        for marker in markers
    ),
)


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
        selected.append(line)

    text = "\n".join(selected).strip()
    return text or None


async def _load_policy() -> dict[str, Any]:
    try:
        page = await notion_client.get_page_with_body(POLICY_PAGE_ID)
        return {**page, "source_mode": "notion"}
    except (httpx.HTTPError, RuntimeError, ValueError) as error:
        return {
            "id": POLICY_PAGE_ID,
            "title": "Vacation and Sick days",
            "url": POLICY_PAGE_URL,
            "last_edited_time": None,
            "body": _FALLBACK_POLICY_BODY,
            "attachments": [],
            "attachment_count": 0,
            "source_mode": "fallback_snapshot",
            "fallback_reason": str(error),
        }


@tool(
    description=(
        "Fetch vacation day entitlement from Benefits & Perks 2026, plus "
        "shared vacation rules from Vacation and Sick days. Call for how "
        "many vacation/PTO days someone gets, carry-over, half days, and "
        "country PTO policy — not for how to book time off."
    )
)
async def get_vacation_policy_guidance(
    location_override: str | None = None,
    question: str | None = None,
    context: ToolContext = None,
) -> ToolResult:
    """Return vacation policy for the employee's work country.

    Args:
        location_override: Country they stated or corrected this turn.
        question: What they asked (how many days, carry-over, half days, …).
    """
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    location = await user_location.resolve(
        context,
        location_override=location_override,
    )
    geography = location["country"]

    benefits_query = " ".join(
        part
        for part in (
            "vacation days PTO annual leave entitlement allowance",
            location["country_label"] or geography or "",
            (question or "").strip(),
        )
        if part
    )
    benefits = await notion_sources.load("benefits", query=benefits_query)

    page = await _load_policy()
    body = page.get("body") or ""
    shared_sections = {
        key: _extract_section(body, key) for key in _SECTION_MARKERS
    }

    handbook_section = None
    handbook_ok = False
    if location["has_local_policy"]:
        query_bits = [
            location["country_label"] or "",
            "vacation",
            "PTO",
            "annual leave",
            "holiday entitlement",
            "carry-over",
            (question or "").strip(),
        ]
        handbook = await notion_sources.load(
            "employee_handbooks",
            query=" ".join(part for part in query_bits if part),
        )
        handbook_ok = bool(handbook.get("ok"))
        if handbook_ok:
            handbook_section = handbook.get("source_content")

    if location["ask_for_location"]:
        await user_location.send_country_picker(
            context,
            "Which country are you employed in for vacation policy?",
            options=user_location.STANDARD_COUNTRY_OPTIONS,
        )
        return ToolResult()

    return ToolResult(
        llm_response={
            "ok": True,
            "source_title": page.get("title"),
            "source_url": page.get("url") or POLICY_PAGE_URL,
            "source_slack_link": POLICY_SLACK_LINK,
            "entitlement_ok": bool(benefits.get("ok")),
            "entitlement_content": benefits.get("source_content"),
            "entitlement_url": benefits.get("source_url"),
            "entitlement_slack_link": BENEFITS_SLACK_LINK,
            "handbooks_slack_link": HANDBOOKS_SLACK_LINK,
            "source_last_edited_time": page.get("last_edited_time"),
            "source_mode": page.get("source_mode"),
            "shared_sections": shared_sections,
            "geography": geography,
            "geography_label": location["country_label"],
            "local_section": handbook_section if handbook_ok else None,
            "handbook_section": handbook_section if handbook_ok else None,
            "handbook_available": handbook_ok,
            "timezone": location["timezone"],
            "profile_location": location["profile_location"],
            "location_source": location["location_source"],
            "inferred_from_slack": location["inferred_from_slack"],
            "required_preface": location["required_preface"],
            "ask_for_location": location["ask_for_location"],
            "instruction": (
                "For how many vacation days they get, use only "
                "entitlement_content (Benefits & Perks 2026). Quote the "
                "number for their geography only — never invent days or copy "
                "another country's figure. Always paste entitlement_slack_link. "
                "If entitlement_ok is false, share that link and say the "
                "day count is on the Benefits page. For carry-over, half days, "
                "offline days, or sick-during-vacation, use shared_sections "
                "and paste source_slack_link. Handbook text is extra context "
                "only, never a substitute for the Benefits day count. If "
                "required_preface is present, begin with that exact sentence."
            ),
        }
    )
