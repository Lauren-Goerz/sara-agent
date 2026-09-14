"""Shared access layer for Sara's allowlisted Notion sources.

Skills declare which registered source they read; this module owns fetching,
cleaning, caching, and trimming the payload that reaches the LLM. Only the
sections relevant to the user's question are returned, so a large policy page
does not become a large prompt.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from lib import notion_client

# Cleaned page bodies change rarely; re-reading Notion on every turn is slow
# and pointless.
_CACHE_TTL_SECONDS = 300.0
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

_DEFAULT_CHAR_LIMIT = 6000
_PREAMBLE_CHAR_LIMIT = 900

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "are", "can", "you", "our", "with", "what", "how",
        "does", "did", "was", "were", "have", "has", "any", "about", "from",
        "that", "this", "there", "when", "where", "who", "why", "rasa", "please",
        "tell", "give", "need", "want", "into", "out", "get", "got", "would",
        "should", "could", "policy", "page", "info", "information",
    }
)


@dataclass(frozen=True)
class NotionSource:
    """One allowlisted Notion page or database."""

    key: str
    notion_id: str
    url: str
    title: str
    # page, database, or auto (try database rows first, then page body).
    kind: str = "page"
    max_blocks: int = 400
    max_rows: int = 200
    # Extra words that should always count as a match for this source.
    keywords: tuple[str, ...] = field(default_factory=tuple)
    # Keep Notion bookmark/embed URLs (slides, recordings). Signed [file]
    # URLs are still dropped — they expire and crowd the prompt.
    keep_links: bool = False
    # Optional Notion database query (only used when kind is database/auto).
    database_filter: dict[str, Any] | None = None
    database_sorts: tuple[dict[str, Any], ...] = ()
    include_row_url: bool = True
    related_links: tuple[str, ...] = ()
    related_source_keys: tuple[str, ...] = ()
    always_include_related: bool = False


SOURCES: dict[str, NotionSource] = {
    "benefits": NotionSource(
        key="benefits",
        notion_id="bd1165c5ece74392917d3b3eaffb4388",
        url=(
            "https://app.notion.com/p/rasa/"
            "Benefits-Perks-2026-bd1165c5ece74392917d3b3eaffb4388"
        ),
        title="Benefits & Perks 2026",
        max_blocks=600,
        keywords=(
            "vacation",
            "pto",
            "annual",
            "leave",
            "entitlement",
            "days",
            "holiday",
        ),
    ),
    "vacation_sick": NotionSource(
        key="vacation_sick",
        notion_id="137b9c0d544a80f3aae3eaaec6a7cf0a",
        url=(
            "https://app.notion.com/p/rasa/"
            "Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a"
        ),
        title="Vacation and Sick days",
        max_blocks=600,
        keywords=(
            "vacation",
            "sick",
            "offline",
            "ooo",
            "child",
            "family",
            "carry",
        ),
    ),
    "work_abroad": NotionSource(
        key="work_abroad",
        notion_id="cd21b2caa0214c85aa2410bb0814e446",
        url=(
            "https://app.notion.com/p/rasa/"
            "Working-from-other-Countries-cd21b2caa0214c85aa2410bb0814e446"
        ),
        title="Working from other Countries",
        max_blocks=600,
    ),
    "part_time": NotionSource(
        key="part_time",
        notion_id="243d2dd4d25a4fe1876b60ef344a8968",
        url=(
            "https://app.notion.com/p/rasa/"
            "Working-Part-Time-at-Rasa-243d2dd4d25a4fe1876b60ef344a8968"
        ),
        title="Working Part-Time at Rasa",
        max_blocks=400,
        keywords=(
            "part-time",
            "part time",
            "hours",
            "week",
            "teilzeit",
            "20h",
            "30h",
            "reduced",
        ),
    ),
    "social_media": NotionSource(
        key="social_media",
        notion_id="39d0d3053dc44c9e89c2baba3230eb4c",
        url=(
            "https://app.notion.com/p/rasa/"
            "Social-Media-Policy-39d0d3053dc44c9e89c2baba3230eb4c"
        ),
        title="Social Media Policy",
    ),
    "slack_guidelines": NotionSource(
        key="slack_guidelines",
        notion_id="256b9c0d544a80d1b41dd9f62949dddd",
        url=(
            "https://app.notion.com/p/rasa/"
            "Slack-Guidelines-256b9c0d544a80d1b41dd9f62949dddd"
        ),
        title="Slack Guidelines",
        max_blocks=600,
        keywords=(
            "slack",
            "profile",
            "display",
            "name",
            "channel",
            "channels",
            "dm",
            "dms",
            "status",
            "open",
        ),
    ),
    "company_values": NotionSource(
        key="company_values",
        notion_id="f3afec52e31742f292f9a776d4ef712d",
        url=(
            "https://app.notion.com/p/rasa/"
            "Rasa-s-Company-Values-f3afec52e31742f292f9a776d4ef712d"
        ),
        title="Rasa's Company Values",
        max_blocks=200,
    ),
    "company_info": NotionSource(
        key="company_info",
        notion_id="44a36a2d9f8745adbc7827769f530906",
        url=(
            "https://app.notion.com/p/rasa/"
            "Rasa-Offices-banking-important-info-44a36a2d9f8745adbc7827769f530906"
        ),
        title="Rasa Offices, banking & important info",
        max_blocks=500,
    ),
    "board": NotionSource(
        key="board",
        notion_id="984687d72adb4c0fb459c3e9bb280565",
        url="https://app.notion.com/p/rasa/Board-984687d72adb4c0fb459c3e9bb280565",
        title="Board",
        kind="auto",
        max_blocks=300,
        max_rows=100,
    ),
    "signing_documents": NotionSource(
        key="signing_documents",
        notion_id="9f1daaf4a269400b8a2f854ffe0a313c",
        url=(
            "https://app.notion.com/p/rasa/"
            "Signing-Documents-9f1daaf4a269400b8a2f854ffe0a313c"
        ),
        title="Signing Documents",
        max_blocks=600,
        keywords=(
            "sign",
            "signing",
            "signature",
            "signatory",
            "authority",
            "contract",
            "employment",
            "serbia",
            "germany",
            "uk",
            "france",
            "us",
            "india",
        ),
    ),
    "hiring_contractors": NotionSource(
        key="hiring_contractors",
        notion_id="2e182b6b188d46b9a0b991a435041f75",
        url=(
            "https://app.notion.com/p/rasa/"
            "Working-with-Contractors-Agency-s-2e182b6b188d46b9a0b991a435041f75"
        ),
        title="Working with Contractors & Agency’s",
        max_blocks=600,
        keep_links=True,
        keywords=(
            "contractor",
            "contractors",
            "freelancer",
            "agency",
            "agreement",
            "hire",
            "hiring",
            "intake",
            "w9",
        ),
    ),
    "security_incidents": NotionSource(
        key="security_incidents",
        notion_id="202b9c0d544a8143be59e3e3568b1b4d",
        url=(
            "https://app.notion.com/p/rasa/"
            "202b9c0d544a8143be59e3e3568b1b4d"
            "?v=202b9c0d544a816bb595000c37f7dab3"
        ),
        title="Security incidents tracker",
        kind="auto",
        max_blocks=500,
    ),
    "rfp_security": NotionSource(
        key="rfp_security",
        notion_id="0f73f9f5d14342e4bfff68423e73ba3e",
        url=(
            "https://app.notion.com/p/rasa/"
            "0f73f9f5d14342e4bfff68423e73ba3e"
            "?v=a22c9219c6a34f24835c43c25b757131"
        ),
        title="Vendor Security Questionnaire Bank",
        kind="auto",
        max_blocks=600,
        max_rows=300,
    ),
    "yubikey": NotionSource(
        key="yubikey",
        notion_id="5a3e653ef9f54accb8646444263f5f42",
        url=(
            "https://app.notion.com/p/rasa/"
            "All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42"
        ),
        title="All about Yubikeys / google phones",
    ),
    "yubisneeze": NotionSource(
        key="yubisneeze",
        notion_id="5a3e653ef9f54accb8646444263f5f42",
        url=(
            "https://app.notion.com/p/rasa/"
            "All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42"
            "#e9faa6c469a34069a3f1219bb4bea0f2"
        ),
        title="Undo the Yubisneeze",
        max_blocks=500,
        keywords=("yubisneeze", "sneeze", "undo", "otp"),
    ),
    "laptop_repairs": NotionSource(
        key="laptop_repairs",
        notion_id="ccda2595781346bfb3de7c64d5715ac6",
        url=(
            "https://app.notion.com/p/rasa/"
            "Laptop-issues-repairs-ccda2595781346bfb3de7c64d5715ac6"
        ),
        title="Laptop issues & repairs",
        max_blocks=200,
        related_links=(
            "<https://getsupport.apple.com/solutions|Apple Support>",
        ),
    ),
    "travel_insurance": NotionSource(
        key="travel_insurance",
        notion_id="fea448cc42fb4348b4a74f12736c1c50",
        url=(
            "https://app.notion.com/p/rasa/"
            "Travel-Insurances-2026-fea448cc42fb4348b4a74f12736c1c50"
        ),
        title="Travel Insurances 2026",
        max_blocks=600,
        keywords=("travel", "insurance", "insurances", "trip", "cover"),
    ),
    "us_visa": NotionSource(
        key="us_visa",
        notion_id="1f8b9c0d544a80df8ea6e5d7021653ac",
        url=(
            "https://app.notion.com/p/rasa/"
            "US-Visa-Process-B1-B2-Tourism-Business-"
            "1f8b9c0d544a80df8ea6e5d7021653ac"
        ),
        title="US Visa Process (B1/B2 Tourism & Business)",
        max_blocks=600,
        keywords=("visa", "b1", "b2", "esta", "ds160", "consulate"),
    ),
    "business_travel": NotionSource(
        key="business_travel",
        notion_id="f5c1d8842db048539e065865d0e066cf",
        url=(
            "https://app.notion.com/p/rasa/"
            "Business-Travel-f5c1d8842db048539e065865d0e066cf"
        ),
        title="Business Travel",
        max_blocks=600,
        keywords=(
            "flight",
            "economy",
            "hotel",
            "perdiem",
            "per-diem",
            "receipt",
            "transport",
            "train",
            "expense",
        ),
    ),
    "remote_budget": NotionSource(
        key="remote_budget",
        notion_id="fb07ed3e076f4096a15a1d4fc95091ed",
        url=(
            "https://app.notion.com/p/rasa/"
            "Remote-Budget-2026-fb07ed3e076f4096a15a1d4fc95091ed"
        ),
        title="Remote Budget - 2026",
        max_blocks=600,
        keywords=(
            "remote",
            "budget",
            "home",
            "office",
            "coworking",
            "co-working",
            "internet",
            "utility",
            "payhawk",
        ),
    ),
    "sexual_harassment": NotionSource(
        key="sexual_harassment",
        notion_id="bde30194f1794d77a1b8055fca871369",
        url=(
            "https://app.notion.com/p/rasa/"
            "Sexual-Harassment-Policy-bde30194f1794d77a1b8055fca871369"
        ),
        title="Sexual Harassment Policy",
        max_blocks=600,
        keywords=(
            "sexual",
            "harassment",
            "harass",
            "inappropriate",
            "consent",
            "complaint",
            "complaints",
            "hostile",
            "workplace",
        ),
    ),
    "employee_handbooks": NotionSource(
        key="employee_handbooks",
        notion_id="defd5187553d4e8598e412a115679b40",
        url=(
            "https://app.notion.com/p/rasa/"
            "Employee-Handbooks-defd5187553d4e8598e412a115679b40"
        ),
        title="Employee Handbooks",
        max_blocks=400,
        keywords=(
            "handbook",
            "handbooks",
            "employee",
            "country",
            "germany",
            "berlin",
            "usa",
            "uk",
            "ireland",
            "spain",
            "netherlands",
            "canada",
            "india",
        ),
    ),
    "employee_equity": NotionSource(
        key="employee_equity",
        notion_id="1da6be3271984b239d5f441cb968984e",
        url=(
            "https://app.notion.com/p/rasa/"
            "Employee-Equity-1da6be3271984b239d5f441cb968984e"
        ),
        title="Employee Equity",
        max_blocks=400,
        keywords=(
            "equity",
            "stock",
            "options",
            "compensation",
            "dei",
        ),
        related_source_keys=(
            "employee_equity_how_options_work",
            "employee_equity_compensation",
            "equity_refresh_policy",
        ),
        always_include_related=True,
    ),
    "employee_equity_how_options_work": NotionSource(
        key="employee_equity_how_options_work",
        notion_id="0780fa938be1449385eebd3210c648e5",
        url=(
            "https://app.notion.com/p/rasa/"
            "Employee-Equity-How-Options-Work-0780fa938be1449385eebd3210c648e5"
        ),
        title="Employee Equity: How Options Work",
        max_blocks=600,
        keywords=(
            "carta",
            "exercise",
            "vesting",
            "cliff",
            "strike",
            "option",
            "options",
            "see",
            "view",
            "portal",
            "login",
        ),
        related_source_keys=(
            "employee_equity",
            "employee_equity_compensation",
            "equity_refresh_policy",
        ),
        always_include_related=True,
    ),
    "employee_equity_compensation": NotionSource(
        key="employee_equity_compensation",
        notion_id="546b37a91911448bbf084be36bd322f6",
        url=(
            "https://app.notion.com/p/rasa/"
            "Employee-Equity-How-We-Use-Options-as-Compensation-"
            "546b37a91911448bbf084be36bd322f6"
        ),
        title="Employee Equity: How We Use Options as Compensation",
        max_blocks=600,
        keywords=(
            "grant",
            "initial",
            "promotion",
            "refresh",
            "seniority",
            "location",
            "part-time",
            "leave",
            "how many",
            "topped",
            "top-up",
            "topup",
        ),
        related_source_keys=(
            "employee_equity",
            "employee_equity_how_options_work",
            "equity_refresh_policy",
        ),
        always_include_related=True,
    ),
    "equity_refresh_policy": NotionSource(
        key="equity_refresh_policy",
        notion_id="af5be3af4034438c90ddc17f960cce8d",
        url=(
            "https://app.notion.com/p/rasa/"
            "Equity-Refresh-Policy-af5be3af4034438c90ddc17f960cce8d"
        ),
        title="Equity Refresh Policy",
        max_blocks=600,
        keywords=(
            "refresh",
            "topped",
            "top-up",
            "topup",
            "anniversary",
            "two year",
            "2 year",
        ),
        related_source_keys=(
            "employee_equity",
            "employee_equity_how_options_work",
            "employee_equity_compensation",
        ),
        always_include_related=True,
    ),
    "learning_development": NotionSource(
        key="learning_development",
        notion_id="a744377944c1416592c0a9fdb761b2f4",
        url=(
            "https://app.notion.com/p/rasa/"
            "Learning-Development-a744377944c1416592c0a9fdb761b2f4"
        ),
        title="Learning & Development",
        max_blocks=600,
        keywords=(
            "learning",
            "development",
            "education",
            "edu",
            "budget",
            "course",
            "courses",
            "training",
            "conference",
            "conferences",
            "certification",
            "study",
            "months",
            "allocated",
            "eligibility",
            "pro-rata",
            "prorata",
            "pdp",
        ),
    ),
    "mandatory_training": NotionSource(
        key="mandatory_training",
        notion_id="30ab9c0d544a803a90badcbe0de916ef",
        url=(
            "https://app.notion.com/p/rasa/"
            "Mandatory-Training-Policy-2026-30ab9c0d544a803a90badcbe0de916ef"
        ),
        title="Mandatory Training Policy 2026",
        max_blocks=400,
        keywords=(
            "mandatory",
            "training",
            "easyllama",
            "compliance",
            "gdpr",
            "harassment",
            "occupational",
            "ai act",
        ),
    ),
    "relocation_germany": NotionSource(
        key="relocation_germany",
        notion_id="79de728aadc5486b940bdd79b70235d8",
        url=(
            "https://app.notion.com/p/rasa/"
            "Relocation-Guide-Germany-79de728aadc5486b940bdd79b70235d8"
        ),
        title="Relocation Guide Germany",
        max_blocks=600,
        keywords=(
            "relocation",
            "relocate",
            "move",
            "moving",
            "visa",
            "permit",
            "shipping",
            "package",
        ),
        related_source_keys=("welcome_berlin", "working_in_germany"),
        always_include_related=True,
    ),
    "welcome_berlin": NotionSource(
        key="welcome_berlin",
        notion_id="fde61822cf77417c8712380d47fba265",
        url=(
            "https://app.notion.com/p/rasa/"
            "Welcome-to-Berlin-fde61822cf77417c8712380d47fba265"
        ),
        title="Welcome to Berlin",
        max_blocks=600,
        keywords=(
            "berlin",
            "welcome",
            "neighborhood",
            "neighbourhood",
            "apartment",
            "flat",
            "anmeldung",
            "city",
        ),
        related_source_keys=("relocation_germany", "working_in_germany"),
        always_include_related=True,
    ),
    "working_in_germany": NotionSource(
        key="working_in_germany",
        notion_id="f9ae50b8c6cc438e8e86b4c5dbaff1ac",
        url=(
            "https://app.notion.com/p/rasa/"
            "Overview-Working-in-Germany-f9ae50b8c6cc438e8e86b4c5dbaff1ac"
        ),
        title="Overview: Working in Germany",
        max_blocks=600,
        keywords=(
            "working",
            "germany",
            "employment",
            "tax",
            "contract",
            "payroll",
            "social",
            "insurance",
        ),
        related_source_keys=("relocation_germany", "welcome_berlin"),
        always_include_related=True,
    ),
    "berlin_office": NotionSource(
        key="berlin_office",
        notion_id="7a57e119a0fb443b9c9ce6a481e14578",
        url=(
            "https://app.notion.com/p/rasa/"
            "Working-from-Berlin-Office-7a57e119a0fb443b9c9ce6a481e14578"
        ),
        title="Working from Berlin Office",
        max_blocks=600,
        keywords=(
            "berlin",
            "office",
            "desk",
            "hq",
            "building",
            "access",
            "nuki",
            "wifi",
            "guest",
            "zoom",
            "tv",
            "printer",
            "snacks",
            "lunch",
            "visitor",
            "package",
            "ac",
            "cleaning",
            "workplace",
        ),
    ),
    "berlin_fire_safety": NotionSource(
        key="berlin_fire_safety",
        notion_id="a1c6df69943847bea14c91ebc0e8de6d",
        url=(
            "https://app.notion.com/p/rasa/"
            "Fire-Safety-at-Rasa-a1c6df69943847bea14c91ebc0e8de6d"
        ),
        title="Fire Safety at Rasa",
        max_blocks=600,
        keywords=(
            "fire",
            "extinguisher",
            "exit",
            "marshal",
            "evacuation",
            "112",
            "first",
            "aid",
        ),
    ),
    "berlin_pets": NotionSource(
        key="berlin_pets",
        notion_id="fb1e4a2be3a04f0da17fccc4b178cbb2",
        url=(
            "https://app.notion.com/p/rasa/"
            "Pets-in-the-office-fb1e4a2be3a04f0da17fccc4b178cbb2"
        ),
        title="Pets in the office",
        max_blocks=500,
        keywords=(
            "pet",
            "pets",
            "dog",
            "dogs",
            "cat",
            "insurance",
            "comfortable",
        ),
    ),
    "ai_tools": NotionSource(
        key="ai_tools",
        notion_id="ea4e9ed1af46449b9fb036bcf70b2795",
        url=(
            "https://app.notion.com/p/rasa/"
            "Using-AI-Tools-at-Rasa-ea4e9ed1af46449b9fb036bcf70b2795"
        ),
        title="Using AI Tools at Rasa",
        max_blocks=600,
        keywords=(
            "ai",
            "chatgpt",
            "claude",
            "gemini",
            "copilot",
            "llm",
            "tools",
            "approved",
            "generative",
        ),
    ),
    "crowdstrike": NotionSource(
        key="crowdstrike",
        notion_id="7e762e4d1b4e4beb917b71f4f304d375",
        url=(
            "https://app.notion.com/p/rasa/"
            "Crowdstrike-7e762e4d1b4e4beb917b71f4f304d375"
        ),
        title="Crowdstrike",
        max_blocks=400,
        keywords=(
            "crowdstrike",
            "crowd",
            "strike",
            "falcon",
            "edr",
            "endpoint",
            "browsing",
            "tracking",
            "monitoring",
        ),
    ),
    "kandji": NotionSource(
        key="kandji",
        notion_id="1f4b9c0d544a8029888cd852181b9b58",
        url=(
            "https://app.notion.com/p/rasa/"
            "Kandji-Iru-1f4b9c0d544a8029888cd852181b9b58"
        ),
        title="Kandji / Iru",
        max_blocks=400,
        keywords=(
            "kandji",
            "iru",
            "mdm",
            "keystroke",
            "keystrokes",
            "mac",
            "device",
            "management",
            "tracking",
            "monitoring",
        ),
    ),
    "all_hands": NotionSource(
        key="all_hands",
        notion_id="0ace3e5a54b04170adccd1f3d6a02e53",
        url=(
            "https://app.notion.com/p/rasa/"
            "All-Hands-Slides-Recordings-78c804f648094a2389dd0cc494fe6fec"
        ),
        title="All Hands: Slides & Recordings",
        kind="database",
        max_rows=50,
        keep_links=True,
        # Older rows often have missing or file-only links; 2025+ has URLs.
        database_filter={
            "property": "Date",
            "date": {"on_or_after": "2025-01-01"},
        },
        database_sorts=({"property": "Date", "direction": "descending"},),
        include_row_url=False,
        keywords=(
            "all",
            "hands",
            "offsite",
            "townhall",
            "slides",
            "deck",
            "recording",
            "latest",
            "recent",
            "last",
        ),
    ),
}


def clean_body(body: str, *, keep_links: bool = False) -> str:
    """Drop file/link lines whose signed URLs crowd out readable text."""
    cleaned_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("[file]"):
            continue
        if line.startswith("[link]"):
            if not keep_links:
                continue
            match = re.match(r"^\[link\]\s*(.*?):\s+(\S+)\s*$", line)
            if match:
                name, url = match.group(1).strip(), match.group(2).strip()
                cleaned_lines.append(f"<{url}|{name}>" if name else url)
            else:
                cleaned_lines.append(line)
            continue
        cleaned_lines.append(line)
    lines = cleaned_lines
    cleaned = "\n".join(lines).strip()
    if cleaned.endswith("\nUntitled"):
        cleaned = cleaned[: -len("\nUntitled")].rstrip()
    elif cleaned == "Untitled":
        cleaned = ""
    return cleaned


def rows_to_text(rows: list[dict[str, Any]], *, include_row_url: bool = True) -> str:
    """Flatten database rows into the same heading/bullet shape as page text."""
    chunks: list[str] = []
    for row in rows:
        title = row.get("title") or "Untitled"
        fields = row.get("fields") or {}
        lines = [f"## {title}"]
        for key, value in fields.items():
            text = str(value or "").strip()
            if text and text != title:
                lines.append(f"- {key}: {text}")
        url = row.get("url")
        if include_row_url and url:
            lines.append(f"- notion_url: {url}")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks).strip()


def _split_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (preamble, [(heading, section_text), ...])."""
    preamble_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []

    for line in body.splitlines():
        if re.match(r"^#{1,3}\s+\S", line):
            sections.append((line.lstrip("# ").strip(), [line]))
        elif sections:
            sections[-1][1].append(line)
        else:
            preamble_lines.append(line)

    return (
        "\n".join(preamble_lines).strip(),
        [(heading, "\n".join(lines).strip()) for heading, lines in sections],
    )


