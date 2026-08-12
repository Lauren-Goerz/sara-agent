"""Slack input channel with env secrets + thread follow-ups without @mention.

Maestro beta ``rasa train`` cannot parse ``${ENV_VAR}`` inside
``integrations.yml``, so secrets are read from ``.env`` at runtime.

Behaviour:
  - DMs always work (no @mention needed).
  - Channel: first message must @mention Sara; replies go in a thread.
  - Further messages in that same thread are accepted without another @mention.
  - Conversation state is scoped per Slack thread (and per DM channel).
  - Outgoing text is posted as one Slack message (stock Rasa splits on blank
    lines into multiple bubbles).
  - GIFs/images are accepted even with empty text; a short vision description
    is injected so Maestro (text-only) can react. This includes app-posted
    GIFs (``/giphy``), which Slack delivers as bot messages with no user id.
  - Slack voice messages / audio files are transcribed with Deepgram
    (``DEEPGRAM_API_KEY``) and injected as the user text.
"""

from __future__ import annotations

import os
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Text

import httpx
import structlog
from rasa.core.channels.channel import UserMessage
from rasa.core.channels.slack import SlackBot, SlackInput
from rasa.shared.exceptions import InvalidConfigException
from sanic.request import Request

from lib.media_vision import describe_slack_media, media_from_slack_event
from lib.slack_audio import audio_from_slack_event, transcribe_slack_audio

structlogger = structlog.get_logger()

# Remember threads Sara was invited into so follow-ups don't need @mention.
# Key: "channel_id:thread_ts" → last activity epoch seconds.
_ACTIVE_THREADS: Dict[str, float] = {}
_THREAD_TTL_SECONDS = 60 * 60 * 24  # 24 hours

# Last human sender per conversation, so app-posted GIFs (which carry no user
# id) continue the same tracker instead of opening a new one.
_LAST_HUMAN_SENDER: Dict[str, str] = {}

# Sara's own bot identity, resolved once. Used to ignore her own uploads
# (e.g. Phosphor icons) so she never reacts to herself.
_OWN_BOT_IDS: Optional[set[str]] = None


def _own_bot_ids() -> set[str]:
    global _OWN_BOT_IDS
    if _OWN_BOT_IDS is not None:
        return _OWN_BOT_IDS

    ids: set[str] = set()
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if token:
        try:
            response = httpx.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            data = response.json()
            if data.get("ok"):
                for key in ("bot_id", "user_id"):
                    value = data.get(key)
                    if value:
                        ids.add(str(value))
        except Exception as error:  # noqa: BLE001 - identity is best effort
            structlogger.warning("slack_channel.auth_test_failed", error=str(error))

    _OWN_BOT_IDS = ids
    return ids


def _sender_key(channel_id: Optional[Text], thread_id: Optional[Text]) -> Optional[Text]:
    if not channel_id:
        return None
    return f"{channel_id}:{thread_id}" if thread_id else str(channel_id)


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


