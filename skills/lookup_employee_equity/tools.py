"""Fetch Rasa employee equity guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

_RELATED = [
    {
        "key": "employee_equity",
        "title": "Employee Equity",
        "url": notion_sources.SOURCES["employee_equity"].url,
    },
    {
        "key": "employee_equity_how_options_work",
        "title": "How Options Work",
        "url": notion_sources.SOURCES["employee_equity_how_options_work"].url,
    },
    {
        "key": "employee_equity_compensation",
        "title": "How We Use Options as Compensation",
        "url": notion_sources.SOURCES["employee_equity_compensation"].url,
    },
    {
        "key": "equity_refresh_policy",
        "title": "Equity Refresh Policy",
        "url": notion_sources.SOURCES["equity_refresh_policy"].url,
    },
]

_PAGE_HINTS = (
    (
        "equity_refresh_policy",
        (
            "refresh",
            "top up",
            "top-up",
            "topup",
            "topped",
            "anniversary",
            "every two years",
            "2 year",
            "two year",
        ),
    ),
    (
        "employee_equity_how_options_work",
        (
            "carta",
            "where",
            "see my",
            "view my",
            "login",
            "portal",
            "exercise",
            "how options work",
            "what is an option",
            "vesting",
            "cliff",
            "strike",
            "409a",
            "tax",
        ),
    ),
    (
        "employee_equity_compensation",
        (
            "how many",
            "how much",
            "initial",
            "grant size",
            "promotion",
            "seniority",
            "location",
            "part-time",
            "part time",
            "leave",
            "who gets",
            "eligible",
            "compensation",
        ),
    ),
    (
        "employee_equity",
        (
            "overview",
            "dei",
            "employee equity",
        ),
    ),
)

_SUCCESS = (
    "Answer the equity question using only source_content. Keep it short "
    "and Slack-friendly. Always share all related_urls at the end. Never "
    "invent grant sizes, vesting terms, platforms, or refresh rules. For "
    "personal 'how much equity do I have' questions: say you cannot see "
    "individual balances; if the page names where to look (e.g. Carta), "
    "share that, otherwise People Ops. Never invent a platform. If "
    "content_truncated is true and the answer is not here, check "
    "other_sections and say what you could not confirm. If the answer is "
    "not on this page, say so and point people to the related_urls."
)
_FAILURE = (
    "Share all related_urls. Do not invent grant sizes, vesting terms, "
    "platforms, or refresh rules. For personal balance questions, say you "
    "cannot see individual equity and point them to People Ops (and Carta "
    "only if a loaded page named it)."
)


def _pick_source_key(query: str) -> str:
    text = (query or "").strip().lower()
    if not text:
        return "employee_equity_compensation"
    for key, hints in _PAGE_HINTS:
        if any(hint in text for hint in hints):
            return key
    return "employee_equity_compensation"


@tool(
    description=(
        "Fetch Rasa employee equity guidance from Notion. Picks Employee "
        "Equity overview, How Options Work (incl. Carta), How We Use Options "
        "as Compensation, or Equity Refresh Policy based on the query."
    )
)
async def get_employee_equity(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the best-matching employee equity page for the question.

    Args:
        query: Topic (e.g. initial grant, refresh, Carta, where to see equity).
    """
    source_key = _pick_source_key(query)
    payload = await notion_sources.load(source_key, query=query)
    # Refresh policy page may not be shared yet; compensation page also
    # covers refresh grants.
    if not payload.get("ok") and source_key == "equity_refresh_policy":
        source_key = "employee_equity_compensation"
        payload = await notion_sources.load(source_key, query=query)
    payload["selected_page"] = source_key
    payload["related_urls"] = _RELATED
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
