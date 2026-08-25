"""Fetch Rasa Using AI Tools guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.notion_page_tool import notion_page_tool  # noqa: E402

get_ai_tools_guidance = notion_page_tool(
    name="get_ai_tools_guidance",
    source="ai_tools",
    description=(
        "Fetch Rasa's Using AI Tools at Rasa page from Notion. Call for "
        "which AI tools are allowed, ChatGPT/Claude/Copilot/Gemini rules, "
        "or generative-AI workplace guidance."
    ),
    docstring="Return live AI tools guidance for employee questions.",
    query_doc="Topic (e.g. ChatGPT, approved tools, customer data, Copilot).",
    instruction=(
        "Answer the AI-tools question using only source_content. Keep it short "
        "and Slack-friendly. Use exact allowed-"
        "tool and usage rules from the page - never invent them. Always share "
        "source_url. If content_truncated is true and the answer is not here, "
        "check other_sections and say what you could not confirm. If the answer "
        "is not on the page, say so and point to source_url."
    ),
    failure_instruction=(
        "Share source_url and ask them to check Using AI Tools at Rasa there. "
        "Do not invent which tools are allowed or how data may be used."
    ),
)
