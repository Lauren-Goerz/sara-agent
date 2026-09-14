"""Vacation policy from Notion, personalized from the shared work country."""

from __future__ import annotations

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

    page = await notion_sources.load_full("vacation_sick")
    body = page.get("body") or ""
    shared_sections = {
        key: vacation_sick.extract_section(body, key)
        for key in vacation_sick.VACATION_POLICY_SECTIONS
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
            "source_title": page.get("page_title"),
            "source_url": page.get("source_url"),
            "source_slack_link": notion_sources.slack_link("vacation_sick"),
            "entitlement_ok": bool(benefits.get("ok")),
            "entitlement_content": benefits.get("source_content"),
            "entitlement_url": benefits.get("source_url"),
            "entitlement_slack_link": notion_sources.slack_link("benefits"),
            "handbooks_slack_link": notion_sources.slack_link(
                "employee_handbooks"
            ),
            "source_last_edited_time": page.get("last_edited_time"),
            "source_mode": page.get("source_kind"),
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
                "and paste source_slack_link. If shared_sections.carry_over is "
                "present, answer carry-over from that text only — never say the "
                "page has no carry-over rule. For offline days (including "
                "overtime or public-holiday balance), always say they must "
                "speak with their Manager first before booking, then quote the "
                "yearly limit from shared_sections.offline. Handbook text is "
                "extra context only, never a substitute for the Benefits day "
                "count. If required_preface is present, begin with that exact "
                "sentence."
            ),
        }
    )
