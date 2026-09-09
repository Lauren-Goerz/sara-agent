"""Shared work-country resolution for Sara's country-aware skills.

One resolver so sick leave, vacation policy, parental leave, payday, and
payslips all answer for the same country. Order of truth: what the user just said, then what
was already established this conversation, then the Slack profile Location
field, then the Slack timezone.
"""

from __future__ import annotations

import re
from typing import Any

from lib import slack_client

# Declared in the project-level memory.yml.
MEMORY_COUNTRY = "user_country"
MEMORY_SOURCE = "user_country_source"
MEMORY_CONFIRMED = "user_country_confirmed"

# Countries with dedicated policy sections. India and "other" are recognized
# countries with none, which is different from not knowing the country at all.
SUPPORTED = ("germany", "uk", "serbia", "france", "us")

GEO_LABELS = {
    "germany": "Germany",
    "uk": "the UK",
    "serbia": "Serbia",
    "france": "France",
    "us": "the US",
    "india": "India",
}

STANDARD_COUNTRY_OPTIONS = (
    "Germany",
    "UK",
    "Serbia",
    "France",
    "US",
    "India",
    "Other",
)
LOCAL_POLICY_COUNTRY_OPTIONS = (
    "Germany",
    "UK",
    "Serbia",
    "France",
    "US",
    "Other",
)
PAYROLL_COUNTRY_OPTIONS = (
    "Germany",
    "UK",
    "Serbia",
    "France",
    "US",
    "Deel",
    "Other",
)
PAYDAY_COUNTRY_OPTIONS = (
    "Germany",
    "UK",
    "Serbia",
    "France",
    "US",
    "Deel",
)

SLACK_LOCATION_PREFACE = (
    "based on the location information you provided in your Slack profile..."
)

TIMEZONE_TO_GEO: dict[str, str] = {
    "Europe/Berlin": "germany",
    "Europe/Busingen": "germany",
    "Europe/London": "uk",
    "Europe/Belfast": "uk",
    "Europe/Guernsey": "uk",
    "Europe/Isle_of_Man": "uk",
    "Europe/Jersey": "uk",
    "Europe/Belgrade": "serbia",
    "Europe/Paris": "france",
    "Asia/Kolkata": "india",
    "Asia/Calcutta": "india",
    "America/New_York": "us",
    "America/Detroit": "us",
    "America/Kentucky/Louisville": "us",
    "America/Kentucky/Monticello": "us",
    "America/Indiana/Indianapolis": "us",
    "America/Indiana/Vincennes": "us",
    "America/Indiana/Winamac": "us",
    "America/Indiana/Marengo": "us",
    "America/Indiana/Petersburg": "us",
    "America/Indiana/Vevay": "us",
    "America/Chicago": "us",
    "America/Indiana/Tell_City": "us",
    "America/Indiana/Knox": "us",
    "America/Menominee": "us",
    "America/North_Dakota/Center": "us",
    "America/North_Dakota/New_Salem": "us",
    "America/North_Dakota/Beulah": "us",
    "America/Denver": "us",
    "America/Boise": "us",
    "America/Phoenix": "us",
    "America/Los_Angeles": "us",
    "America/Anchorage": "us",
    "America/Juneau": "us",
    "America/Sitka": "us",
    "America/Metlakatla": "us",
    "America/Yakutat": "us",
    "America/Nome": "us",
    "America/Adak": "us",
    "Pacific/Honolulu": "us",
}

COUNTRY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "germany",
        re.compile(
            r"\b(germany|german|deutschland|berlin|munich|m[uü]nchen|hamburg|"
            r"cologne|k[oö]ln|frankfurt|bavaria|bayern)\b",
            re.I,
        ),
    ),
    (
        "uk",
        re.compile(
            r"\b(uk|u\.k\.|united kingdom|britain|british|england|scotland|"
            r"wales|london|manchester|edinburgh)\b",
            re.I,
        ),
    ),
    (
        "serbia",
        re.compile(r"\b(serbia|serbian|serbien|belgrade|beograd)\b", re.I),
    ),
    (
        "france",
        re.compile(r"\b(france|french|paris|lyon|marseille)\b", re.I),
    ),
    (
        "us",
        re.compile(
            r"\b(usa|u\.s\.a\.|u\.s\.|united states|america|american|"
            r"san francisco|new york|nyc|seattle|austin|boston|california|"
            r"texas)\b",
            re.I,
        ),
    ),
    (
        "india",
        re.compile(
            r"\b(india|indian|bengaluru|bangalore|mumbai|delhi|"
            r"hyderabad|chennai|pune)\b",
            re.I,
        ),
    ),
]


