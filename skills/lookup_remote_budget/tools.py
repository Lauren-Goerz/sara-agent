"""Fetch Rasa remote / home-office budget guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

# Snapshot used when the Notion page is not shared with Sara's integration.
# Sourced from the Remote Budget - 2026 export (as of August 11, 2026).
_FALLBACK_CONTENT = """
# Remote Budget - 2026
(Policy snapshot as of August 11, 2026 - always confirm on the Notion page.)

## Summary
| Option | One-time payment | Monthly payment |
| --- | --- | --- |
| Berlin Office | €800 | Internet expense |
| Co-working space | $900 // €800 // £870 // 1190 CAD (or equivalent) | Flex seat cost |
| Home only | $1,800 // €1,600 // £1,450 // CAD 2,475 (or equivalent) | Utility cost |

## How to work with this document
1. Read through all 3 options of remote work and decide which one would work
   best for you.
2. Add your choice to BambooHR in the "Remote Work Style" column (Job tab).
   People Ops receives a request and adds the available home office budget in
   the "Home Office Budget" field.
3. Your home office budget is based on whether you will work from home only
   or from somewhere else.
4. You have 03 months from your start date to access your one-time payment
   funds from the Home office budget options. After that the budget will
   lapse.

## Option 1: You work from our Berlin Office
New Employee Home Office Budget: €800 to buy equipment to improve your home
office setup for days when you are not working from the office. Use within
three months or lose it.

How: Purchase items and submit invoices for reimbursement through Payhawk.
Choose "Office - Home Office - New Hire Equipment Budget".

Internet: We will reimburse your monthly internet costs. Upload your invoice
every month and use the category "Home Office Internet".

## Option 2: Hot desk membership at a local co-working space
New Employee Home Office Budget: $900 // €800 // £870 // 1190 CAD for
equipment for days you are not at the co-working space. Use within three
months or lose it.

How: Purchase items and submit invoices through Payhawk. Choose
"Office - Home Office" under Expense Category.

Flex desk at a co-working space:
- Each month, Rasa reimburses Flex desk subscription at a local co-working
  space up to a max of 250 Euros or equivalent.
- You contract directly with the co-working space. Rasa does not contract or
  pay the space directly.
- Example: seat for 150 euros/month -> full reimbursement; seat for 300
  euros/month -> reimburse 250 euros (the max).
- Submit the invoice monthly via Payhawk. Choose "Office Co-working".

Good to know: Berlin-based people who prefer co-working instead of the
office also fall into this category. If you pick this option and are based
in Berlin you will not get reimbursed for any internet costs at home.

## Option 3: You will only work from home
1. New Employee Home Office Budget: $1,800 // €1,600 // £1,450 // CAD 2,475
   (choose the relevant currency of your home office location). Use within
   three months or lose it.
   How: Purchase items and submit invoices through Payhawk. Choose
   "Office - Home Office - New Hire Equipment Budget".

2. Monthly Utility Costs:
   Rasa covers monthly expenses around your work (e.g. internet, cell phone,
   office supplies etc.).
   How: You receive a gross monthly allowance in addition to your salary
   every month. It is taxed based on regional laws. No receipts needed.
   - US: $175 / month
   - Canada: CAD 240 / month
   - Europe: €160 / month
   - UK: £135 / month

Good to know: If you are based in Berlin and will work 90% of your work time
from home instead of the office, you fall into this category as well. Be
realistic; if unsure, go with Option 1.

## Switching from full home office to co-working (within a year of availing
full home office option)
- Stop getting paid monthly utility costs.
- Instead get reimbursed for a Flex seat in the co-working office.
- One-time Home office allowance reduced from 1600 euros to 800 euros
  equivalent.
- If you already spent more than 800 euros, Rasa debits the difference from
  your coworking allowance.
Example: Used 1200 of 1600 euros, then switch to coworking at 200 euros/mo.
Refund 400 euros (1200 - 800). Rasa would not pay the next 2 months of
coworking fees (2 x 200 = 400), and would also stop the monthly utility
cost. From the 3rd month, submit the 200 euro coworking invoice.
Inform Finance soonest and once agreed update BambooHR.

## Part-time employees / interns / working students
- Part-time employees can choose one of the options above, but budget is 80%
  of full-time.
- Working students and interns who stay at Rasa for more than 6 months and
  are based in Berlin: initial Home Office of 400 EUR. Payhawk category
  "Office - Home Office".
- Interns staying 3-6 months: basic equipment (mouse, keyboard, adapters) up
  to a reasonable amount of 200 EUR.
- Part-time / working students who work only from home (option 3) monthly
  allowance:
  - US: $87.5/mo
  - Europe: €77.5/mo
  - UK: £67.5/mo
- In some cases full-time contractors receive 100% of the remote budget -
  reach out to People.

## Tracking / principles
- Track purchases via spreadsheet copy or Payhawk filters.
- Act in Rasa's best interest; don't spend just because there's a budget.

## FAQ highlights
- Keyboard/mouse: yes, buy with HO budget. Company laptop is provided
  separately and is not part of HO expenses.
- You track your own HO budget expenses.
- Leaving Rasa: keep HO-budget equipment; only ship back laptop and charger.
- Already bought after hire date: yes, reimburse with invoice within budget.
- What can be expensed: desk, chair, bookshelf, AC/fan, plants, headphones,
  monitor, etc. - must connect to office setup.
- Spend window: 03 months from start date.
- Stationery (paper, pens, notebooks): home-only uses monthly allowance;
  Berlin office check office stock or ask Rajesh.
- Partial reimbursement vs invoice: request can be less than invoice amount;
  correct auto-scan and add a short note.
- NOT entitled: interns under 6 months don't get HO budget (but up to 200 EUR
  necessary tech).
- Decide remote option within 15 days of joining.
- New office in your city: not obligated to go; can still work 100% from home.
- Switching styles: contact manager and update Remote Work Style in BambooHR.
- Payhawk categories:
  - Office - Home Office: New Hire Equipment Budget
  - Office - Home Office Internet: when coming to Berlin Office
  - Office - Minor Equipment: replace faulty minor hardware
- Broken electronics bought 2-3 years ago from HO budget: contact Rajesh.

Questions: reach out to Rajesh, Everett or Sarah.
""".strip()

_INSTRUCTION = (
    "Answer the remote/home-office budget question using only "
    "source_content. Keep it short and Slack-friendly. Use exact amounts, "
    "currencies, and Payhawk categories - never invent or combine them. "
    "Always state that this is the policy as of August 11, 2026 and tell "
    "them to double-check source_url for any updates. Always share "
    "source_url. If used_fallback is true, still treat source_content as "
    "the approved snapshot for that date."
)


@tool(
    description=(
        "Fetch Rasa Remote Budget 2026 / home office budget guidance "
        "(Berlin office, co-working, home-only). Uses Notion when shared, "
        "otherwise a baked-in August 11 2026 snapshot. Call for every "
        "remote-budget or home-office budget question."
    )
)
async def get_remote_budget_guidance(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return remote budget guidance for employee questions.

    Args:
        query: The remote-budget topic (e.g. coworking flex desk, home-only
            utility, Berlin office internet, part-time budget).
    """
    payload = await notion_sources.load(
        "remote_budget",
        query=query,
        char_limit=8000,
        fallback_content=_FALLBACK_CONTENT,
    )
    payload["policy_as_of"] = "August 11, 2026"
    payload["instruction"] = _INSTRUCTION
    return ToolResult(llm_response=payload)
