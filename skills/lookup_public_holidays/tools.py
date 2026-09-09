"""Look up public holidays by country / region and date."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import holidays
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

# Free-text place → (ISO country, optional subdivision, timezone).
_PLACE_ALIASES: dict[str, tuple[str, str | None, str]] = {
    # Germany + states
    "germany": ("DE", None, "Europe/Berlin"),
    "deutschland": ("DE", None, "Europe/Berlin"),
    "de": ("DE", None, "Europe/Berlin"),
    "bayern": ("DE", "BY", "Europe/Berlin"),
    "bavaria": ("DE", "BY", "Europe/Berlin"),
    "by": ("DE", "BY", "Europe/Berlin"),
    "berlin": ("DE", "BE", "Europe/Berlin"),
    "hamburg": ("DE", "HH", "Europe/Berlin"),
    "hh": ("DE", "HH", "Europe/Berlin"),
    "hessen": ("DE", "HE", "Europe/Berlin"),
    "hesse": ("DE", "HE", "Europe/Berlin"),
    "nrw": ("DE", "NW", "Europe/Berlin"),
    "nordrhein-westfalen": ("DE", "NW", "Europe/Berlin"),
    "north rhine-westphalia": ("DE", "NW", "Europe/Berlin"),
    "nw": ("DE", "NW", "Europe/Berlin"),
    "baden-württemberg": ("DE", "BW", "Europe/Berlin"),
    "baden-wurttemberg": ("DE", "BW", "Europe/Berlin"),
    "bw": ("DE", "BW", "Europe/Berlin"),
    "sachsen": ("DE", "SN", "Europe/Berlin"),
    "saxony": ("DE", "SN", "Europe/Berlin"),
    "sn": ("DE", "SN", "Europe/Berlin"),
    "niedersachsen": ("DE", "NI", "Europe/Berlin"),
    "lower saxony": ("DE", "NI", "Europe/Berlin"),
    "ni": ("DE", "NI", "Europe/Berlin"),
    "rheinland-pfalz": ("DE", "RP", "Europe/Berlin"),
    "rhineland-palatinate": ("DE", "RP", "Europe/Berlin"),
    "rp": ("DE", "RP", "Europe/Berlin"),
    "schleswig-holstein": ("DE", "SH", "Europe/Berlin"),
    "sh": ("DE", "SH", "Europe/Berlin"),
    "saarland": ("DE", "SL", "Europe/Berlin"),
    "sl": ("DE", "SL", "Europe/Berlin"),
    "bremen": ("DE", "HB", "Europe/Berlin"),
    "hb": ("DE", "HB", "Europe/Berlin"),
    "mecklenburg-vorpommern": ("DE", "MV", "Europe/Berlin"),
    "mv": ("DE", "MV", "Europe/Berlin"),
    "sachsen-anhalt": ("DE", "ST", "Europe/Berlin"),
    "saxony-anhalt": ("DE", "ST", "Europe/Berlin"),
    "st": ("DE", "ST", "Europe/Berlin"),
    "thüringen": ("DE", "TH", "Europe/Berlin"),
    "thuringia": ("DE", "TH", "Europe/Berlin"),
    "th": ("DE", "TH", "Europe/Berlin"),
    "brandenburg": ("DE", "BB", "Europe/Berlin"),
    "bb": ("DE", "BB", "Europe/Berlin"),
    # Common countries
    "united states": ("US", None, "America/New_York"),
    "usa": ("US", None, "America/New_York"),
    "us": ("US", None, "America/New_York"),
    "united kingdom": ("GB", None, "Europe/London"),
    "uk": ("GB", None, "Europe/London"),
    "great britain": ("GB", None, "Europe/London"),
    "england": ("GB", "ENG", "Europe/London"),
    "scotland": ("GB", "SCT", "Europe/London"),
    "wales": ("GB", "WLS", "Europe/London"),
    "northern ireland": ("GB", "NIR", "Europe/London"),
    "france": ("FR", None, "Europe/Paris"),
    "fr": ("FR", None, "Europe/Paris"),
    "spain": ("ES", None, "Europe/Madrid"),
    "es": ("ES", None, "Europe/Madrid"),
    "italy": ("IT", None, "Europe/Rome"),
    "it": ("IT", None, "Europe/Rome"),
    "netherlands": ("NL", None, "Europe/Amsterdam"),
    "holland": ("NL", None, "Europe/Amsterdam"),
    "nl": ("NL", None, "Europe/Amsterdam"),
    "belgium": ("BE", None, "Europe/Brussels"),
    "austria": ("AT", None, "Europe/Vienna"),
    "at": ("AT", None, "Europe/Vienna"),
    "switzerland": ("CH", None, "Europe/Zurich"),
    "ch": ("CH", None, "Europe/Zurich"),
    "denmark": ("DK", None, "Europe/Copenhagen"),
    "dk": ("DK", None, "Europe/Copenhagen"),
    "sweden": ("SE", None, "Europe/Stockholm"),
    "se": ("SE", None, "Europe/Stockholm"),
    "norway": ("NO", None, "Europe/Oslo"),
    "no": ("NO", None, "Europe/Oslo"),
    "finland": ("FI", None, "Europe/Helsinki"),
    "fi": ("FI", None, "Europe/Helsinki"),
    "poland": ("PL", None, "Europe/Warsaw"),
    "pl": ("PL", None, "Europe/Warsaw"),
    "portugal": ("PT", None, "Europe/Lisbon"),
    "pt": ("PT", None, "Europe/Lisbon"),
    "ireland": ("IE", None, "Europe/Dublin"),
    "ie": ("IE", None, "Europe/Dublin"),
    "canada": ("CA", None, "America/Toronto"),
    "ca": ("CA", None, "America/Toronto"),
    "australia": ("AU", None, "Australia/Sydney"),
    "au": ("AU", None, "Australia/Sydney"),
    "new zealand": ("NZ", None, "Pacific/Auckland"),
    "nz": ("NZ", None, "Pacific/Auckland"),
    "japan": ("JP", None, "Asia/Tokyo"),
    "jp": ("JP", None, "Asia/Tokyo"),
    "india": ("IN", None, "Asia/Kolkata"),
    "in": ("IN", None, "Asia/Kolkata"),
    "singapore": ("SG", None, "Asia/Singapore"),
    "sg": ("SG", None, "Asia/Singapore"),
    "south africa": ("ZA", None, "Africa/Johannesburg"),
    "za": ("ZA", None, "Africa/Johannesburg"),
    "brazil": ("BR", None, "America/Sao_Paulo"),
    "br": ("BR", None, "America/Sao_Paulo"),
    "serbia": ("RS", None, "Europe/Belgrade"),
    "rs": ("RS", None, "Europe/Belgrade"),
}

_US_STATE_ALIASES: dict[str, str] = {
    "california": "CA",
    "new york": "NY",
    "texas": "TX",
    "florida": "FL",
    "washington": "WA",
    "massachusetts": "MA",
    "illinois": "IL",
    "colorado": "CO",
}


def _normalize_place(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _resolve_place(location: str) -> tuple[str, str | None, str, str] | None:
    """Return (country, subdiv, timezone, label) or None."""
    raw = _normalize_place(location)
    if not raw:
        return None

    if raw in _PLACE_ALIASES:
        country, subdiv, tz = _PLACE_ALIASES[raw]
        label = location.strip() or country
        return country, subdiv, tz, label

    if raw in _US_STATE_ALIASES:
        subdiv = _US_STATE_ALIASES[raw]
        return "US", subdiv, "America/New_York", location.strip()

    # "bayern, germany" / "bavaria germany"
    for alias, (country, subdiv, tz) in _PLACE_ALIASES.items():
        if alias in raw and len(alias) > 1:
            return country, subdiv, tz, location.strip()

    # Bare ISO country code
    code = raw.upper()
    if len(code) in {2, 3}:
        try:
            holidays.country_holidays(code, years=date.today().year)
            return code, None, "UTC", location.strip().upper()
        except NotImplementedError:
            pass

    return None


def _parse_when(when: str, *, tz_name: str) -> date:
    text = (when or "today").strip().lower()
    now = datetime.now(ZoneInfo(tz_name)).date()
    if text in {"", "today", "now"}:
        return now
    if text == "tomorrow":
        return now + timedelta(days=1)
    if text == "yesterday":
        return now - timedelta(days=1)
    # YYYY-MM-DD
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(
            f"Could not parse date '{when}'. Use today, tomorrow, yesterday, "
            "or YYYY-MM-DD."
        ) from exc


def _holiday_calendar(country: str, subdiv: str | None, years: list[int]):
    kwargs: dict = {"years": years}
    if subdiv:
        kwargs["subdiv"] = subdiv
    return holidays.country_holidays(country, **kwargs)


@tool(
    description=(
        "Look up public / bank holidays for a country or region on a given "
        "date (default today), or list upcoming holidays. Pass location like "
        "'Bayern', 'Bavaria', 'Germany', 'US', 'California', 'Denmark'. Pass "
        "when as 'today', 'tomorrow', or YYYY-MM-DD."
    )
)
async def lookup_public_holiday(
    location: str,
    when: str = "today",
    upcoming_days: int = 0,
    context: ToolContext = None,
) -> ToolResult:
    """Answer holiday questions for a place and date.

    Args:
        location: Country or region, e.g. Bayern, Bavaria, Germany, US.
        when: today, tomorrow, yesterday, or YYYY-MM-DD.
        upcoming_days: If > 0, also list holidays in the next N days
            (useful for "what's next" / "this month" style asks; use 30 or 60).
    """
    resolved = _resolve_place(location)
    if not resolved:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unknown_location",
                "message": (
                    f"Could not map '{location}' to a supported country or "
                    "region. Ask for a country (Germany, US, Denmark) or a "
                    "known region (Bayern/Bavaria, California, England)."
                ),
                "instruction": (
                    "Ask one clarifying question for the country or region. "
                    "Do not invent whether it is a holiday."
                ),
            }
        )

    country, subdiv, tz_name, label = resolved
    try:
        target = _parse_when(when, tz_name=tz_name)
    except ValueError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "bad_date",
                "message": str(exc),
                "instruction": (
                    "Ask for today/tomorrow or an ISO date. Do not guess."
                ),
            }
        )

    years = sorted({target.year, target.year + 1})
    try:
        cal = _holiday_calendar(country, subdiv, years)
    except NotImplementedError:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unsupported_location",
                "message": (
                    f"Public holidays for {label} ({country}"
                    f"{'/' + subdiv if subdiv else ''}) are not in the "
                    "holiday dataset."
                ),
                "instruction": (
                    "Say this location is not supported yet. Do not invent "
                    "holidays."
                ),
            }
        )

    holiday_name = cal.get(target)
    is_holiday = target in cal

    upcoming: list[dict[str, str]] = []
    horizon = max(0, min(int(upcoming_days or 0), 366))
    if horizon:
        for offset in range(0, horizon + 1):
            day = target + timedelta(days=offset)
            name = cal.get(day)
            if name:
                upcoming.append({"date": day.isoformat(), "name": str(name)})

    place_bits = [country]
    if subdiv:
        place_bits.append(subdiv)

    return ToolResult(
        llm_response={
            "ok": True,
            "location_asked": location,
            "resolved_label": label,
            "country": country,
            "subdivision": subdiv,
            "place_code": "/".join(place_bits),
            "timezone_used": tz_name,
            "date": target.isoformat(),
            "is_public_holiday": is_holiday,
            "holiday_name": str(holiday_name) if holiday_name else None,
            "upcoming_holidays": upcoming,
            "source": "Python holidays package (public/bank holidays)",
            "instruction": (
                "Answer clearly whether that date is a public holiday in the "
                "resolved place. Name the holiday when is_public_holiday is "
                "true. Mention this covers public/bank holidays, not company "
                "shutdowns or school-only breaks, unless asked. If "
                "upcoming_holidays is present, summarize briefly. Keep it "
                "short and Slack-friendly."
            ),
        }
    )
