"""Dependent-care leave: sick child or other relative."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources, vacation_sick  # noqa: E402


@tool(
    description=(
        "Fetch leave guidance for caring for a sick child or another relative "
        "from the approved Vacation and Sick days page."
    )
)
async def get_dependent_care_guidance(
    case: str = "child",
    context: ToolContext = None,
) -> ToolResult:
    """Return dependent-care guidance from the approved Notion source.

    Args:
        case: Who needs care: child or family (parent, partner, sibling, etc.).
    """
    case_key = (case or "child").strip().lower()
    if case_key not in {"child", "family"}:
        case_key = "child"

    source_link = notion_sources.slack_link("vacation_sick")
    page = await notion_sources.load_full("vacation_sick")
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

    child_sick = vacation_sick.extract_section(page["body"], "child_sick")
    offline = vacation_sick.extract_section(page["body"], "offline")

    if case_key == "child" and not child_sick:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "child_sick_section_missing",
                "source_slack_link": source_link,
                "instruction": (
                    "Do not answer from memory. Say the sick-child FAQ could "
                    "not be read and share source_slack_link."
                ),
            }
        )

    if case_key == "child":
        return ToolResult(
            llm_response={
                "ok": True,
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

    return ToolResult(
        llm_response={
            "ok": True,
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