def slack_user_id(context: Any) -> str | None:
    """Pull the Slack user id off the most recent event metadata."""
    for event in reversed(getattr(context, "events", []) or []):
        metadata = getattr(event, "metadata", None) or {}
        candidate = metadata.get("slack_user_id")
        if isinstance(candidate, str) and candidate.startswith("U"):
            return candidate
        for user in metadata.get("users") or []:
            if isinstance(user, str) and user.startswith("U"):
                return user
    return None


def from_text(value: str | None) -> str | None:
    """Map free text (a country, city, or Slack Location field) to a country."""
    if not value:
        return None
    for geography, pattern in COUNTRY_PATTERNS:
        if pattern.search(str(value)):
            return geography
    return None


def label(country: str | None) -> str | None:
    return GEO_LABELS.get(country or "")


async def send_country_picker(
    context: Any,
    prompt: str,
    *,
    options: tuple[str, ...] = STANDARD_COUNTRY_OPTIONS,
) -> None:
    """Send a readable choice list that Slack renders as Block Kit buttons."""
    if context is None:
        return
    choices = " | ".join(options)
    await context.send(f"{prompt.strip()}\n[Country options: {choices}]")


def _remembered(context: Any) -> tuple[str | None, str | None]:
    try:
        country = context.memory.get(MEMORY_COUNTRY)
        source = context.memory.get(MEMORY_SOURCE)
    except Exception:  # noqa: BLE001 - memory is optional, never block an answer
        return None, None
    country = str(country).strip().lower() if country else None
    return (country or None), (str(source) if source else None)


def confirm(context: Any, country: str) -> None:
    """Mark a country the employee stated out loud as confirmed."""
    _remember(context, country, "user_override", confirmed=True)


def _remember(
    context: Any,
    country: str,
    source: str,
    *,
    confirmed: bool | None = None,
) -> None:
    try:
        context.memory.set(MEMORY_COUNTRY, country)
        context.memory.set(MEMORY_SOURCE, source)
        if confirmed is True:
            context.memory.set(MEMORY_CONFIRMED, True)
        elif confirmed is False:
            context.memory.set(MEMORY_CONFIRMED, False)
    except Exception:  # noqa: BLE001 - remembering is best effort
        pass


async def resolve(
    context: Any,
    *,
    location_override: str | None = None,
    remember: bool = True,
    use_memory: bool = True,
) -> dict[str, Any]:
    """Resolve the employee's work country once, consistently.

    Args:
        context: The ToolContext of the calling tool.
        location_override: A country the user stated or corrected this turn.
        remember: Store the result so later skills reuse the same country.
        use_memory: Read a country established earlier in the conversation.
    """
    override = (location_override or "").strip() or None
    country: str | None = None
    source: str | None = None
    timezone: str | None = None
    profile_location: str | None = None

    if override:
        country = from_text(override)
        source = "user_override" if country else None

    if country is None and use_memory:
        remembered, remembered_source = _remembered(context)
        if remembered:
            country = remembered
            source = "memory"
            timezone = None
            profile_location = None
            if remembered_source:
                source = "memory"

    if country is None and context is not None:
        user_id = slack_user_id(context)
        if user_id and slack_client.configured():
            profile = await slack_client.get_user_location(user_id)
            timezone = profile.get("timezone")
            profile_location = profile.get("location")
            # Slack "My Location" is the employment geography; timezone is a
            # weaker fallback (people travel).
            if profile_location:
                country = from_text(str(profile_location))
                if country:
                    source = "slack_profile"
            if country is None and timezone:
                country = TIMEZONE_TO_GEO.get(str(timezone))
                if country:
                    source = "slack_timezone"

    read_from_slack_now = source in {"slack_profile", "slack_timezone"}
    if remember and country and source and source != "memory":
        _remember(
            context,
            country,
            source,
            confirmed=True if source == "user_override" else None,
        )

    return {
        "country": country,
        "country_label": label(country),
        "location_source": source,
        "timezone": timezone,
        "profile_location": profile_location,
        "inferred_from_slack": read_from_slack_now,
        # Say where the guess came from once, not in every later skill.
        "required_preface": (
            SLACK_LOCATION_PREFACE if read_from_slack_now else None
        ),
        "ask_for_location": country is None,
        "has_local_policy": country in SUPPORTED,
        "supported_countries": list(SUPPORTED),
    }