def _query_terms(query: str, extra: tuple[str, ...]) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", (query or "").lower())
    terms = [word for word in words if word not in _STOPWORDS]
    return list(dict.fromkeys(terms + list(extra)))


def _score(text: str, heading: str, terms: list[str]) -> int:
    if not terms:
        return 0
    body_lower = text.lower()
    heading_lower = heading.lower()
    score = 0
    for term in terms:
        score += body_lower.count(term)
        if term in heading_lower:
            score += 5
    return score


def select_relevant(
    body: str,
    *,
    query: str = "",
    char_limit: int = _DEFAULT_CHAR_LIMIT,
    extra_keywords: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Trim a source body down to the parts that answer the question."""
    body = body.strip()
    if len(body) <= char_limit:
        return {
            "content": body,
            "truncated": False,
            "matched_headings": [],
            "other_headings": [],
        }

    preamble, sections = _split_sections(body)
    terms = _query_terms(query, extra_keywords)

    if not sections:
        return {
            "content": body[:char_limit].rstrip(),
            "truncated": True,
            "matched_headings": [],
            "other_headings": [],
        }

    scored = [
        (_score(text, heading, terms), index, heading, text)
        for index, (heading, text) in enumerate(sections)
    ]
    matching = sorted(
        (item for item in scored if item[0] > 0),
        key=lambda item: (-item[0], item[1]),
    )
    # With no query match, fall back to document order so the answer still
    # starts from the top of the page rather than an arbitrary section.
    chosen = matching or sorted(scored, key=lambda item: item[1])

    head = preamble[:_PREAMBLE_CHAR_LIMIT].rstrip() if preamble else ""
    used = len(head)

    # Pick by relevance, but emit in document order so the page still reads
    # top to bottom.
    picked: list[tuple[int, str, str]] = []
    for _, index, heading, text in chosen:
        if used + len(text) > char_limit:
            continue
        picked.append((index, heading, text))
        used += len(text)

    if not picked:
        # Single oversized section: keep a prefix rather than returning nothing.
        _, index, heading, text = chosen[0]
        picked.append(
            (index, heading, text[: max(char_limit - used, 500)].rstrip())
        )

    picked.sort(key=lambda item: item[0])
    matched_headings = [heading for _, heading, _ in picked]
    parts = [head, *(text for _, _, text in picked)]

    other = [
        heading for _, _, heading, _ in scored if heading not in matched_headings
    ]
    return {
        "content": "\n\n".join(part for part in parts if part).strip(),
        "truncated": True,
        "matched_headings": matched_headings,
        "other_headings": other[:25],
    }


async def _load_raw(source: NotionSource) -> dict[str, Any]:
    """Fetch and clean a source, using the short-lived cache when warm."""
    cached = _cache.get(source.key)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    raw: dict[str, Any] | None = None
    db_error: Exception | None = None

    if source.kind in {"database", "auto"}:
        try:
            rows = await notion_client.query_database(
                source.notion_id,
                max_rows=source.max_rows,
                filter=source.database_filter,
                sorts=list(source.database_sorts) or None,
            )
            text = rows_to_text(rows, include_row_url=source.include_row_url)
            if text:
                raw = {
                    "ok": True,
                    "source_kind": "database",
                    "title": source.title,
                    "last_edited_time": None,
                    "row_count": len(rows),
                    "body": text,
                }
        except notion_client.NotionConfigError:
            raise
        except Exception as error:  # noqa: BLE001
            db_error = error

    if raw is None and source.kind in {"page", "auto"}:
        page = await notion_client.get_page_with_body(
            source.notion_id,
            max_blocks=source.max_blocks,
        )
        raw = {
            "ok": True,
            "source_kind": "page",
            "title": page.get("title") or source.title,
            "last_edited_time": page.get("last_edited_time"),
            "row_count": None,
            "body": clean_body(page.get("body") or "", keep_links=source.keep_links),
        }

    if raw is None:
        raise db_error or RuntimeError(f"Could not load Notion source {source.key}")

    _cache[source.key] = (time.monotonic(), raw)
    return raw


def slack_link(key: str) -> str:
    """Return the canonical Slack hyperlink for a registered source."""
    source = SOURCES[key]
    return f"<{source.url}|{source.title}>"


async def load_full(key: str) -> dict[str, Any]:
    """Return one registered source without query-aware trimming."""
    source = SOURCES[key]
    try:
        raw = await _load_raw(source)
    except notion_client.NotionConfigError as exc:
        return {
            "ok": False,
            "error": "not_configured",
            "message": str(exc),
            "source_url": source.url,
            "page_title": source.title,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "ok": False,
            "error": "notion_page_unavailable",
            "message": (
                f"'{source.title}' is not visible to Sara's Notion integration."
            ),
            "status_code": exc.response.status_code,
            "source_url": source.url,
            "page_title": source.title,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": "notion_error",
            "message": str(exc),
            "source_url": source.url,
            "page_title": source.title,
        }
    return {
        "ok": True,
        "source_url": source.url,
        "page_title": raw.get("title") or source.title,
        "last_edited_time": raw.get("last_edited_time"),
        "source_kind": raw.get("source_kind"),
        "body": raw.get("body") or "",
    }


async def load(
    key: str,
    *,
    query: str = "",
    char_limit: int = _DEFAULT_CHAR_LIMIT,
    fallback_content: str | None = None,
) -> dict[str, Any]:
    """Return a normalized payload for a registered source.

    On success: ok=True with source_content trimmed to the relevant sections.
    On failure: ok=False with an error code and the source_url to share, unless
    fallback_content is supplied.
    """
    source = SOURCES[key]
    base = {"query": query, "source_url": source.url, "page_title": source.title}

    def _failed(error: str, message: str, **extra: Any) -> dict[str, Any]:
        if fallback_content:
            selected = select_relevant(
                fallback_content,
                query=query,
                char_limit=char_limit,
                extra_keywords=source.keywords,
            )
            return {
                **base,
                "ok": True,
                "used_fallback": True,
                "source_kind": "fallback",
                "last_edited_time": None,
                "source_content": selected["content"],
                "content_truncated": selected["truncated"],
                "other_sections": selected["other_headings"],
            }
        return {**base, "ok": False, "error": error, "message": message, **extra}

    try:
        raw = await _load_raw(source)
    except notion_client.NotionConfigError as exc:
        return _failed("not_configured", str(exc))
    except httpx.HTTPStatusError as exc:
        return _failed(
            "notion_page_unavailable",
            (
                f"'{source.title}' is not visible to Sara's Notion integration. "
                "Share it with the Sara-Agent integration and retry."
            ),
            status_code=exc.response.status_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _failed("notion_error", str(exc))

    body = raw.get("body") or ""
    if not body:
        return _failed("empty_source", "The Notion source had no readable text.")

    selected = select_relevant(
        body,
        query=query,
        char_limit=char_limit,
        extra_keywords=source.keywords,
    )
    return {
        **base,
        "ok": True,
        "used_fallback": False,
        "source_kind": raw.get("source_kind"),
        "page_title": raw.get("title") or source.title,
        "last_edited_time": raw.get("last_edited_time"),
        "row_count": raw.get("row_count"),
        "source_content": selected["content"],
        "content_truncated": selected["truncated"],
        "other_sections": selected["other_headings"],
    }
