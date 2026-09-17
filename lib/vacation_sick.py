"""Shared section extraction for the Vacation and Sick days Notion page."""

from __future__ import annotations

import re

BAMBOO_HOME_URL = "https://rasa.bamboohr.com/home/"
BAMBOO_SLACK_LINK = "<https://rasa.bamboohr.com/home/|rasa.bamboohr.com>"

# Caring for an adult relative is not on the Notion page. People Ops confirmed
# this answer; remove once the page itself covers the case.
FAMILY_CARE_GUIDANCE = (
    "How much time you can take, and what type, is decided case by case.\n"
    "- For the first day, tell your Manager and take a sick day.\n"
    "- If you need longer than that, talk to your Manager and People Ops, and "
    "log some of the days as offline days."
)

# Vacation-policy sections (carry-over, half-days, …) plus sick-leave sections.
_SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "everyone": ("for everyone",),
    "germany": ("for employees in germany",),
    "uk": ("for employees in the uk", "for employees in uk"),
    "serbia": ("for employees in serbia",),
    "france": ("for employees in france",),
    "us": ("for employees in the us", "for employees in us"),
    # "hospital stay" alone also appears in the Germany bullets.
    "surgery": ("surgery leave",),
    "child_sick": ("my kid got sick",),
    "offline": ("offline days",),
    "vacation_booking": ("plan your vacation",),
    "ooo_template": (
        "is there a template for ooo email",
        "template for ooo email",
    ),
    # Shared vacation rules (no dedicated heading for carry-over — the rule
    # sentence itself contains "carry over").
    "carry_over": ("carry over", "carry-over", "carried-over"),
    "half_days": (
        "december 24th",
        "half a day off",
        "half day on december",
    ),
    "sick_during_vacation": (
        "sick during my vacation",
        "sick during vacation",
    ),
}

_STRUCTURAL_BOUNDARIES = (
    "additional tasks depending on your country",
    "additional important information on vacation days",
    "plan your vacation",
    "offline days",
    "faq",
    "is there a template for ooo email",
    "what if i get sick during my vacation",
    "will i still receive the home office allowance",
    "my kid got sick",
)

# Nested "For everyone:" under Plan your vacation is content, not a stop.
_IGNORE_BOUNDARY_SECTIONS: dict[str, frozenset[str]] = {
    "vacation_booking": frozenset({"everyone"}),
}


def _clean_line(line: str) -> str:
    return re.sub(r"^[\s#>*\-\d.)\[\]xX]+", "", line).strip().lower()


def _is_heading_match(cleaned: str, markers: tuple[str, ...]) -> bool:
    """True when the matching line is a title, not the rule itself."""
    remainder = cleaned
    for marker in markers:
        remainder = remainder.replace(marker, " ")
    remainder = re.sub(r"[\s:?./\-]+", " ", remainder).strip()
    return len(remainder) < 40


def extract_section(body: str, section: str) -> str | None:
    """Extract one named section from flattened Notion block text.

    If the marker appears inside the policy sentence (carry-over), that line is
    kept. Own-section markers are not treated as stop boundaries, so answer
    lines that repeat the phrase still get included.
    """
    markers = _SECTION_MARKERS[section]
    own = set(markers)
    ignore_sections = _IGNORE_BOUNDARY_SECTIONS.get(section, frozenset())
    boundaries = [
        *(_STRUCTURAL_BOUNDARIES),
        *(
            marker
            for key, key_markers in _SECTION_MARKERS.items()
            if key != section and key not in ignore_sections
            for marker in key_markers
            if marker not in own
        ),
    ]

    lines = body.splitlines()
    start: int | None = None

    for index, line in enumerate(lines):
        cleaned = _clean_line(line)
        if not any(marker in cleaned for marker in markers):
            continue
        start = index + 1 if _is_heading_match(cleaned, markers) else index
        break

    if start is None:
        return None

    selected: list[str] = []
    for line in lines[start:]:
        cleaned = _clean_line(line)
        if any(marker in cleaned for marker in boundaries):
            break
        selected.append(line)

    text = "\n".join(selected).strip()
    return text or None


VACATION_POLICY_SECTIONS = ("carry_over", "half_days", "offline", "sick_during_vacation")
