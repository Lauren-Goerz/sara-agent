"""Slack input channel with env secrets + thread follow-ups without @mention.

Maestro beta ``rasa train`` cannot parse ``${ENV_VAR}`` inside
``integrations.yml``, so secrets are read from ``.env`` at runtime.

Behaviour:
  - DMs always work (no @mention needed).
  - Channel: first message must @mention Sara; replies go in a thread.
  - Further messages in that same thread are accepted without another @mention,
    until someone @mentions another person and does not @mention Sara - then
    she drops out of the thread (quiet until tagged again).
  - Channels listed in ``SLACK_ALWAYS_REPLY_CHANNELS`` (comma-separated IDs)
    accept every message without an @mention (Sara must still be a member of
    the channel, and the Slack app must subscribe to ``message.channels`` /
    ``message.groups`` with ``channels:history`` / ``groups:history``).
  - Ignore IDs in ``SLACK_IGNORE_BOT_IDS`` (plus Sara herself).
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

import json
import os
import re
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Text, Set

import httpx
import structlog
from rasa.core.channels.channel import UserMessage
from rasa.core.channels.slack import SlackBot, SlackInput
from rasa.shared.exceptions import InvalidConfigException
from sanic.request import Request
from slack_sdk.web.async_client import AsyncWebClient

from lib.media_vision import describe_slack_media, media_from_slack_event
from lib.slack_audio import audio_from_slack_event, transcribe_slack_audio

structlogger = structlog.get_logger()

# Remember threads Sara was invited into so follow-ups don't need @mention.
# Key: "channel_id:thread_ts" → last activity epoch seconds.
_ACTIVE_THREADS: Dict[str, float] = {}
_THREAD_TTL_SECONDS = 60 * 60 * 24  # 24 hours

# Slack user / bot-user mentions look like <@U123> or <@W123>.
_USER_MENTION_RE = re.compile(r"<@([UW][A-Z0-9]+)>")

# Last human sender per conversation, so app-posted GIFs (which carry no user
# id) continue the same tracker instead of opening a new one.
_LAST_HUMAN_SENDER: Dict[str, str] = {}

# Sara's own bot identity, resolved once. Used to ignore her own uploads
# (e.g. Phosphor icons) so she never reacts to herself.
_OWN_BOT_IDS: Optional[set[str]] = None

# Tools append this readable line when Slack should render country buttons.
# Other channels show it as a normal plain-text list of choices.
_COUNTRY_OPTIONS_RE = re.compile(
    r"(?:\n\s*)?\[Country options:\s*([^\]\n]+)\]\s*$",
    re.IGNORECASE,
)
_COUNTRY_ACTION_ID = "sara_country_picker"
_COUNTRY_VALUES = {
    "germany": "My employment country is Germany",
    "uk": "My employment country is the UK",
    "serbia": "My employment country is Serbia",
    "france": "My employment country is France",
    "us": "My employment country is the US",
    "india": "My employment country is India",
    "deel": "I am employed through Deel",
    "other": "My employment country is another country",
}


def _always_reply_channels() -> set[str]:
    """Channel IDs where Sara answers every message (no @mention required)."""
    raw = os.environ.get("SLACK_ALWAYS_REPLY_CHANNELS", "").strip()
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def _ignored_bot_ids() -> set[str]:
    """Extra bot/user IDs to ignore (e.g. Wrangle), plus Sara's own ids."""
    ids = set(_own_bot_ids())
    raw = os.environ.get("SLACK_IGNORE_BOT_IDS", "").strip()
    if raw:
        ids.update(part.strip() for part in raw.split(",") if part.strip())
    return ids


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


def _forget_thread(channel_id: Optional[Text], thread_id: Optional[Text]) -> None:
    key = _thread_key(channel_id, thread_id)
    if key:
        _ACTIVE_THREADS.pop(key, None)


def _mentioned_user_ids(text: Optional[Text]) -> Set[str]:
    if not text:
        return set()
    return set(_USER_MENTION_RE.findall(text))


