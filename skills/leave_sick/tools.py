"""Sick-leave guidance sourced only from the approved Notion policy page."""

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

POLICY_PAGE_ID = "137b9c0d544a80f3aae3eaaec6a7cf0a"
POLICY_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a"
)
POLICY_SLACK_LINK = (
    "<https://app.notion.com/p/rasa/"
    "Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a|Vacation and Sick days>"
)
BAMBOO_HOME_URL = "https://rasa.bamboohr.com/home/"
BAMBOO_SLACK_LINK = "<https://rasa.bamboohr.com/home/|rasa.bamboohr.com>"

# Used only when the Notion page is not yet shared with Sara-Agent.
_FALLBACK_POLICY_BODY = """
## For everyone:
1. Take time off until you feel better.
2. Request a sick day in Bamboo (<https://rasa.bamboohr.com/home/|rasa.bamboohr.com>) and your Manager gets a notification that you are offline
   - Add them from day one onwards
3. Inform affected team members.
4. Set up "Out of Office" in your Google Calendar so meeting requests will be automatically declined.
5. Set yourself as away in Slack.
6. Set up an out of office automatic email response.

## Additional tasks depending on your country:

## For employees in Germany
If you're sick for more than five days in a row, we need a sick certificate from your doctor. All sick leave certificates are transferred digital from your doctor to the health insurance. We as employer need the following information via email, slack or phone:
- Duration of sick leave.
- Did you see a doctor or was sick leave because of a hospital stay.
For questions reach out to the People Team.

## For employees in the UK
If you're sick for more than five days in a row, we need a sick note from your doctor. Please send the note to peopleteam@rasa.com.
Once you need to go on sick leave (passed the company benefit), there is a 48 hour window to notify the company and the CPAM (health insurance organisation) that you are on sick leave.

## For employees in Serbia
If you are sick for more than five days in a row, we need a doctor's certificate from your state doctor. Please sent the note to the peopleteam@rasa.com. Keep in mind that different types of sick leave affect payroll, for detailed information please contact peopleteam@rasa.com

## For employees in France
There is a form that is required from your doctor called "avis d'arrêt de travail" (notice of sick leave). The first two pages of this document are sent to the CPAM and the final third page needs to be sent to Rasa. The company is also to inform the CPAM as confirmation of your sick leave. Please send the filled out and signed form to peopleteam@rasa.com.
Further information on payments are provided in the collective bargaining agreement SYNTEC.

## For employees in the US
If you're sick for more than five days in a row, we need a sick certificate from your doctor.
For questions reach out to the People Team.

## Surgery Leave / Hospital Stay
If you need to undergo surgery, please make sure to record a sick day in Bamboo (<https://rasa.bamboohr.com/home/|rasa.bamboohr.com>) as well.
If the hospital in your location is able to provide a doctor's note, please share it with us. We understand that this may not be possible in every country, but in many locations it is required.
Thank you for your cooperation.
"""

_SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "everyone": ("for everyone",),
    "germany": ("for employees in germany",),
    "uk": ("for employees in the uk", "for employees in uk"),
    "serbia": ("for employees in serbia",),
    "france": ("for employees in france",),
    "us": ("for employees in the us", "for employees in us"),
    "surgery": ("surgery leave", "hospital stay"),
}
_BOUNDARY_MARKERS = (
    "additional tasks depending on your country",
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
    """Extract one named section from flattened Notion block text."""
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
    """Fetch the approved page; fall back to the maintained snapshot if unshared."""
    try:
        page = await notion_client.get_page_with_body(POLICY_PAGE_ID)
        return {
            **page,
            "source_mode": "notion",
        }
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
        "Fetch the approved Vacation and Sick days Notion page and return only "
        "the shared sick-leave section plus the Slack user's matching geography."
    )
)
async def get_sick_leave_guidance(
    location_override: str | None = None,
    context: ToolContext = None,
) -> ToolResult:
    """Return sick guidance from the single approved Notion source.

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

    page = await _load_policy()
    everyone = _extract_section(page["body"], "everyone")
    surgery = _extract_section(page["body"], "surgery")
    local_section = (
        _extract_section(page["body"], geography)
        if location["has_local_policy"]
        else None
    )

    if not everyone:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "approved_sick_policy_missing_shared_section",
                "source_url": page.get("url") or POLICY_PAGE_URL,
                "instruction": (
                    "Do not answer from memory. Say the approved page was found "
                    "but its 'For everyone' section could not be read."
                ),
            }
        )

    # Germany: People Team is fine, but do not invent peopleteam@rasa.com.
    if geography == "germany" and local_section:
        local_section = re.sub(
            r"peopleteam@rasa\.com",
            "the People Team",
            local_section,
            flags=re.I,
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "source_title": page.get("title"),
            "source_url": page.get("url") or POLICY_PAGE_URL,
            "source_slack_link": POLICY_SLACK_LINK,
            "bamboo_home_url": BAMBOO_HOME_URL,
            "bamboo_slack_link": BAMBOO_SLACK_LINK,
            "source_last_edited_time": page.get("last_edited_time"),
            "source_mode": page.get("source_mode"),
            "everyone_section": everyone,
            "geography": geography,
            "local_section": local_section,
            "surgery_section": surgery,
            "timezone": location["timezone"],
            "profile_location": location["profile_location"],
            "location_source": location["location_source"],
            "inferred_from_slack": location["inferred_from_slack"],
            "required_preface": location["required_preface"],
            "ask_for_location": location["ask_for_location"],
            "forbid_peopleteam_email": geography == "germany",
            "instruction": (
                "Use only everyone_section, local_section, and surgery_section "
                "from this result. Never use another page. If required_preface "
                "is present, begin with that exact sentence before geography "
                "content. Include only the matching local_section. India and "
                "unsupported geographies have local_section=null: do not mention "
                "any country section. If forbid_peopleteam_email is true, never "
                "tell them to email peopleteam@rasa.com. If ask_for_location is "
                "true, give everyone_section and ask for country only if local "
                "rules are needed. Always paste source_slack_link and "
                "bamboo_slack_link as-is (Slack hyperlinks). Never write bare "
                "URLs or wrap links in backticks."
            ),
        }
    )
