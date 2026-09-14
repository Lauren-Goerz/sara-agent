"""Vacation / offline / OOO booking steps from Vacation and Sick days."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources, vacation_sick  # noqa: E402

_TOPIC_TO_SECTION = {
    "vacation": "vacation_booking",
    "offline": "offline",
    "ooo": "ooo_template",
}


@tool(
    description=(
        "Fetch booking steps from Vacation and Sick days. Use topic=offline "
        "for overtime, public-holiday work, or offline days; topic=vacation "
        "to book vacation; topic=ooo for the OOO email template."
    )
)
async def get_leave_booking_guidance(
    topic: str = "vacation",
    context: ToolContext = None,
) -> ToolResult:
    """Return one booking section from the approved Notion page.

    Args:
        topic: vacation, offline (includes overtime / public holiday), or ooo.
    """
    topic_key = (topic or "vacation").strip().lower()
    if topic_key in {
        "overtime",
        "public_holiday",
        "public holiday",
        "holiday",
        "toil",
    }:
        topic_key = "offline"
    if topic_key not in _TOPIC_TO_SECTION:
        topic_key = "vacation"

    section_key = _TOPIC_TO_SECTION[topic_key]
    source_link = notion_sources.slack_link("vacation_sick")
    page = await notion_sources.load_full("vacation_sick")
    if not page.get("ok"):
        return ToolResult(
            llm_response={
                **page,
                "source_slack_link": source_link,
                "instruction": (
                    "Do not answer from memory. Say the approved page could "
                    "not be loaded and share source_slack_link."
                ),
            }
        )

    section = vacation_sick.extract_section(page["body"], section_key)
    if not section:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": f"{section_key}_missing",
                "source_slack_link": source_link,
                "instruction": (
                    "Do not answer from memory. Say that section could not be "
                    "read and share source_slack_link."
                ),
            }
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
