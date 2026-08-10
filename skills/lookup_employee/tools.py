"""Mock BambooHR directory lookup for the lookup_employee skill."""

from __future__ import annotations

import sys
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

# Allow importing shared mocks from project lib/
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.hr_mocks import (  # noqa: E402
    DIRECTORY_FIELDS,
    find_employees,
    get_employee,
)


@tool(description="Search the BambooHR company directory by name, team, title, or email.")
async def search_directory(query: str, context: ToolContext = None) -> ToolResult:
    """Search mock directory records.

    Args:
        query: Name, email, department, title, or location fragment.
    """
    matches = find_employees(query)
    return ToolResult(
        llm_response={
            "ok": True,
            "query": query,
            "match_count": len(matches),
            "employees": [
                {
                    "id": e["id"],
                    "displayName": e["displayName"],
                    "jobTitle": e["jobTitle"],
                    "department": e["department"],
                    "location": e["location"],
                    "workEmail": e["workEmail"],
                }
                for e in matches
            ],
            "hint": (
                None
                if matches
                else "No directory matches. Ask for a different name or team."
            ),
        }
    )


@tool(
    description=(
        "Return full directory details for the selected employee. Call only "
        "after selected_employee_id is set in skill memory."
    )
)
async def get_employee_details(context: ToolContext = None) -> ToolResult:
    """Return BambooHR directory-shaped details for the selected employee."""
    if context is None:
        return ToolResult(
            llm_response={"ok": False, "error": "no_context"}
        )

    employee_id = context.memory.get("selected_employee_id")
    if not employee_id:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_employee_selected",
                "hint": "Search the directory and select someone first.",
            }
        )

    employee = get_employee(str(employee_id))
    if employee is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unknown_employee",
                "employee_id": employee_id,
            }
        )

    context.memory.set("selected_employee_name", employee["displayName"])
    return ToolResult(
        llm_response={
            "ok": True,
            "fields": DIRECTORY_FIELDS,
            "employee": employee,
        }
    )
