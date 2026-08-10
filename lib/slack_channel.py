"""Slack input channel with env secrets + thread follow-ups without @mention.

Maestro beta ``rasa train`` cannot parse ``${ENV_VAR}`` inside
``integrations.yml``, so secrets are read from ``.env`` at runtime.

Behaviour:
  - DMs always work (no @mention needed).
  - Channel: first message must @mention Sara; replies go in a thread.
  - Further messages in that same thread are accepted without another @mention.
  - Conversation state is scoped per Slack thread (and per DM channel).
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Text

from rasa.core.channels.slack import SlackInput
from rasa.shared.exceptions import InvalidConfigException

# Remember threads Sara was invited into so follow-ups don't need @mention.
# Key: "channel_id:thread_ts" → last activity epoch seconds.
_ACTIVE_THREADS: Dict[str, float] = {}
_THREAD_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def _thread_key(channel_id: Optional[Text], thread_id: Optional[Text]) -> Optional[Text]:
    if not channel_id or not thread_id:
        return None
    return f"{channel_id}:{thread_id}"


def _remember_thread(channel_id: Optional[Text], thread_id: Optional[Text]) -> None:
    key = _thread_key(channel_id, thread_id)
    if key:
        _ACTIVE_THREADS[key] = time.time()
        _prune_threads()


def _is_active_thread(channel_id: Optional[Text], thread_id: Optional[Text]) -> bool:
    key = _thread_key(channel_id, thread_id)
    if not key:
        return False
    last = _ACTIVE_THREADS.get(key)
    if last is None:
        return False
    if time.time() - last > _THREAD_TTL_SECONDS:
        _ACTIVE_THREADS.pop(key, None)
        return False
    _ACTIVE_THREADS[key] = time.time()
    return True


def _prune_threads() -> None:
    cutoff = time.time() - _THREAD_TTL_SECONDS
    stale = [k for k, ts in _ACTIVE_THREADS.items() if ts < cutoff]
    for k in stale:
        _ACTIVE_THREADS.pop(k, None)


class EnvSlackInput(SlackInput):
    """SlackInput that loads secrets from env and continues open threads."""

    @classmethod
    def name(cls) -> Text:
        # Keep the public webhook path as /webhooks/slack/webhook
        return "slack"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> "EnvSlackInput":
        creds = dict(credentials or {})

        token = (
            creds.pop("slack_token", None)
            or os.environ.get("SLACK_BOT_TOKEN", "")
        ).strip()
        signing_secret = (
            creds.pop("slack_signing_secret", None)
            or os.environ.get("SLACK_SIGNING_SECRET", "")
        ).strip()

        if not token or token == "xoxb-REPLACE_ME" or "REPLACE" in token:
            raise InvalidConfigException(
                "SLACK_BOT_TOKEN is missing. Set it in .env (Bot User OAuth Token)."
            )
        if (
            not signing_secret
            or signing_secret == "REPLACE_ME"
            or "REPLACE" in signing_secret
        ):
            raise InvalidConfigException(
                "SLACK_SIGNING_SECRET is missing. Set it in .env "
                "(Slack App → Basic Information → Signing Secret)."
            )

        # Defaults for threaded Slack conversations (caller may override).
        creds.setdefault("use_threads", True)
        creds.setdefault("conversation_granularity", "thread")
        creds["slack_token"] = token
        creds["slack_signing_secret"] = signing_secret
        return super().from_credentials(creds)

    def _get_conversation_id(
        self,
        sender_id: Optional[Text],
        channel_id: Optional[Text],
        thread_id: Optional[Text],
    ) -> Optional[Text]:
        """One tracker per DM; one tracker per channel thread."""
        if not sender_id:
            return sender_id

        # Slack DM channels start with D — keep a continuous DM conversation.
        if channel_id and str(channel_id).startswith("D"):
            return f"{sender_id}_{channel_id}"

        if channel_id and thread_id:
            return f"{sender_id}_{channel_id}_{thread_id}"

        if channel_id:
            return f"{sender_id}_{channel_id}"

        return sender_id

    def _is_supported_channel(self, slack_event: Dict, metadata: Dict) -> bool:
        """Accept DMs, @mentions, and follow-ups in threads Sara already joined."""
        if self._is_direct_message(slack_event):
            return True

        channel_id = metadata.get("out_channel")
        thread_id = metadata.get("thread_id")
        event = slack_event.get("event") or {}

        if self._is_app_mention(slack_event):
            # Opening @mention becomes the thread parent (ts) when use_threads=True.
            _remember_thread(channel_id, thread_id)
            return True

        # Follow-up in an existing thread — no @mention required.
        # Real replies always include thread_ts; the parent mention does not.
        if event.get("thread_ts") and _is_active_thread(channel_id, event.get("thread_ts")):
            _remember_thread(channel_id, event.get("thread_ts"))
            return True

        if metadata.get("out_channel") == self.slack_channel and self.slack_channel:
            return True

        return False
