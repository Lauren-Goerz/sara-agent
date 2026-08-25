"""Fetch 'undo the Yubisneeze' guidance from the YubiKey Notion page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_yubisneeze_undo_guidance = notion_page_tool(
    name="get_yubisneeze_undo_guidance",
    source="yubisneeze",
    description=(
        "Fetch guidance for undoing a Yubisneeze (accidental YubiKey touch / "
        "OTP paste) from the designated Notion section. Call for every "
        "Yubisneeze undo request."
    ),
    docstring="Return Yubisneeze undo steps from Notion when available.",
    query_doc=None,
    default_query="undo yubisneeze turn off otp",
    instruction=(
        "Help them undo the Yubisneeze / turn off accidental OTP using only "
        "source_content. If their message was a long modhex OTP paste, briefly "
        "acknowledge the sneeze without repeating the full string. Keep it short "
        "and Slack-friendly. Always share source_url. Do not invent recovery, "
        "password-reset, YubiKey Manager, or security steps that are not on the "
        "page."
    ),
    failure_instruction=(
        "Share source_url (the Yubisneeze section) and ask them to follow the "
        "undo steps there. Do not invent steps."
    ),
    char_limit=5000,
)
