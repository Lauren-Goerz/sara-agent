"""Own sick-leave guidance from the Vacation and Sick days Notion page."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources, user_location, vacation_sick  # noqa: E402


@tool(
    description=(
        "Fetch own sick-leave steps and matching country rules from the "
        "approved Vacation and Sick days page."
    )
)
async def get_sick_leave_guidance(
    location_override: str | None = None,
    context: ToolContext = None,
) -> ToolResult:
    """Return own-illness sick guidance from the approved Notion source.

    Args:
        location_override: Country stated by the user when correcting or
            replacing the Slack-derived geography.
    """
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    location = await user_location.resolve(
        context,
        location_override=location_override,
    )
    geography = location["country"]
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

    everyone = vacation_sick.extract_section(page["body"], "everyone")
    surgery = vacation_sick.extract_section(page["body"], "surgery")
    local_section = (
        vacation_sick.extract_section(page["body"], geography)
        if location["has_local_policy"]
        else None
    )

    if not everyone:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "approved_sick_policy_missing_shared_section",
                "source_url": page["source_url"],
                "source_slack_link": source_link,
                "instruction": (
                    "Do not answer from memory. Say the approved page was found "
                    "but its 'For everyone' section could not be read."
                ),
            }
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
        return ToolResult()

    return ToolResult(
        llm_response={
            "ok": True,
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
