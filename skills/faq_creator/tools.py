"""Calculate Sara's age for FAQ response interpolation."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_FIRST_WORDS_DATE = date(2026, 8, 11)
_SARA_TIMEZONE = ZoneInfo("Europe/Berlin")


@tool(description="Calculate how many days Sara has been alive.")
async def calculate_sara_age(
    context: ToolContext = None,
) -> ToolResult:
    """Calculate and store Sara's age as human-readable text."""
    today = datetime.now(_SARA_TIMEZONE).date()
    days_alive = max((today - _FIRST_WORDS_DATE).days, 0)
    day_label = "day" if days_alive == 1 else "days"
    age_text = f"{days_alive:,} {day_label}"

    if context is not None:
        context.memory.set("age_text", age_text)

    return ToolResult(llm_response={"age_text": age_text})
