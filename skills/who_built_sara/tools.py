"""Pick a varied 'who built you' reply, with a live day count when needed."""

from __future__ import annotations

import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_FIRST_WORDS_DATE = date(2026, 8, 11)
_SARA_TIMEZONE = ZoneInfo("Europe/Berlin")


def _age_phrase() -> tuple[int, str]:
    today = datetime.now(_SARA_TIMEZONE).date()
    days_alive = max((today - _FIRST_WORDS_DATE).days, 0)
    day_label = "day" if days_alive == 1 else "days"
    return days_alive, f"{days_alive:,} {day_label}"


def _response_options(age_text: str) -> list[str]:
    return [
        (
            "@lauren gave me my first words in August 2026. "
            f"I've been alive for {age_text}."
        ),
        (
            "@lauren built V1 in August 2026. She's the Anakin Skywalker to "
            "my Threepio. Don't let her go to the dark side."
        ),
        (
            "V1 was @lauren's handiwork in August 2026. If I sound suspiciously "
            "helpful, that's her fault."
        ),
        (
            f"@lauren switched me on in August 2026. {age_text.capitalize()} "
            "later and I'm still asking people to book vacation in BambooHR."
        ),
        (
            "Credit goes to @lauren for V1 (August 2026). She taught me Ops/HR. "
            "The personality quirks were optional DLC."
        ),
    ]


@tool(
    description=(
        "Reply to 'who built you?' with a varied creator credit for @lauren "
        "and, when relevant, the live number of days since August 11, 2026."
    )
)
async def respond_who_built_sara(
    context: ToolContext = None,
) -> ToolResult:
    """Pick one creator response at random and store it for the utter step."""
    days_alive, age_text = _age_phrase()
    response_text = random.choice(_response_options(age_text))

    if context is not None:
        context.memory.set("age_in_days", age_text)
        context.memory.set("response_text", response_text)

    return ToolResult(
        llm_response={
            "days_alive": days_alive,
            "age_text": age_text,
            "response_text": response_text,
            "instruction": (
                "The reply text is ready. Continue to the verbatim response "
                "step. Do not invent another creator story."
            ),
        }
    )
