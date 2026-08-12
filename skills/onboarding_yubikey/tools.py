"""Fetch YubiKey setup guidance from the designated Notion onboarding page."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

_SUCCESS = (
    "Walk the person through YubiKey installation using only source_content. "
    "Keep it short and Slack-friendly. Prefer numbered steps that match the "
    "page. Always share source_url. Do not invent PIN, Google, Slack, or "
    "hardware steps that are not on the page."
)
_FAILURE = (
    "Share source_url and ask them to follow the install steps there. Do not "
    "invent YubiKey setup steps."
)


@tool(
    description=(
        "Fetch Rasa YubiKey installation and Google phone security setup "
        "guidance from the designated Notion onboarding page. Call for every "
        "YubiKey / security-key install request."
    )
)
async def get_yubikey_setup_guidance(context: ToolContext = None) -> ToolResult:
    """Return live YubiKey setup guidance from Notion."""
    payload = await notion_sources.load(
        "yubikey",
        query="install setup security key",
        char_limit=8000,
    )
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
