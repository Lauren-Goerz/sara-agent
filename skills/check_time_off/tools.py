"""Mock BambooHR time-off tools for the check_time_off skill."""

from __future__ import annotations

import sys
import uuid
from datetime import date
from pathlib import Path

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.hr_mocks import (  # noqa: E402
    TIME_OFF_BALANCES,
    TIME_OFF_TYPES,
    find_employees,
    get_employee,
)


@tool(description="Resolve an employee name to a BambooHR directory id.")
async def resolve_employee(query: str, context: ToolContext = None) -> ToolResult:
    """Find employees by name for time-off flows.

    Args:
        query: Employee name or email fragment.
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
                    "department": e["department"],
                    "workEmail": e["workEmail"],
                }
                for e in matches
            ],
        }
    )


@tool(description="List company time-off types available to request.")
async def list_time_off_types(context: ToolContext = None) -> ToolResult:
    """Return BambooHR List Time Off Types–shaped mock data."""
    return ToolResult(
        llm_response={
            "ok": True,
            "defaultHoursPerDay": 8,
            "timeOffTypes": TIME_OFF_TYPES,
        }
    )


@tool(
    description=(
        "Get time-off balances for the selected employee. Call only after "
        "selected_employee_id is set."
    )
)
async def get_time_off_balance(context: ToolContext = None) -> ToolResult:
    """Return BambooHR Get Time Off Balance–shaped mock data."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    employee_id = context.memory.get("selected_employee_id")
    if not employee_id:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_employee_selected",
                "hint": "Resolve and select an employee first.",
            }
        )

    employee = get_employee(str(employee_id))
    balances = TIME_OFF_BALANCES.get(str(employee_id))
    if employee is None or balances is None:
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
            "employeeId": employee_id,
            "employeeName": employee["displayName"],
            "asOf": date.today().isoformat(),
            "balances": balances,
        }
    )


@tool(
    description=(
        "Submit a time-off request after the user confirms. Requires "
        "request_confirmed in memory."
    )
)
async def submit_time_off_request(
    start: str,
    end: str,
    time_off_type: str,
    context: ToolContext = None,
) -> ToolResult:
    """Create a mock BambooHR time-off request.

    Args:
        start: Start date YYYY-MM-DD.
        end: End date YYYY-MM-DD.
        time_off_type: Vacation, Sick, or Personal.
    """
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    if not context.memory.get("request_confirmed"):
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_confirmed",
                "hint": "Confirm the request with the user first.",
            }
        )

    employee_id = context.memory.get("selected_employee_id")
    employee = get_employee(str(employee_id)) if employee_id else None
    if employee is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_employee_selected",
            }
        )

    type_match = next(
        (
            t
            for t in TIME_OFF_TYPES
            if t["name"].lower() == time_off_type.strip().lower()
        ),
        None,
    )
    if type_match is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unknown_type",
                "hint": "Use Vacation, Sick, or Personal.",
                "availableTypes": TIME_OFF_TYPES,
            }
        )

    request_id = f"tor_{uuid.uuid4().hex[:8]}"
    context.memory.set("last_request_id", request_id)
    return ToolResult(
        llm_response={
            "ok": True,
            "status": "requested",
            "requestId": request_id,
            "employeeId": employee["id"],
            "employeeName": employee["displayName"],
            "start": start,
            "end": end,
            "timeOffType": type_match["name"],
            "timeOffTypeId": type_match["id"],
            "note": "Demo request — not sent to live BambooHR.",
        }
    )
