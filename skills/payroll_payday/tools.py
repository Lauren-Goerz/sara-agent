"""Estimate days until the next Rasa payday from location / pay setup."""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import holidays
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import user_location

# Pay setups Sara can compute.
_MONTHLY_26 = frozenset({"germany", "serbia", "france", "uk"})
_SEMI_MONTHLY = frozenset({"us", "deel_semimonthly"})
_MONTH_END = frozenset({"deel_month_end"})

_GEO_LABELS = {
    "germany": "Germany",
    "serbia": "Serbia",
    "france": "France",
    "uk": "the UK",
    "us": "the US",
    "deel_semimonthly": "Deel (twice a month)",
    "deel_month_end": "Deel (last day of the month)",
}

# Deel schedules are pay setups, not countries, so they stay local to payday.
# Countries come from lib/user_location.py.
_DEEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("deel_semimonthly", re.compile(r"\bdeel\b.*\b(twice|semi|bi[-\s]?month|15th)\b|\b(twice|semi).*\bdeel\b", re.I)),
    ("deel_month_end", re.compile(r"\bdeel\b.*\b(last|end of month|month[-\s]?end)\b|\b(last day).*\bdeel\b", re.I)),
    ("deel", re.compile(r"\bdeel\b", re.I)),
]

_GEO_TZ = {
    "germany": "Europe/Berlin",
    "serbia": "Europe/Belgrade",
    "france": "Europe/Paris",
    "uk": "Europe/London",
    "us": "America/New_York",
    "deel_semimonthly": "UTC",
    "deel_month_end": "UTC",
}

_GEO_HOLIDAY_COUNTRY = {
    "germany": "DE",
    "serbia": "RS",
    "france": "FR",
    "uk": "GB",
    "us": "US",
}


def _deel_from_text(value: str | None) -> str | None:
    if not value:
        return None
    for setup, pattern in _DEEL_PATTERNS:
        if pattern.search(value):
            return setup
    return None


def _today_for(geo: str | None) -> date:
    tz_name = _GEO_TZ.get(geo or "", "UTC")
    try:
        return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:  # noqa: BLE001
        return date.today()


def _holiday_set(geo: str, year: int):
    code = _GEO_HOLIDAY_COUNTRY.get(geo)
    if not code:
        return {}
    try:
        return holidays.country_holidays(code, years=[year, year + 1])
    except NotImplementedError:
        return {}


def _is_non_banking_day(day: date, geo: str) -> bool:
    if day.weekday() >= 5:
        return True
    cal = _holiday_set(geo, day.year)
    return day in cal


def _adjust_pay_day(day: date, geo: str) -> date:
    """Move off weekends/public holidays onto a nearby banking day.

    Common payroll practice is the previous banking day; Rasa may still shift
    a bit earlier or later, so callers should treat this as an estimate.
    """
    adjusted = day
    # Prefer previous banking day when 26th / anchor falls badly.
    while _is_non_banking_day(adjusted, geo) and adjusted.day > 1:
        adjusted -= timedelta(days=1)
    # If we somehow hit the 1st still blocked, nudge forward instead.
    guard = 0
    while _is_non_banking_day(adjusted, geo) and guard < 7:
        adjusted += timedelta(days=1)
        guard += 1
    return adjusted


def _add_months(day: date, months: int) -> date:
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last))


def _month_day(year: int, month: int, day: int) -> date:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def _last_day_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _next_from_candidates(today: date, candidates: list[date]) -> date:
    future = sorted(d for d in candidates if d >= today)
    if future:
        return future[0]
    raise RuntimeError("no payday candidates")


def _next_monthly_26(today: date, geo: str) -> tuple[date, date]:
    """Return (estimated_pay_day, nominal_26th)."""
    candidates: list[tuple[date, date]] = []
    for month_offset in range(0, 3):
        anchor_month = _add_months(date(today.year, today.month, 1), month_offset)
        nominal = _month_day(anchor_month.year, anchor_month.month, 26)
        estimated = _adjust_pay_day(nominal, geo)
        candidates.append((estimated, nominal))
    for estimated, nominal in candidates:
        if estimated >= today:
            return estimated, nominal
    estimated, nominal = candidates[-1]
    return estimated, nominal


def _next_semimonthly(today: date, geo: str) -> tuple[date, str]:
    """Mid-month (~15) and month-end, adjusted off weekends/holidays."""
    options: list[tuple[date, str]] = []
    for month_offset in range(0, 3):
        base = _add_months(date(today.year, today.month, 1), month_offset)
        mid_nominal = _month_day(base.year, base.month, 15)
        end_nominal = _last_day_of_month(base.year, base.month)
        options.append((_adjust_pay_day(mid_nominal, geo), "mid-month (~15th)"))
        options.append((_adjust_pay_day(end_nominal, geo), "month-end"))
    for pay_day, label in options:
        if pay_day >= today:
            return pay_day, label
    return options[-1]


