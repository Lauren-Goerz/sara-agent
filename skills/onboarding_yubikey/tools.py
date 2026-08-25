"""Fetch YubiKey setup guidance from the designated Notion onboarding page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_yubikey_setup_guidance = notion_page_tool(
    name="get_yubikey_setup_guidance",
    source="yubikey",
    description=(
        "Fetch Rasa YubiKey installation and Google phone security setup "
        "guidance from the designated Notion onboarding page. Call for every "
        "YubiKey / security-key install request."
    ),
    docstring="Return live YubiKey setup guidance from Notion.",
    query_doc=None,
    default_query="install setup security key",
    instruction=(
        "Walk the person through YubiKey installation using only source_content. "
        "Keep it short and Slack-friendly. Prefer numbered steps that match the "
        "page. Always share source_url. Do not invent PIN, Google, Slack, or "
        "hardware steps that are not on the page."
    ),
    failure_instruction=(
        "Share source_url and ask them to follow the install steps there. Do not "
        "invent YubiKey setup steps."
    ),
    char_limit=8000,
)
