"""Resolve employment country before payslip routing."""

from __future__ import annotations

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import user_location


@tool(
    description=(
        "Resolve the employee's employment country for payslip routing from "
        "what they just said, session memory, or Slack profile."
    )
)
async def resolve_payslip_country(
    context: ToolContext = None,
) -> ToolResult:
    """Set project.user_country when it can be inferred; otherwise leave unset."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    location = await user_location.resolve(context)
    return ToolResult(
        llm_response={
            "ok": True,
            "country": location["country"],
            "ask_for_location": location["ask_for_location"],
        }
    )