def _next_month_end(today: date, geo: str) -> date:
    for month_offset in range(0, 3):
        base = _add_months(date(today.year, today.month, 1), month_offset)
        pay_day = _adjust_pay_day(_last_day_of_month(base.year, base.month), geo)
        if pay_day >= today:
            return pay_day
    base = _add_months(date(today.year, today.month, 1), 2)
    return _adjust_pay_day(_last_day_of_month(base.year, base.month), geo)


@tool(
    description=(
        "Estimate how many days until the next Rasa payday from the employee's "
        "location or pay setup. Uses Slack location/timezone when available. "
        "Pass location_override or pay_setup when the user states Germany, "
        "Serbia, France, UK, US, or Deel."
    )
)
async def get_days_until_payday(
    location_override: str = "",
    pay_setup: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Compute days until the next estimated payday.

    Args:
        location_override: Country or setup the user stated (Germany, US, Deel…).
        pay_setup: Optional explicit setup: germany, serbia, france, uk, us,
            deel_semimonthly, or deel_month_end.
    """
    override = (location_override or "").strip()
    explicit = (pay_setup or "").strip().lower().replace(" ", "_").replace("-", "_")
    if explicit in {"deel_twice", "deel_semi", "deel_semimonthly", "deel_biweekly"}:
        explicit = "deel_semimonthly"
    if explicit in {"deel_eom", "deel_last", "deel_month_end", "deel_end"}:
        explicit = "deel_month_end"

    timezone: str | None = None
    profile_location: str | None = None
    location_source: str | None = None
    geo: str | None = None

    if explicit in _GEO_LABELS:
        geo = explicit
        location_source = "user_pay_setup"
    elif override:
        geo = _deel_from_text(override)
        location_source = "user_override" if geo else None

    if geo is None and context is not None:
        location = await user_location.resolve(
            context,
            location_override=override or None,
        )
        geo = location["country"]
        timezone = location["timezone"]
        profile_location = location["profile_location"]
        location_source = location["location_source"]

    # Bare "deel" needs a schedule choice.
    if geo == "deel":
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "deel_schedule_needed",
                "ask_for_deel_schedule": True,
                "message": (
                    "Deel pay can be twice a month or on the last day of the "
                    "month. Ask which one applies, then call again with "
                    "pay_setup=deel_semimonthly or pay_setup=deel_month_end."
                ),
                "instruction": (
                    "Ask whether they are paid twice a month on Deel, or on "
                    "the last day of the month. Then call this tool again."
                ),
            }
        )

    if geo is None:
        if context is not None:
            await user_location.send_country_picker(
                context,
                "Which country are you employed in, or are you paid through Deel?",
                options=user_location.PAYDAY_COUNTRY_OPTIONS,
            )
        return ToolResult()

    today = _today_for(geo if geo in _GEO_TZ else "us")
    rule_summary = ""
    next_payday: date
    nominal_note: str | None = None
    schedule_label = _GEO_LABELS.get(geo, geo)

    if geo in _MONTHLY_26:
        next_payday, nominal = _next_monthly_26(today, geo)
        rule_summary = (
            f"For {schedule_label}, payday is around the 26th. If the 26th "
            "falls on a weekend or public holiday, it may be a bit earlier "
            "or later."
        )
        if next_payday != nominal:
            nominal_note = (
                f"Nominal anchor is {nominal.isoformat()}; estimated banking "
                f"day used for the countdown is {next_payday.isoformat()}."
            )
    elif geo in _SEMI_MONTHLY:
        holiday_geo = "us" if geo.startswith("deel") else geo
        next_payday, bucket = _next_semimonthly(today, holiday_geo)
        rule_summary = (
            f"For {schedule_label}, pay is twice a month (mid-month and end "
            "of month). Weekend/holiday shifts can move the exact day a bit."
        )
        nominal_note = f"Next estimated slot: {bucket}."
    elif geo in _MONTH_END:
        next_payday = _next_month_end(today, "us")
        rule_summary = (
            f"For {schedule_label}, pay is on the last day of the month "
            "(shifted slightly if that day is a weekend/holiday)."
        )
    else:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unsupported_setup",
                "message": f"No payday rule configured for '{geo}'.",
                "instruction": (
                    "Ask them to confirm Germany/Serbia/France/UK, US, or Deel."
                ),
            }
        )

    days = (next_payday - today).days
    if days == 0:
        days_phrase = "today"
    elif days == 1:
        days_phrase = "1 day"
    else:
        days_phrase = f"{days} days"

    return ToolResult(
        llm_response={
            "ok": True,
            "today": today.isoformat(),
            "pay_setup": geo,
            "schedule_label": schedule_label,
            "location_source": location_source,
            "profile_location": profile_location,
            "timezone": timezone,
            "next_payday_estimate": next_payday.isoformat(),
            "days_until_payday": days,
            "days_phrase": days_phrase,
            "rule_summary": rule_summary,
            "nominal_note": nominal_note,
            "is_estimate": True,
            "instruction": (
                "Tell them how many days until payday using days_phrase and "
                "next_payday_estimate. Include rule_summary briefly. Make "
                "clear this is an estimate (weekend/holiday shifts happen). "
                "If location_source is slack_profile or slack_timezone, "
                "mention you used their Slack location/timezone. Keep it "
                "short and Slack-friendly."
            ),
        }
    )
