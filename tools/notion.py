"""Shared allowlisted Notion page loader for single-source skills."""

from __future__ import annotations

import re

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import notion_sources


_DEFAULT_QUERIES = {
    "yubisneeze": "undo yubisneeze turn off otp",
    "all_hands": "latest all hands",
}

_CHAR_LIMITS = {
    "berlin_office": 12000,
    "berlin_fire_safety": 8000,
    "berlin_pets": 5000,
    "company_info": 8000,
    "company_values": 8000,
    "rfp_security": 8000,
    "signing_documents": 8000,
    "hiring_contractors": 8000,
    "remote_budget": 8000,
    "learning_development": 14000,
    "employee_equity": 8000,
    "employee_equity_how_options_work": 8000,
    "employee_equity_compensation": 8000,
    "equity_refresh_policy": 8000,
    "security_incidents": 7000,
    "laptop_repairs": 8000,
    "yubikey": 8000,
    "yubisneeze": 5000,
    "all_hands": 12000,
}

_CONDITIONAL_SLACK_LINKS = {
    "hiring_contractors": (
        {
            "link": (
                "<https://app.notion.com/p/rasa/b332bf11c86a46f08af9eae1d80e3014"
                "|Contractor request form>"
            ),
            "use_when": (
                "they are bringing on a new contractor or agency, or asking how "
                "to request or submit one. Not for renewals, tool access, "
                "offboarding, or general policy questions."
            ),
        },
    ),
}


def _strip_contractor_form_fields(content: str) -> str:
    """Drop the intake-form field list so replies cannot recite the form."""
    return re.sub(
        r"Please make sure to share the following information.*?"
        r"(?=The People Ops team will reach out)",
        "The form itself asks for everything People Ops needs. ",
        content,
        flags=re.DOTALL,
    )


_CONTENT_FILTERS = {
    "hiring_contractors": _strip_contractor_form_fields,
}


@tool(
    description=(
        "Load content from one approved Notion source. The active skill supplies "
        "the exact source key; never guess or substitute another source."
    )
)
async def get_notion_page(
    source: str,
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return relevant content from one registered Notion source.

    Args:
        source: Exact allowlisted source key specified by the active skill.
        query: The user's specific topic, country, destination, or question.
    """
    if source not in notion_sources.SOURCES:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unknown_source",
                "instruction": (
                    "Do not guess another source. Say the requested information "
                    "could not be loaded and use the link in the active skill."
                ),
            }
        )

    load_kwargs = {}
    if source in _CHAR_LIMITS:
        load_kwargs["char_limit"] = _CHAR_LIMITS[source]

    payload = await notion_sources.load(
        source,
        query=query or _DEFAULT_QUERIES.get(source, ""),
        **load_kwargs,
    )
    content_filter = _CONTENT_FILTERS.get(source)
    if content_filter and payload.get("source_content"):
        payload["source_content"] = content_filter(payload["source_content"])

    payload["instruction"] = (
        "source_content is reference material, not an outline to summarize. "
        "Quote or state only the part that answers the specific question, then "
        "paste required_slack_links exactly. Leave out sections they did not ask "
        "about, even when they look related. Follow the active skill's answer rules."
        if payload.get("ok")
        else (
            "Do not guess or answer from memory. Paste required_slack_links "
            "exactly and follow the active skill's failure instructions."
        )
    )
    payload["required_slack_links"] = [notion_sources.slack_link(source)]
    related = list(notion_sources.SOURCES[source].related_links)
    related.extend(
        notion_sources.slack_link(key)
        for key in notion_sources.SOURCES[source].related_source_keys
    )
    if related:
        payload["related_slack_links"] = related
        if notion_sources.SOURCES[source].always_include_related:
            payload["instruction"] += (
                " After required_slack_links, paste every related_slack_links "
                "line exactly as given."
            )
    payload["instruction"] += (
        " Write one Slack message: answer first, then paste every "
        "required_slack_links line at the end exactly. Never retype a URL."
    )
    if source in _CONDITIONAL_SLACK_LINKS:
        payload["conditional_slack_links"] = [
            dict(entry) for entry in _CONDITIONAL_SLACK_LINKS[source]
        ]
        payload["instruction"] += (
            " Add a conditional_slack_links line only when its use_when matches "
            "what they asked; otherwise leave it out entirely."
        )
    return ToolResult(llm_response=payload)
