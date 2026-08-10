"""Shared mock HR/Ops data shaped like BambooHR, Notion, and Slack payloads.

Swap these for live API clients later using env vars:
  BAMBOO_API_KEY, BAMBOO_COMPANY_DOMAIN
  NOTION_API_KEY, NOTION_POLICIES_DB_ID
  SLACK_BOT_TOKEN
"""

from __future__ import annotations

# BambooHR Get Employees Directory–shaped records (directory fields only).
# See: https://documentation.bamboohr.com/reference/get-employees-directory
EMPLOYEES: list[dict] = [
    {
        "id": "101",
        "displayName": "Alex Rivera",
        "firstName": "Alex",
        "lastName": "Rivera",
        "jobTitle": "People Ops Manager",
        "department": "People",
        "location": "Berlin",
        "workEmail": "alex.rivera@rasa.com",
        "workPhone": "+49 30 555-0101",
        "supervisor": "Jordan Lee",
        "supervisorId": "100",
    },
    {
        "id": "102",
        "displayName": "Sam Okonkwo",
        "firstName": "Sam",
        "lastName": "Okonkwo",
        "jobTitle": "Senior Product Manager",
        "department": "Product",
        "location": "London",
        "workEmail": "sam.okonkwo@rasa.com",
        "workPhone": "+44 20 555-0102",
        "supervisor": "Jordan Lee",
        "supervisorId": "100",
    },
    {
        "id": "103",
        "displayName": "Priya Shah",
        "firstName": "Priya",
        "lastName": "Shah",
        "jobTitle": "Staff Engineer",
        "department": "Engineering",
        "location": "Remote — EU",
        "workEmail": "priya.shah@rasa.com",
        "workPhone": None,
        "supervisor": "Casey Nguyen",
        "supervisorId": "104",
    },
    {
        "id": "104",
        "displayName": "Casey Nguyen",
        "firstName": "Casey",
        "lastName": "Nguyen",
        "jobTitle": "Engineering Manager",
        "department": "Engineering",
        "location": "San Francisco",
        "workEmail": "casey.nguyen@rasa.com",
        "workPhone": "+1 415 555-0104",
        "supervisor": "Jordan Lee",
        "supervisorId": "100",
    },
    {
        "id": "100",
        "displayName": "Jordan Lee",
        "firstName": "Jordan",
        "lastName": "Lee",
        "jobTitle": "VP Operations",
        "department": "Operations",
        "location": "Berlin",
        "workEmail": "jordan.lee@rasa.com",
        "workPhone": "+49 30 555-0100",
        "supervisor": None,
        "supervisorId": None,
    },
]

DIRECTORY_FIELDS = [
    {"id": "displayName", "type": "text", "name": "Display Name"},
    {"id": "firstName", "type": "text", "name": "First Name"},
    {"id": "lastName", "type": "text", "name": "Last Name"},
    {"id": "jobTitle", "type": "list", "name": "Job Title"},
    {"id": "department", "type": "list", "name": "Department"},
    {"id": "location", "type": "list", "name": "Location"},
    {"id": "workEmail", "type": "email", "name": "Work Email"},
    {"id": "workPhone", "type": "text", "name": "Work Phone"},
    {"id": "supervisor", "type": "text", "name": "Supervisor"},
]

# BambooHR time-off balances keyed by employee id.
# Shape inspired by Get Time Off Balance:
# https://documentation.bamboohr.com/reference/get-time-off-balance
TIME_OFF_BALANCES: dict[str, list[dict]] = {
    "101": [
        {"timeOffType": "Vacation", "timeOffTypeId": "1", "units": "days", "balance": "12.5"},
        {"timeOffType": "Sick", "timeOffTypeId": "2", "units": "days", "balance": "5.0"},
    ],
    "102": [
        {"timeOffType": "Vacation", "timeOffTypeId": "1", "units": "days", "balance": "8.0"},
        {"timeOffType": "Sick", "timeOffTypeId": "2", "units": "days", "balance": "3.5"},
    ],
    "103": [
        {"timeOffType": "Vacation", "timeOffTypeId": "1", "units": "days", "balance": "18.0"},
        {"timeOffType": "Sick", "timeOffTypeId": "2", "units": "days", "balance": "6.0"},
    ],
    "104": [
        {"timeOffType": "Vacation", "timeOffTypeId": "1", "units": "days", "balance": "10.0"},
        {"timeOffType": "Sick", "timeOffTypeId": "2", "units": "days", "balance": "4.0"},
    ],
    "100": [
        {"timeOffType": "Vacation", "timeOffTypeId": "1", "units": "days", "balance": "20.0"},
        {"timeOffType": "Sick", "timeOffTypeId": "2", "units": "days", "balance": "7.0"},
    ],
}

TIME_OFF_TYPES = [
    {"id": "1", "name": "Vacation", "units": "days"},
    {"id": "2", "name": "Sick", "units": "days"},
    {"id": "3", "name": "Personal", "units": "days"},
]