def _addresses_other_colleague(event: Dict[Text, Any]) -> bool:
    """True when the message @mentions someone else and does not @mention Sara.

    Used to drop Sara out of an open thread once the conversation clearly
    pivots to another person.
    """
    mentioned = _mentioned_user_ids(str(event.get("text") or ""))
    if not mentioned:
        return False

    sara_ids = _own_bot_ids()
    mentions_sara = bool(mentioned & sara_ids)
    mentions_others = bool(mentioned - sara_ids)
    return mentions_others and not mentions_sara


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


def _country_picker(text: str) -> tuple[str, list[dict[str, str]]] | None:
    """Parse a readable country-options suffix into Slack button data."""
    match = _COUNTRY_OPTIONS_RE.search(text or "")
    if not match:
        return None

    prompt = (text[: match.start()] or "Which country do you work in?").strip()
    buttons: list[dict[str, str]] = []
    for raw_label in match.group(1).split("|"):
        label = raw_label.strip()
        value = _COUNTRY_VALUES.get(label.lower())
        if label and value:
            buttons.append({"label": label, "value": value})
    return (prompt, buttons) if buttons else None


def _interactive_payload(request: Request) -> dict[str, Any] | None:
    """Return a URL-encoded Slack interaction payload, when present."""
    content_type = str(request.headers.get("content-type") or "").split(";", 1)[0]
    if content_type != "application/x-www-form-urlencoded":
        return None
    raw = request.form.get("payload")
    if not isinstance(raw, str):
        try:
            raw = raw[0]
        except (IndexError, TypeError):
            return None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


