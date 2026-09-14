"""Deterministic links and referrals for policies Sara does not summarize."""

from __future__ import annotations

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult


_POLICIES = {
    "anti_bribery": {
        "links": [
            "<https://app.notion.com/p/rasa/Anti-Bribery-anti-Corruption-Fraud-prevention-policy-f431c6bfda0849b0b3233307f6c362d6|Anti-Bribery, anti Corruption & Fraud prevention policy>",
            "<https://app.notion.com/p/rasa/Ethics-Officer-at-Rasa-c1a4a11dae9844e5a162285c940267ad|Ethics Officer at Rasa>",
        ],
        "referral": "Further questions go to Rasa's Ethics Officer.",
    },
    "anti_slavery": {
        "links": [
            "<https://app.notion.com/p/rasa/Anti-slavery-Policy-b0b8a6d2413c482e9c61c3e614d154ca|Anti-slavery Policy>",
        ],
        "referral": "The official policy details are on that page.",
    },
    "whistleblower": {
        "links": [
            "<https://app.notion.com/p/rasa/Rasa-Whistleblower-Policy-Abridged-18b194bbcfb34927ae10cefa71d1388e|Rasa Whistleblower Policy (Abridged)>",
            "<https://app.notion.com/p/rasa/Ethics-Officer-at-Rasa-c1a4a11dae9844e5a162285c940267ad|Ethics Officer at Rasa>",
        ],
        "referral": "Further questions go to Rasa's Ethics Officer.",
        "private": True,
    },
    "code_of_conduct": {
        "links": [
            "<https://app.notion.com/p/rasa/Rasa-Code-of-Conduct-ab7c7ec6404a4f43adbdb38eafe1316d|Rasa Code of Conduct>",
        ],
        "referral": "Further questions go to People Ops.",
    },
    "intellectual_property": {
        "links": [
            "<https://app.notion.com/p/rasa/Intellectual-Property-Rights-c1e942f0fdb843abba324930d288590b|Intellectual Property Rights>",
        ],
        "referral": "Further questions go to #security.",
    },
    "data_deletion": {
        "links": [
            "<https://app.notion.com/p/rasa/Handling-Data-Deletion-Requests-1f5b9c0d544a80e2aa27cff4bef1b830?v=1f4b9c0d544a803a8061000c061b8dc3|Handling Data Deletion Requests>",
        ],
        "referral": "Further questions go to #security.",
    },
    "security_responsibilities": {
        "links": [
            "<https://app.notion.com/p/rasa/Information-Security-Responsibilities-a612570f15b94b91ab977f1df390537a|Information Security Responsibilities>",
        ],
        "referral": "That page lists who is responsible for each security area.",
    },
    "export_control": {
        "links": [
            "<https://app.notion.com/p/Product-Export-Classification-Policy-33cb9c0d544a8140af7ef4b146104da7|Product Export Classification Policy>",
        ],
        "referral": (
            "Legal must confirm the destination and customer before the deal "
            "moves forward. Ask the requester to ping @Mat with the country, "
            "customer or partner, and what they want to sell."
        ),
        "never_decide": True,
    },
    "legal_support": {
        "links": [],
        "referral": (
            "Mat Searle is Rasa's internal legal contact and works with external "
            "counsel. Ask the requester to ping @Mat with relevant context."
        ),
    },
    "ethics_officer": {
        "links": [
            "<https://app.notion.com/p/rasa/Ethics-Officer-at-Rasa-c1a4a11dae9844e5a162285c940267ad|Ethics Officer at Rasa>",
        ],
        "referral": "The current Ethics Officer details are on that page.",
    },
}


@tool(
    description=(
        "Return the exact approved link and referral for a link-only Rasa policy."
    )
)
async def get_policy_link(
    topic: str,
    context: ToolContext = None,
) -> ToolResult:
    """Get one approved policy response.

    Args:
        topic: One of anti_bribery, anti_slavery, whistleblower,
            code_of_conduct, intellectual_property, data_deletion,
            security_responsibilities, export_control, legal_support, or
            ethics_officer.
    """
    policy = _POLICIES.get(topic)
    if policy is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "instruction": "Do not guess. Say this policy link is unavailable.",
            }
        )
    return ToolResult(
        llm_response={
            "ok": True,
            "topic": topic,
            **policy,
            "instruction": (
                "Reply in one short message using only referral and links. Paste "
                "each link exactly. Do not summarize or interpret the policy, "
                "invent details or contacts, or ask for private details."
            ),
        }
    )
