"""Slack Start date → first-6-months flag for L&D budget answers."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import slack_client, user_location  # noqa: E402


@tool(
    description=(
        "Read the requester's Slack Start date and whether they are still "
        "within their first 6 months at Rasa."
    )
)
async def get_ld_tenure(context: ToolContext = None) -> ToolResult:
    """Return whether the Slack requester is within their first 6 months.

    No args — uses the Slack user on the current message.
    """
    result: dict = {
        "ok": True,
        "within_first_six_months": None,
        "start_date": None,
    }
    user_id = user_location.slack_user_id(context) if context is not None else None
    if not user_id or not slack_client.configured():
        return ToolResult(llm_response=result)

    profile = await slack_client.get_user_start_date(user_id)
    if not profile.get("ok"):
        result["ok"] = False
        result["error"] = profile.get("error")
        return ToolResult(llm_response=result)

    raw = profile.get("start_date_raw")
    start = slack_client.parse_start_date(str(raw) if raw is not None else None)
    if start is None:
        return ToolResult(llm_response=result)

    result["start_date"] = start.isoformat()
    result["within_first_six_months"] = slack_client.within_first_n_months(start, 6)
    return ToolResult(llm_response=result)