class CombinedSlackBot(SlackBot):
    """Slack output that keeps paragraphs in a single chat.postMessage."""

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        recipient = self.slack_channel or recipient_id
        body = (text or "").strip()
        if not body:
            return
        if getattr(self, "_country_picker_sent", False):
            structlogger.info("slack_channel.country_picker_duplicate_suppressed")
            return

        picker = _country_picker(body)
        if picker:
            self._country_picker_sent = True
            prompt, buttons = picker
            fallback = f"{prompt}\nOptions: {', '.join(b['label'] for b in buttons)}"
            blocks: list[dict[str, Any]] = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": prompt},
                }
            ]
            for start in range(0, len(buttons), 5):
                blocks.append(
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "action_id": (
                                    f"{_COUNTRY_ACTION_ID}_{start + offset}"
                                ),
                                "text": {
                                    "type": "plain_text",
                                    "text": button["label"],
                                    "emoji": True,
                                },
                                "value": button["value"],
                            }
                            for offset, button in enumerate(buttons[start : start + 5])
                        ],
                    }
                )
            await self._post_message(
                channel=recipient,
                as_user=True,
                text=fallback,
                blocks=blocks,
            )
            return

        await self._post_message(
            channel=recipient, as_user=True, text=body, type="mrkdwn"
        )

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: list,
        **kwargs: Any,
    ) -> None:
        """Post Mantle/response buttons; Slack allows 5 per actions row."""
        recipient = self.slack_channel or recipient_id
        body = (text or "").strip() or "Choose an option:"
        if not buttons:
            await self.send_text_message(recipient, body, **kwargs)
            return

        blocks: list[dict[str, Any]] = [
            {"type": "section", "text": {"type": "mrkdwn", "text": body}}
        ]
        for start in range(0, len(buttons), 5):
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": str(button.get("title") or "")[:75],
                                "emoji": True,
                            },
                            "value": str(button.get("payload") or button.get("title") or ""),
                        }
                        for button in buttons[start : start + 5]
                    ],
                }
            )
        fallback = f"{body}\nOptions: {', '.join(str(b.get('title') or '') for b in buttons)}"
        await self._post_message(
            channel=recipient,
            as_user=True,
            text=fallback,
            blocks=blocks,
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
        """Accept DMs, @mentions, open threads, and always-reply channels."""
        if self._is_direct_message(slack_event):
            return True

        channel_id = metadata.get("out_channel")
        thread_id = metadata.get("thread_id")
        event = slack_event.get("event") or {}

        # A reply addressed to another person is not for Sara, even in an
        # always-reply channel or a thread where Sara was previously active.
        # Check this before every acceptance path so the always-reply fallback
        # cannot pull her back into the conversation.
        parent_ts = event.get("thread_ts")
        if parent_ts and _addresses_other_colleague(event):
            _forget_thread(channel_id, parent_ts)
            structlogger.info(
                "slack_channel.left_thread_for_colleague",
                channel_id=channel_id,
                thread_ts=parent_ts,
                mentioned=_mentioned_user_ids(str(event.get("text") or "")),
            )
            return False

        if self._is_app_mention(slack_event):
            # Opening @mention becomes the thread parent (ts) when use_threads=True.
            _remember_thread(channel_id, thread_id)
            return True

        # Follow-up in an existing thread — no @mention required.
        # Real replies always include thread_ts; the parent mention does not.
        if event.get("thread_ts") and _is_active_thread(channel_id, event.get("thread_ts")):
            parent_ts = event.get("thread_ts")
            _remember_thread(channel_id, parent_ts)
            return True

        # Dedicated always-reply channels (env allowlist) — no @mention needed.
        if channel_id and str(channel_id) in _always_reply_channels():
            parent = event.get("thread_ts") or thread_id or event.get("ts")
            _remember_thread(channel_id, parent)
            structlogger.info(
                "slack_channel.always_reply_channel",
                channel_id=channel_id,
            )
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
        message_ts = None
        thread_ts = None
        channel_id = None
        if content_type == "application/json":
            event = (request.json or {}).get("event") or {}
            slack_user_id = event.get("user")
            media = media_from_slack_event(event)
            message_ts = event.get("ts")
            thread_ts = event.get("thread_ts")
            channel_id = event.get("channel")
        metadata = dict(metadata or {})
        if slack_user_id:
            metadata["slack_user_id"] = slack_user_id
        if message_ts:
            metadata["message_ts"] = str(message_ts)
        if thread_ts:
            metadata["thread_ts"] = str(thread_ts)
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
            # otherwise every upload would trigger another turn. Also ignore
            # allowlisted bots such as Wrangle.
            ignored = _ignored_bot_ids()
            if bot_id in ignored or str(event.get("user") or "") in ignored:
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

        # Human sender that matches an ignore list (rare; Wrangle may appear
        # as a user id in some workspaces).
        user_id = str(event.get("user") or "")
        if user_id and user_id in _ignored_bot_ids():
            return False

        subtype = event.get("subtype")
        # file_share is how Slack delivers many GIF/image/voice uploads.
        if subtype and subtype not in {"file_share", "file_mention"}:
            return False

        # Remember the human so app-posted GIFs can reuse this conversation.
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
        payload = _interactive_payload(request)
        if payload:
            actions = payload.get("actions") or []
            action = actions[0] if actions and isinstance(actions[0], dict) else {}
            if str(action.get("action_id") or "").startswith(_COUNTRY_ACTION_ID):
                channel_id = (payload.get("channel") or {}).get("id")
                message = payload.get("message") or {}
                message_ts = message.get("ts")
                selected = ((action.get("text") or {}).get("text") or "").strip()
                if channel_id and message_ts and selected:
                    original = str(message.get("text") or "").split("\nOptions:", 1)[0]
                    updated_text = f"{original}\nSelected: {selected}".strip()
                    try:
                        client = AsyncWebClient(self.slack_token, proxy=self.proxy)
                        await client.chat_update(
                            channel=channel_id,
                            ts=message_ts,
                            text=updated_text,
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"{original}\n*Selected:* {selected}",
                                    },
                                }
                            ],
                        )
                    except Exception as error:  # noqa: BLE001 - click still proceeds
                        structlogger.warning(
                            "slack_channel.country_picker_cleanup_failed",
                            error=str(error),
                            channel_id=channel_id,
                        )

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
