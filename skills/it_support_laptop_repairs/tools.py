"""Fetch laptop repair guidance from the designated Notion IT page."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

APPLE_SUPPORT_URL = "https://getsupport.apple.com/solutions"

# Used only if Notion is temporarily unavailable.
_FALLBACK_CONTENT = """
We at Rasa work on Macbooks. These are strong and robust piece of electronics.
However, there is a possibility that at some point due to wear and tear or an
accident, it might need a repair.

In that case, the following steps need to be followed -
- 1st step:- Can you do a quick check by clicking on the apple icon on the top
  left and do the initial contact with Apple support. Smaller problems are fixed
  on the phone itself.
- https://getsupport.apple.com/solutions
- If you click on details , you would reach the help page.
- 2nd step :- If the Apple support team is unable to rectify the problem on
  phone, they will guide you with regards to possible repairs options
- 3rd Step :- Inform Rajesh and he would suggest one of the following solutions -

## for Berlin based GmbH employees
- Inform Rajesh about the problem
- Exchange your Mac with a substitute Mac from the office
- Your Mac would be sent for repairs and once it’s fixed, we shall return it to you
- However, if you are satisfied with the replaced Mac, we shall keep the repaired
  one as a substitute and make the changes in the asset form in Bamboo HR

## for Macs from our leasing partners
- Inform Rajesh about the problem and he will contact them
- They shall arrange to send you a replacement and give you instructions about
  collecting the problematic Mac.

## for Macs purchased directly from Apple or resellers Globally
- Coordinate with the local authorised Apple repair center and find out the
  approx cost of repairing
- Inform Rajesh about the cost and if worth it, then it shall be agreed to get
  it repaired
- Send your Macbook for repairs
- We shall try to send you a replacement.
- Put in the invoice for reimbursement
- You shall be reimbursed
""".strip()

_INSTRUCTION = (
    "Guide the employee using source_content only. Start with Apple Support "
    "(apple_support_url) unless they already completed it, then Inform "
    "Rajesh, then the Berlin GmbH / leasing / purchased path that matches "
    "them. Ask one clarifying question if the Mac category is unclear. Do "
    "not invent warranty, cost, or timeline details. Do not tag Rajesh "
    "yourself. Always share source_url. If used_fallback is true, still "
    "treat this as the approved process."
)


@tool(
    description=(
        "Fetch Rasa work MacBook / laptop repair process from the designated "
        "Notion IT page. Call for every laptop repair or substitute-Mac request."
    )
)
async def get_laptop_repair_guidance(context: ToolContext = None) -> ToolResult:
    """Return live laptop repair guidance, with a static fallback if needed."""
    payload = await notion_sources.load(
        "laptop_repairs",
        char_limit=8000,
        fallback_content=_FALLBACK_CONTENT,
    )
    payload["apple_support_url"] = APPLE_SUPPORT_URL
    payload["instruction"] = _INSTRUCTION
    return ToolResult(llm_response=payload)
