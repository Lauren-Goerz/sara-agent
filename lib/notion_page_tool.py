"""Factory for skills that read one allowlisted Notion page.

Each skill still owns a named Maestro tool (so the LLM cannot pick another
page). Fetch, cache, and trimming stay in notion_sources; this module only
stamps the skill's answer rules onto that payload.
"""

from __future__ import annotations

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

from lib import notion_sources


def notion_page_tool(
    *,
    name: str,
    source: str,
    description: str,
    docstring: str,
    instruction: str,
    failure_instruction: str,
    query_doc: str | None = "The topic they asked about.",
    query_required: bool = False,
    default_query: str = "",
    char_limit: int | None = None,
):
    """Build a @tool that loads one registered Notion source.

    Args:
        name: Tool name the skill.md already calls (function name).
        source: Key in notion_sources.SOURCES.
        description: Shown to the LLM in the tool schema.
        docstring: Tool docstring; query_doc is appended as Args when used.
        instruction: Stamped on a successful payload.
        failure_instruction: Stamped when the page cannot be loaded.
        query_doc: Per-argument description. Pass None to omit the query arg.
        query_required: If True, the LLM must pass query (no default).
        default_query: Used when there is no query arg, or query is empty.
        char_limit: Optional override for notion_sources.load.
    """
    if source not in notion_sources.SOURCES:
        raise KeyError(f"Unknown Notion source {source!r}")

    load_kwargs: dict = {}
    if char_limit is not None:
        load_kwargs["char_limit"] = char_limit

    async def _load(query: str) -> ToolResult:
        payload = await notion_sources.load(
            source,
            query=query,
            **load_kwargs,
        )
        payload["instruction"] = (
            instruction if payload.get("ok") else failure_instruction
        )
        return ToolResult(llm_response=payload)

    if query_doc is None:
        async def _tool(context: ToolContext = None) -> ToolResult:
            return await _load(default_query)

        _tool.__doc__ = docstring
    elif query_required:
        async def _tool(  # type: ignore[misc]
            query: str,
            context: ToolContext = None,
        ) -> ToolResult:
            return await _load(query or default_query)

        _tool.__doc__ = f"{docstring}\n\n    Args:\n        query: {query_doc}"
    else:
        async def _tool(  # type: ignore[misc]
            query: str = "",
            context: ToolContext = None,
        ) -> ToolResult:
            return await _load(query or default_query)

        _tool.__doc__ = f"{docstring}\n\n    Args:\n        query: {query_doc}"

    _tool.__name__ = name
    _tool.__qualname__ = name
    return tool(description=description)(_tool)
