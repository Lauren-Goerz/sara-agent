#!/usr/bin/env python
"""Report which registered Notion sources Sara can actually read.

A source that fails here makes its skill fall back to "here is the link"
instead of answering. Usually the page just needs sharing with the Sara-Agent
integration (Notion page ⋯ → Connections → Sara-Agent).

    source .venv/bin/activate
    python scripts/check_notion_access.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_sources  # noqa: E402

# Notion rate-limits around three requests per second and one source costs
# several calls, so walk the registry slowly rather than in parallel.
_PAUSE_SECONDS = 0.5


async def main() -> int:
    ok: list[str] = []
    failed: list[tuple[str, str, str]] = []

    for key, source in notion_sources.SOURCES.items():
        payload = await notion_sources.load(key, query="overview")
        if payload.get("ok") and not payload.get("used_fallback"):
            ok.append(key)
        else:
            failed.append((key, source.title, str(payload.get("error"))))
        await asyncio.sleep(_PAUSE_SECONDS)

    total = len(notion_sources.SOURCES)
    print(f"readable: {len(ok)}/{total}")

    if failed:
        print("\nnot readable — share these with the Sara-Agent integration:")
        for key, title, error in failed:
            print(f"  {key:24s} {title}")
            print(f"  {'':24s}   {notion_sources.SOURCES[key].url}  ({error})")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
