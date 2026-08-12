"""Fetch 'undo the Yubisneeze' guidance from the YubiKey Notion page."""

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
    "Help them undo the Yubisneeze / turn off accidental OTP using only "
    "source_content. If their message was a long modhex OTP paste, briefly "
    "acknowledge the sneeze without repeating the full string. Keep it short "
    "and Slack-friendly. Always share source_url. Do not invent recovery, "
    "password-reset, YubiKey Manager, or security steps that are not on the "
    "page."
)
_FAILURE = (
    "Share source_url (the Yubisneeze section) and ask them to follow the "
    "undo steps there. Do not invent steps."
)


@tool(
    description=(
        "Fetch guidance for undoing a Yubisneeze (accidental YubiKey touch / "
        "OTP paste) from the designated Notion section. Call for every "
        "Yubisneeze undo request."
    )
)
async def get_yubisneeze_undo_guidance(context: ToolContext = None) -> ToolResult:
    """Return Yubisneeze undo steps from Notion when available."""
    payload = await notion_sources.load(
        "yubisneeze",
        query="undo yubisneeze turn off otp",
        char_limit=5000,
    )
    payload["instruction"] = _SUCCESS if payload["ok"] else _FAILURE
    return ToolResult(llm_response=payload)
