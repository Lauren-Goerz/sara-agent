"""Slack channel listing and posting for the notify_slack skill (live API)."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import slack_client  # noqa: E402


@tool(description="List public Slack channels available for posting.")
async def list_slack_channels(context: ToolContext = None) -> ToolResult:
    """Return live Slack public channels (optionally allowlisted)."""
    try:
        channels = await slack_client.list_channels()
    except slack_client.SlackConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "hint": str(exc),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "slack_error",
                "hint": str(exc),
            }
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "channels": channels,
            "hint": (
                None
                if channels
                else (
                    "No channels visible. Invite the bot to channels and check "
                    "SLACK_ALLOWED_CHANNELS if set."
                )
            ),
        }
    )


@tool(
    description=(
        "Post a confirmed message to Slack. Requires post_confirmed, "
        "channel_id, and message_text in skill memory."
    )
)
async def post_slack_message(context: ToolContext = None) -> ToolResult:
    """Post via Slack chat.postMessage after user confirmation."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    if not context.memory.get("post_confirmed"):
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_confirmed",
                "hint": "Confirm channel and message with the user first.",
            }
        )

    channel_id = context.memory.get("channel_id")
    message_text = context.memory.get("message_text")
    if not channel_id or not message_text:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "missing_fields",
                "hint": "Set channel_id and message_text before posting.",
            }
        )

    try:
        channel = await slack_client.resolve_channel(str(channel_id))
        if channel is None:
            available = await slack_client.list_channels()
            return ToolResult(
                llm_response={
                    "ok": False,
                    "error": "unknown_channel",
                    "channel_id": channel_id,
                    "available": available,
                    "hint": "Pick a channel id or name from the available list.",
                }
            )

        result = await slack_client.post_message(channel["id"], str(message_text))
    except slack_client.SlackConfigError as exc:
        return ToolResult(
            llm_response={"ok": False, "error": "not_configured", "hint": str(exc)}
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "slack_http_error",
                "status_code": exc.response.status_code,
                "hint": "Check SLACK_BOT_TOKEN and bot channel membership.",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={"ok": False, "error": "slack_error", "hint": str(exc)}
        )

    if result.get("ts"):
        context.memory.set("last_message_ts", str(result["ts"]))

    return ToolResult(
        llm_response={
            "ok": True,
            "channel": result.get("channel"),
            "channel_name": channel["name"],
            "ts": result.get("ts"),
            "message": result.get("message"),
            "permalink": result.get("permalink"),
        }
    )
