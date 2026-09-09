"""Fetch Rasa business travel policy guidance from Notion."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

# Used when the Notion page is not shared with Sara's integration.
# Sourced from the Business Travel export (Aug 2026).
_FALLBACK_CONTENT = """
# Business Travel

Disclaimer: When it comes to spending company money, we expect everyone to
act in the company's best interest. If you're unsure, please reach out to
your manager for guidance.

Please get the trip and the cost (including any aberrations) approved by
your manager before you book. Later at the time of reimbursement in Payhawk
it would go to your manager for approvals. We prefer you book using your
personal credit card and later claim the amount in Payhawk.

Important:
- Except for per diem, all claims for reimbursement need to be supported by
  proper invoices/receipts. We follow the simple rule - no invoices/receipts,
  no payments.
- Approved reimbursements must be submitted within 60 days of the incurred
  expense, or those expenses may not be reimbursed.

## Flight tickets
- Fly economy class as a practice.
- Add all flight details / times to your calendar - in this way everyone can
  see when you are not available.
- If there is an additional cost due to your personal preferences for seat,
  extra luggage or better time, please get it approved by your Manager.
- If you book for somebody else - discuss the details with them before final
  booking.
- If you want to stay longer at a place for personal reasons, please make sure
  the flight is not more expensive than it would have been if you go back
  immediately after your Rasa-related reason to go to that place.

## Local Travel
Public Transport is the default mode to travel within a city. They are
generally fast and economical.

Exceptions to this rule are:
- If the public transport is not available e.g. if there is a strike
- If you are traveling as a group and its more economical for you all to share
  an Uber
- If it takes twice as long to travel

Prefer Uber over a regular taxi.

## Lodging
- Book reasonable hotels or AirBnB. Consider the location - if you need to take
  a taxi to the meeting because your hotel is very far away maybe it's better to
  take a bit more expensive one but in the city centre.
- The average costs hovers around 120 euros for many European cities.
- For short trips hotels are usually better & easier.
- If you want to stay longer at a place for personal reasons, please pay the
  additional nights out of your pocket and please also make sure that it's
  strictly separated from any invoices that go to Rasa.

## Per Diems / Meals and Food while traveling (for everyone)
- Per Diem cannot be clubbed with any other personal meal voucher/invoices or
  direct meal reimbursements to avoid duplication. No invoices are required for
  per diem claim.
- We work with per diems, that means that you get a certain amount of money per
  day to cover the extra expenses you have during the trip. Find the rates for
  the different countries in Payhawk (rates are set-up in Payhawk directly as
  you submit your request).
- For every full day, you get the full amount. You get everything paid to your
  bank account by the end of the month in which you submitted the reimbursement
  request.
- If any meals are provided by the company (e.g. breakfast in the hotel) this
  has to be deducted from the total per diem (20% less for breakfast, 40% each
  for Lunch or Dinner).
- Maximum reimbursement permissible per day would be based on the per diem
  card / rate card in Payhawk.
- Any expense above the said limit would have to be borne by the individual.
- Per diem rate spreadsheet:
  https://docs.google.com/spreadsheets/d/1PI7II5i1Qsz5WT3jgHkwA1f1edNbWcf3aChcBCqdajA/edit#gid=406947408

## Meals - Terminology
- Personal Meal: A meal expense incurred by you when dining alone or with other
  Rasa employees, buying water or food at the airport or at the supermarket
  while on a business trip.
- Team Meals: For meals with Rasa Employees while traveling or getting together
  for a team meeting, including drinks, need to be approved by your manager
  (i.e. the budget owner). Approval is needed by Finance (Mat) for any meal
  inclusive of drinks over the full day limit on the rate card.
- Business Meal: A meal taken with clients, partners, candidates, or associates
  during which a specific business discussion takes place in an atmosphere
  conducive to business and which is reimbursable to a reasonable amount (total
  per day found on the rate card, recommended not to go over). When you pay a
  business meal, you have to add place, date, purpose and names of the guest.
- Dinner with non Rasa Employees or non customers/prospects are not business
  expenses and will not be reimbursed.

## Travel Insurance
We have travel insurance for all Rasa employees across entities. Chubb is our
insurance partner and it uses AXA Assistance to provide support.
- Policy No: 9908-63-59 - for all Inc, Ltd, SAS & LLC employees
- Policy No: DEBBBT03167 for GmbH employees
For more details, see the Travel Insurances 2026 page / policy_travel_insurance.

## Planning to extend your travel?
If you wish to extend your travel to include some personal time, either by
bringing a partner or by adding travel time to the end of your stay, do the
following:
1. Calculate the additional cost added by the detour added to your travel.
2. Subtract this additional amount and put in the reduced amount for
   reimbursement.
3. Include the full invoice and the details in the description when you submit
   your expense for approval and reimbursement.

Example: The total travel cost for you and a partner is $5000 USD. The share
for the Rasa employee is USD $2500. If you do an additional detour not part of
the itinerary and it costs $1000 USD, then bill Rasa for only USD $1500
($2500 - $1000).
""".strip()

_INSTRUCTION = (
    "Answer the business travel question using only source_content. Keep it "
    "short and Slack-friendly. Use exact flight class, transport preference, "
    "hotel guidance, per diem, and receipt/expense rules from the page - "
    "never invent amounts or exceptions. For Uber/taxi questions, cite the "
    "Local Travel default (public transport) and the listed exceptions only - "
    "do not invent early-flight or airport exceptions that are not written "
    "there. Always share source_url. If used_fallback is true, still treat "
    "source_content as the approved policy. If they ask about insurance "
    "cover/claims in depth, point them to policy_travel_insurance / the "
    "Travel Insurances 2026 page."
)


@tool(
    description=(
        "Fetch Rasa's Business Travel policy from Notion (with a baked-in "
        "fallback). Call for flight class, transport preference, hotel "
        "budgets, per diem vs receipts, Uber/taxi vs public transport, or "
        "other work-trip booking and spend rules."
    )
)
async def get_business_travel_policy(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Return the live business travel policy for employee questions.

    Args:
        query: The travel topic (e.g. economy flights, hotel budget,
            per diem vs receipts, Uber to airport, public transport).
    """
    payload = await notion_sources.load(
        "business_travel",
        query=query,
        fallback_content=_FALLBACK_CONTENT,
    )
    payload["instruction"] = _INSTRUCTION
    return ToolResult(llm_response=payload)
