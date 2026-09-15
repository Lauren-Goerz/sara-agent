"""Shared Vacation and Sick days guidance for leave_* skills.

Topics: sick, dependent_child, dependent_family, vacation, offline, ooo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources, user_location, vacation_sick  # noqa: E402

_BOOKING_TOPICS = {
    "vacation": "vacation_booking",
    "offline": "offline",
    "ooo": "ooo_template",
}
_OFFLINE_ALIASES = {
    "overtime",
    "public_holiday",
    "public holiday",
    "holiday",
    "toil",
}


def _fail(source_link: str, error: str, detail: str) -> ToolResult:
    return ToolResult(
        llm_response={
            "ok": False,
            "error": error,
            "source_slack_link": source_link,
            "instruction": (
                f"Do not answer from memory. {detail} Share source_slack_link."
            ),
        }
    )


async def _load_page() -> tuple[dict, str]:
    source_link = notion_sources.slack_link("vacation_sick")
    page = await notion_sources.load_full("vacation_sick")
    return page, source_link


@tool(
    description=(
        "Load Vacation and Sick days guidance. topic: sick (own illness), "
        "dependent_child, dependent_family, vacation (book PTO), offline "
        "(overtime / public holiday / offline days), or ooo (OOO template)."
    )
)
async def get_vacation_sick_guidance(
    topic: str = "sick",
    location_override: str | None = None,
    context: ToolContext = None,
) -> ToolResult:
    """Return one topic from the approved Vacation and Sick days page.

    Args:
        topic: sick, dependent_child, dependent_family, vacation, offline, or ooo.
        location_override: Country the user stated when correcting geography
            (sick topic only).
    """
    topic_key = (topic or "sick").strip().lower().replace("-", "_")
    if topic_key in _OFFLINE_ALIASES:
        topic_key = "offline"
    if topic_key in {"child", "dependent"}:
        topic_key = "dependent_child"
    if topic_key in {"family", "relative"}:
        topic_key = "dependent_family"

    page, source_link = await _load_page()
    if not page.get("ok"):
        return ToolResult(
            llm_response={
                **page,
                "source_slack_link": source_link,
                "instruction": (
                    "Do not answer from memory. Say the approved policy could "
                    "not be loaded and share source_slack_link."
                ),
            }
        )
    body = page.get("body") or ""

    if topic_key == "sick":
        return await _sick(body, source_link, location_override, context)
    if topic_key == "dependent_child":
        return _dependent_child(body, source_link)
    if topic_key == "dependent_family":
        return _dependent_family(body, source_link)
    if topic_key in _BOOKING_TOPICS:
        return _booking(body, source_link, topic_key)

    return _fail(
        source_link,
        "unknown_topic",
        "Say the leave topic was not recognised.",
    )


async def _sick(
    body: str,
    source_link: str,
    location_override: str | None,
    context: ToolContext | None,
) -> ToolResult:
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    location = await user_location.resolve(
        context,
        location_override=location_override,
    )
    geography = location["country"]
    everyone = vacation_sick.extract_section(body, "everyone")
    surgery = vacation_sick.extract_section(body, "surgery")
    local_section = (
        vacation_sick.extract_section(body, geography)
        if location["has_local_policy"]
        else None
    )

    if not everyone:
        return _fail(
            source_link,
            "approved_sick_policy_missing_shared_section",
            "Say the approved page was found but its 'For everyone' section "
            "could not be read.",
        )

    if geography == "germany" and local_section:
        local_section = re.sub(
            r"peopleteam@rasa\.com",
            "the People Team",
            local_section,
            flags=re.I,
        )

    if location["ask_for_location"]:
        await user_location.send_country_picker(
            context,
            "Which country are you employed in for local sick-leave rules?",
            options=user_location.STANDARD_COUNTRY_OPTIONS,
        )
        return ToolResult(
            llm_response={
                "ok": True,
                "topic": "sick",
                "ask_for_location": True,
                "instruction": (
                    "A country picker was already sent. Wait for their reply, "
                    "then call again with location_override."
                ),
            }
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "topic": "sick",
            "source_slack_link": source_link,
            "bamboo_slack_link": vacation_sick.BAMBOO_SLACK_LINK,
            "everyone_section": everyone,
            "local_section": local_section,
            "surgery_section": surgery,
            "geography": geography,
            "required_preface": (
                location["required_preface"] if local_section else None
            ),
            "ask_for_location": False,
            "forbid_peopleteam_email": geography == "germany",
            "instruction": (
                "Answer from everyone_section, then local_section only if "
                "present, and surgery_section only when they asked about "
                "surgery or a hospital stay. Book sick leave from day one even "
                "if they worked a few hours. Never invent partial sick time or "
                "another leave type. If required_preface is present, begin with "
                "that exact sentence before local_section. If "
                "forbid_peopleteam_email is true, never tell them to email "
                "peopleteam@rasa.com. Paste source_slack_link, and "
                "bamboo_slack_link when booking is mentioned, exactly."
            ),
        }
    )


def _dependent_child(body: str, source_link: str) -> ToolResult:
    child_sick = vacation_sick.extract_section(body, "child_sick")
    if not child_sick:
        return _fail(
            source_link,
            "child_sick_section_missing",
            "Say the sick-child FAQ could not be read.",
        )
    return ToolResult(
        llm_response={
            "ok": True,
            "topic": "dependent_child",
            "case": "child",
            "source_slack_link": source_link,
            "bamboo_slack_link": vacation_sick.BAMBOO_SLACK_LINK,
            "child_sick_section": child_sick,
            "instruction": (
                "Answer only from child_sick_section. If they still work "
                "some hours, they book nothing. They book a normal sick day "
                "only when taking the day off. Never invent a 'sick child' "
                "leave type, partial sick time, vacation, or offline day. "
                "Paste source_slack_link, and bamboo_slack_link when booking "
                "is mentioned, exactly."
            ),
        }
    )


def _dependent_family(body: str, source_link: str) -> ToolResult:
    offline = vacation_sick.extract_section(body, "offline")
    return ToolResult(
        llm_response={
            "ok": True,
            "topic": "dependent_family",
            "case": "family",
            "source_slack_link": source_link,
            "bamboo_slack_link": vacation_sick.BAMBOO_SLACK_LINK,
            "family_care_section": vacation_sick.FAMILY_CARE_GUIDANCE,
            "offline_section": offline,
            "instruction": (
                "Answer only from family_care_section. It is case by case: "
                "first day as sick after telling their Manager, then Manager "
                "and People Ops for longer absences with some offline days. "
                "Never call the whole absence sick leave or require vacation. "
                "Use offline_section only if they ask how many offline days "
                "they get. Paste source_slack_link, and bamboo_slack_link when "
                "booking is mentioned, exactly."
            ),
        }
    )


def _booking(body: str, source_link: str, topic_key: str) -> ToolResult:
    section_key = _BOOKING_TOPICS[topic_key]
    section = vacation_sick.extract_section(body, section_key)
    if not section:
        return _fail(
            source_link,
            f"{section_key}_missing",
            "Say that section could not be read.",
        )

    if topic_key == "offline":
        instruction = (
            "Answer only from section_text. Overtime or working on a public "
            "holiday is compensated with an offline day — never invent overtime "
            "pay. Always say they must speak with their Manager first before "
            "booking an offline day; that is mandatory, not optional. Then "
            "cover Bamboo booking, calendar OOO if on the page, examples, and "
            "the yearly offline-day limit. Paste source_slack_link and "
            "bamboo_slack_link exactly."
        )
    elif topic_key == "ooo":
        instruction = (
            "Answer only from section_text with the OOO template. Paste "
            "source_slack_link exactly."
        )
    else:
        instruction = (
            "Answer only from section_text for booking vacation (not offline). "
            "Include Bamboo and OOO steps from the section. Paste "
            "source_slack_link and bamboo_slack_link exactly."
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "topic": topic_key,
            "source_slack_link": source_link,
            "bamboo_slack_link": vacation_sick.BAMBOO_SLACK_LINK,
            "section_text": section,
            "must_confirm_with_manager": topic_key == "offline",
            "instruction": instruction,
        }
    )