class CombinedSlackBot(SlackBot):
    """Slack output that keeps paragraphs in a single chat.postMessage."""

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        recipient = self.slack_channel or recipient_id
        body = (text or "").strip()
        if not body:
            return
        await self._post_message(
            channel=recipient, as_user=True, text=body, type="mrkdwn"
        )


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

    def get_output_channel(
        self,
        channel: Optional[Text] = None,
        thread_id: Optional[Text] = None,
    ) -> CombinedSlackBot:
        return CombinedSlackBot(self.slack_token, channel, thread_id, self.proxy)

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

    def get_metadata(self, request):  # type: ignore[no-untyped-def]
        """Include the Slack message author for per-user personalization."""
        metadata = super().get_metadata(request)
        content_type = request.headers.get("content-type")
        slack_user_id = None
        media: list[dict[str, Any]] = []
        if content_type == "application/json":
            event = (request.json or {}).get("event") or {}
            slack_user_id = event.get("user")
            media = media_from_slack_event(event)
        metadata = dict(metadata or {})
        if slack_user_id:
            metadata["slack_user_id"] = slack_user_id
        if media:
            metadata["media"] = [
                {"kind": item.get("kind"), "name": item.get("name")}
                for item in media
            ]
        return metadata

    def _is_user_message(self, slack_event: Dict[Text, Any]) -> bool:
        """Accept text, images/GIFs, voice notes, and app-posted GIFs."""
        event = slack_event.get("event") or {}
        if not event:
            return False

        event_type = event.get("type")
        if event_type not in {"message", "app_mention"}:
            return False

        media = media_from_slack_event(event)
        audio = audio_from_slack_event(event)
        bot_id = str(event.get("bot_id") or "")

        if bot_id:
            # Never react to Sara's own posts (e.g. Phosphor icon uploads),
            # otherwise every upload would trigger another turn.
            own = _own_bot_ids()
            if bot_id in own or str(event.get("user") or "") in own:
                return False
            # /giphy and similar apps post the GIF on the user's behalf.
            if media:
                structlogger.info(
                    "slack_channel.app_media_message",
                    bot_id=bot_id,
                    media_count=len(media),
                )
                return True
            return False

        subtype = event.get("subtype")
        # file_share is how Slack delivers many GIF/image/voice uploads.
        if subtype and subtype not in {"file_share", "file_mention"}:
            return False

        # Remember the human so app-posted GIFs can reuse this conversation.
        user_id = str(event.get("user") or "")
        if user_id:
            key = _sender_key(event.get("channel"), event.get("thread_ts"))
            if key:
                _LAST_HUMAN_SENDER[key] = user_id
            channel_key = _sender_key(event.get("channel"), None)
            if channel_key:
                _LAST_HUMAN_SENDER[channel_key] = user_id

        if event.get("text"):
            return True
        return bool(media or audio)

    def _event_user_id(self, event: Dict[Text, Any]) -> Text:
        """Fall back to the last human sender for app-posted messages."""
        user = event.get("user", "")
        if isinstance(user, dict):
            user = user.get("id", "") or ""
        if isinstance(user, str) and user:
            return user

        for key in (
            _sender_key(event.get("channel"), event.get("thread_ts")),
            _sender_key(event.get("channel"), None),
        ):
            if key and key in _LAST_HUMAN_SENDER:
                return _LAST_HUMAN_SENDER[key]

        # No known human: fall back to the channel so the turn still runs.
        channel = str(event.get("channel") or "")
        return f"slack_app_{channel}" if channel else ""

    async def process_message(
        self,
        request: Request,
        on_new_message: Callable[[UserMessage], Awaitable[Any]],
        text: Text,
        sender_id: Optional[Text],
        metadata: Optional[Dict],
    ) -> Any:
        """Transcribe voice + describe GIFs/images for Maestro (text-only)."""
        event: Dict[str, Any] = {}
        if request.headers.get("content-type") == "application/json":
            event = (request.json or {}).get("event") or {}

        media = media_from_slack_event(event)
        audio = audio_from_slack_event(event)
        enriched = (text or "").strip()

        if audio:
            structlogger.info(
                "slack_channel.audio_received",
                audio_count=len(audio),
                kinds=[item.get("kind") for item in audio],
            )
            transcripts: list[str] = []
            for item in audio[:1]:
                transcript = await transcribe_slack_audio(item)
                if transcript:
                    transcripts.append(transcript)
            structlogger.info(
                "slack_channel.audio_transcribed",
                transcribed=len(transcripts),
            )
            if transcripts:
                spoken = " ".join(transcripts).strip()
                enriched = f"{enriched}\n{spoken}".strip() if enriched else spoken
                metadata = dict(metadata or {})
                metadata["has_audio"] = True
                metadata["audio_transcript"] = spoken
            elif not enriched:
                enriched = (
                    "[User sent a voice message, but I could not transcribe "
                    "it. Ask them to type the request or try again.]"
                )
                metadata = dict(metadata or {})
                metadata["has_audio"] = True

        if media:
            structlogger.info(
                "slack_channel.media_received",
                media_count=len(media),
                kinds=[item.get("kind") for item in media],
            )
            descriptions: list[str] = []
            for item in media[:2]:
                description = await describe_slack_media(item)
                if description:
                    kind = item.get("kind") or "image"
                    descriptions.append(f"[User sent a {kind}: {description}]")
            structlogger.info(
                "slack_channel.media_described",
                described=len(descriptions),
            )
            if descriptions:
                media_note = " ".join(descriptions)
                enriched = (
                    f"{enriched}\n{media_note}".strip() if enriched else media_note
                )
            elif not enriched:
                enriched = (
                    "[User sent a GIF or image, but I could not view it. "
                    "React briefly and ask them to describe it if needed.]"
                )
            metadata = dict(metadata or {})
            metadata["has_media"] = True

        if not enriched:
            enriched = text or ""

        return await super().process_message(
            request,
            on_new_message,
            enriched,
            sender_id,
            metadata,
        )