# Notion-shaped handbook pages (search results + page bodies).
POLICY_PAGES: list[dict] = [
    {
        "id": "page_pto",
        "title": "Time Off & Leave Policy",
        "url": "https://notion.so/rasa/time-off-leave",
        "summary": (
            "Full-time employees accrue vacation based on tenure. Request time "
            "off in BambooHR at least 2 weeks in advance for planned leave. "
            "Sick leave does not require advance notice."
        ),
        "body": (
            "## Accrual\n"
            "- 0–2 years: 20 vacation days/year\n"
            "- 3+ years: 25 vacation days/year\n"
            "- Sick: 10 days/year\n\n"
            "## How to request\n"
            "Submit in BambooHR. Managers should approve within 3 business days.\n\n"
            "## Public holidays\n"
            "Observed per your work location calendar."
        ),
        "tags": ["pto", "vacation", "sick", "leave", "time off"],
    },
    {
        "id": "page_remote",
        "title": "Remote & Hybrid Work Guidelines",
        "url": "https://notion.so/rasa/remote-hybrid",
        "summary": (
            "Rasa supports remote and hybrid work. Core collaboration hours "
            "are 10:00–16:00 in your local timezone. Office seats are bookable."
        ),
        "body": (
            "## Expectations\n"
            "- Be reachable on Slack during core hours\n"
            "- Update your calendar with working location\n"
            "- Attend all-hands live when possible\n\n"
            "## Expenses\n"
            "Home-office stipend details are in the Benefits page."
        ),
        "tags": ["remote", "hybrid", "wfh", "work from home", "office"],
    },
    {
        "id": "page_expenses",
        "title": "Expense & Travel Policy",
        "url": "https://notion.so/rasa/expenses-travel",
        "summary": (
            "Submit expenses within 30 days via the finance tool. Travel "
            "over €500 needs manager pre-approval."
        ),
        "body": (
            "## Eligible expenses\n"
            "- Work travel, client meals (within per-diem), conference tickets\n\n"
            "## Not covered\n"
            "- Personal commuting, home internet beyond stipend\n\n"
            "## Process\n"
            "Attach receipts. Finance reviews weekly."
        ),
        "tags": ["expense", "expenses", "travel", "reimbursement", "per diem"],
    },
    {
        "id": "page_onboarding",
        "title": "New Hire Onboarding Checklist",
        "url": "https://notion.so/rasa/onboarding",
        "summary": (
            "Day-1 setup: Slack, BambooHR profile, laptop, and buddy intro. "
            "Complete compliance training in week one."
        ),
        "body": (
            "## Before day 1\n"
            "- Complete BambooHR paperwork\n"
            "- Confirm start date and equipment shipment\n\n"
            "## Week 1\n"
            "- Join #general and your team channel\n"
            "- Meet your buddy\n"
            "- Finish security & compliance modules"
        ),
        "tags": ["onboarding", "new hire", "checklist", "first day"],
    },
]

# Slack-shaped channels for mock posts.
SLACK_CHANNELS: list[dict] = [
    {"id": "C_GENERAL", "name": "general", "is_private": False},
    {"id": "C_PEOPLE", "name": "people-ops", "is_private": False},
    {"id": "C_ENG", "name": "engineering", "is_private": False},
    {"id": "C_ANNOUNCE", "name": "announcements", "is_private": False},
]


def find_employees(query: str) -> list[dict]:
    """Case-insensitive match on name, email, title, department, or location."""
    q = query.strip().lower()
    if not q:
        return []
    matches: list[dict] = []
    for emp in EMPLOYEES:
        haystack = " ".join(
            str(emp.get(k) or "")
            for k in (
                "displayName",
                "firstName",
                "lastName",
                "jobTitle",
                "department",
                "location",
                "workEmail",
                "supervisor",
            )
        ).lower()
        if q in haystack:
            matches.append(emp)
    return matches


def get_employee(employee_id: str) -> dict | None:
    return next((e for e in EMPLOYEES if e["id"] == str(employee_id)), None)


def search_policies(query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    results: list[dict] = []
    for page in POLICY_PAGES:
        blob = " ".join(
            [page["title"], page["summary"], " ".join(page["tags"])]
        ).lower()
        if any(token in blob for token in q.split()) or q in blob:
            results.append(
                {
                    "id": page["id"],
                    "title": page["title"],
                    "url": page["url"],
                    "summary": page["summary"],
                }
            )
    return results


def get_policy_page(page_id: str) -> dict | None:
    return next((p for p in POLICY_PAGES if p["id"] == str(page_id)), None)


def find_channel(name_or_id: str) -> dict | None:
    key = name_or_id.strip().lstrip("#").lower()
    for ch in SLACK_CHANNELS:
        if ch["id"].lower() == key or ch["name"].lower() == key:
            return ch
    return None
