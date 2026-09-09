"""Look up a specific policy page under the Security hub (link only)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_HUB_URL = (
    "https://app.notion.com/p/rasa/"
    "Updated-Policies-Procedures-WIP-333b9c0d544a81ea8e0bf456564f47e0"
)
_HUB_TITLE = "Security, Compliance & Risk Policies and Procedures"

# Authoritative child pages under the hub (fetched from Notion). First title wins
# when Notion lists duplicates.
_POLICIES: tuple[tuple[str, str], ...] = (
    ("Information Security Policy", "333b9c0d544a817cbf99d3f0ab673a9f"),
    ("Access Control & IAM Policy", "333b9c0d544a81b498d6c5be5d541e1a"),
    ("Acceptable Use Policy", "333b9c0d544a81f0a91fdfe145cfdf08"),
    ("Security Incident Management Policy", "333b9c0d544a817fa524c68ba178f519"),
    ("Change Management Policy", "333b9c0d544a81799f96e5b215073328"),
    ("Threat and Vulnerability Management Policy", "333b9c0d544a815d87a8d5711d1f4f4d"),
    ("Use of Cryptography Policy", "333b9c0d544a8111afc1eec7bc038b66"),
    ("Application Security Policy", "333b9c0d544a815b8cfbd09a6b37f5b4"),
    ("Supplier and Contractor Management Policy", "333b9c0d544a811f8335d8162e40113a"),
    ("Information Transfer and Data Handling Procedure", "333b9c0d544a8104a7adc98b0139a155"),
    ("Asset Management Policy", "33cb9c0d544a8186868ddb5ef2537659"),
    ("Physical Security Policy", "33cb9c0d544a818ca674d40e8b6e7a6d"),
    ("Secure Configuration Policy", "33cb9c0d544a8146a898e4d7b56e44c6"),
    ("Information Security Responsibilities", "33cb9c0d544a8110aae0e6c266827149"),
    ("Cloud Services Policy", "33cb9c0d544a8118885afff3866336bd"),
    ("Log Management Policy", "33cb9c0d544a81e4bcc1fb1928d59c7a"),
    (
        "Disaster Recovery and Business Continuity Plan",
        "33cb9c0d544a818e9186e0ecff50dd00",
    ),
    ("Intellectual Property Rights Policy", "33cb9c0d544a8188b617cbdcbb5134b0"),
    ("Software Supply Chain Security Policy", "33cb9c0d544a81e7bcd3df05082acd92"),
    ("Business Resiliency Program", "33cb9c0d544a81ffbcd9d9ce2898aca6"),
    ("AI Acceptable Use Policy", "33cb9c0d544a812eb90ecaf4e4f255b4"),
    ("Security Awareness and Training Policy", "33cb9c0d544a81bb98a5df74c1d215c9"),
    ("Product Export Classification Policy", "33cb9c0d544a8140af7ef4b146104da7"),
    ("Log Information Policy", "33cb9c0d544a81adac28cebf719a91e3"),
    ("Data Loss Prevention (DLP) Policy", "33cb9c0d544a81eb946adce4ffb26556"),
    ("AI Ethics Policy WIP", "344b9c0d544a8113afafe4bdd15ac958"),
    (
        "Vulnerability Management Policy - Bank of America",
        "374b9c0d544a81e9b3b1d525fac50aa4",
    ),
)

_GENERIC = frozenset(
    {
        "security",
        "compliance",
        "risk",
        "policy",
        "policies",
        "procedure",
        "procedures",
        "hub",
        "list",
        "all",
        "rasa",
        "the",
        "a",
        "an",
        "and",
        "or",
        "for",
        "of",
        "to",
        "about",
        "what",
        "is",
        "our",
        "me",
        "please",
        "show",
        "find",
        "get",
        "need",
        "want",
        "where",
        "can",
        "you",
        "i",
    }
)


def _slug(title: str) -> str:
    cleaned = re.sub(r"[^\w\s&-]", "", title, flags=re.UNICODE)
    cleaned = cleaned.replace("&", " ")
    cleaned = re.sub(r"[\s_]+", "-", cleaned.strip())
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned.strip("-")


def _policy_url(title: str, notion_id: str) -> str:
    return f"https://app.notion.com/p/rasa/{_slug(title)}-{notion_id}"


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _normalize(text).split() if t and t not in _GENERIC}


def _match_policy(query: str) -> tuple[str, str] | None:
    """Return (title, url) for the best hub child match, or None for the hub."""
    q = _normalize(query or "")
    if not q:
        return None

    q_tokens = _tokens(q)
    # Purely generic asks ("security policy", "compliance policies") → hub.
    if not q_tokens:
        return None

    best: tuple[float, str, str] | None = None
    for title, notion_id in _POLICIES:
        title_norm = _normalize(title)
        title_tokens = _tokens(title)
        url = _policy_url(title, notion_id)

        if q in title_norm or title_norm in q:
            score = 100.0
        else:
            overlap = len(q_tokens & title_tokens)
            if overlap == 0:
                # Allow short aliases: iam → access control, dlp → data loss…
                aliases = {
                    "iam": "access control",
                    "dlp": "data loss",
                    "bcp": "business continuity",
                    "dr": "disaster recovery",
                    "crypto": "cryptography",
                    "cryptography": "cryptography",
                    "appsec": "application security",
                    "sdlc": "application security",
                }
                alias_hit = False
                for alias, mapped in aliases.items():
                    if alias in q_tokens and set(mapped.split()) & title_tokens:
                        alias_hit = True
                        overlap = max(overlap, 2)
                        break
                if not alias_hit:
                    ratio = SequenceMatcher(None, q, title_norm).ratio()
                    if ratio < 0.55:
                        continue
                    score = ratio * 40.0
                else:
                    score = 50.0 + overlap * 10.0
            else:
                # Prefer denser overlap relative to the shorter token set.
                score = (overlap / max(len(q_tokens), 1)) * 80.0
                score += (overlap / max(len(title_tokens), 1)) * 20.0

        if best is None or score > best[0]:
            best = (score, title, url)

    if best is None or best[0] < 35.0:
        return None
    return best[1], best[2]


@tool(
    description=(
        "Look up the matching Security/Compliance/Risk policy page under the "
        "Updated Policies & Procedures hub. Pass the policy topic in query "
        "(e.g. 'access control', 'DLP', 'change management'). For a generic "
        "ask, leave query empty or say 'hub'."
    )
)
async def get_security_compliance_policy(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the specific policy page URL (or the hub) — link only.

    Args:
        query: Policy topic, e.g. access control, physical security, DLP.
    """
    matched = _match_policy(query)
    if matched is None:
        return ToolResult(
            llm_response={
                "ok": True,
                "matched": False,
                "title": _HUB_TITLE,
                "url": _HUB_URL,
                "instruction": (
                    "Share only the hub link below. Do not list every policy. "
                    "Say further questions go to #security. Do not summarize."
                ),
            }
        )

    title, url = matched
    return ToolResult(
        llm_response={
            "ok": True,
            "matched": True,
            "title": title,
            "url": url,
            "hub_url": _HUB_URL,
            "instruction": (
                "Share only this specific policy link (Slack mrkdwn). Do not "
                "summarize the policy. Say further questions go to #security. "
                "Do not share older standalone 2025 policy URLs."
            ),
        }
    )
