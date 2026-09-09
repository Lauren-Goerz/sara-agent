"""Answer product proof-point questions from the Notion PDF."""

from __future__ import annotations

import os
import re
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
import structlog
from pypdf import PdfReader
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult
from slack_sdk.web.async_client import AsyncWebClient

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_client  # noqa: E402

structlogger = structlog.get_logger()

PROOF_POINTS_PAGE_ID = "33eb9c0d544a80839f59e01cfa4c2c0a"
PROOF_POINTS_PAGE_URL = (
    "https://app.notion.com/p/rasa/"
    "Product-Proof-Points-33eb9c0d544a80839f59e01cfa4c2c0a"
)
_MAX_PDF_BYTES = 15 * 1024 * 1024
_FAILURE_INSTRUCTION = (
    "Do not invent proof points, customer metrics, analyst quotes, or "
    "deployment timelines. Share source_url and ask the person to open the "
    "Notion page / PDF themselves."
)


def _latest_slack_destination(context: ToolContext) -> tuple[str, str | None] | None:
    for event in reversed(context.events):
        if getattr(event, "input_channel", None) != "slack":
            continue
        metadata = getattr(event, "metadata", None) or {}
        channel = metadata.get("out_channel")
        if channel:
            return str(channel), metadata.get("thread_id")
    return None


def _filename_from_url(url: str, fallback: str = "Rasa_Proof_Points.pdf") -> str:
    path = unquote(urlparse(url).path)
    name = Path(path).name
    if name.lower().endswith(".pdf"):
        return name
    return fallback


def _pick_pdf(attachments: list[dict]) -> dict | None:
    pdfs = [
        item
        for item in attachments
        if str(item.get("url") or "").lower().endswith(".pdf")
        or "pdf" in str(item.get("name") or "").lower()
        or ".pdf" in str(item.get("url") or "").lower()
    ]
    if pdfs:
        return pdfs[0]
    for item in attachments:
        if item.get("kind") == "file" and item.get("url"):
            return item
    return None


def _extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    chunks: list[str] = []
    seen: set[str] = set()
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        fingerprint = re.sub(r"\s+", " ", text[:400]).lower()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        chunks.append(f"--- page {index} ---\n{text}")
    return "\n\n".join(chunks).strip()


@tool(
    description=(
        "Fetch Rasa product proof points from the designated Notion page PDF: "
        "customer metrics, analyst recognition, deployment speed, quotes, and "
        "security findings. Prefer this for 'why customers use Rasa', CSAT, "
        "scale, and time-to-deploy questions. Uploads the PDF to Slack when "
        "possible."
    )
)
async def get_product_proof_points(context: ToolContext = None) -> ToolResult:
    """Return proof-point text and optionally upload the PDF to Slack."""
    try:
        page = await notion_client.get_page_with_body(
            PROOF_POINTS_PAGE_ID,
            max_blocks=100,
        )
    except notion_client.NotionConfigError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "message": str(exc),
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_page_unavailable",
                "status_code": exc.response.status_code,
                "message": (
                    "The Product Proof Points page is not visible to Sara's "
                    "Notion integration. Share the page with the integration "
                    "and retry."
                ),
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_error",
                "message": str(exc),
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    pdf = _pick_pdf(page.get("attachments") or [])
    if not pdf or not pdf.get("url"):
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "pdf_missing",
                "message": "No PDF attachment found on the Notion page.",
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(str(pdf["url"]))
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "pdf_download_failed",
                "message": str(exc),
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    if len(pdf_bytes) > _MAX_PDF_BYTES:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "pdf_too_large",
                "message": f"PDF exceeds {_MAX_PDF_BYTES} bytes.",
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    try:
        proof_text = _extract_pdf_text(pdf_bytes)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "pdf_parse_failed",
                "message": str(exc),
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    if not proof_text:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "pdf_empty",
                "message": "Could not extract readable text from the PDF.",
                "source_url": PROOF_POINTS_PAGE_URL,
                "instruction": _FAILURE_INSTRUCTION,
            }
        )

    filename = _filename_from_url(str(pdf["url"]))
    destination = _latest_slack_destination(context) if context else None
    upload_error: str | None = None
    uploaded = False

    if destination and os.environ.get("SLACK_BOT_TOKEN", "").strip():
        channel, thread_ts = destination
        client = AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"].strip())
        try:
            await client.files_upload_v2(
                channel=channel,
                thread_ts=thread_ts,
                content=pdf_bytes,
                filename=filename,
                title="Rasa Product Proof Points",
                initial_comment=(
                    "Latest Product Proof Points PDF "
                    f"(<{PROOF_POINTS_PAGE_URL}|Notion page>)."
                ),
            )
            uploaded = True
        except Exception as error:  # Slack SDK raises several API/transport types.
            upload_error = str(error)
            structlogger.error(
                "proof_points.slack_upload_failed",
                channel=channel,
                thread_ts=thread_ts,
                filename=filename,
                error=upload_error,
            )
    elif not destination:
        upload_error = "No Slack destination for this conversation."

    return ToolResult(
        llm_response={
            "ok": True,
            "page_title": page.get("title") or "Product Proof Points",
            "last_edited_time": page.get("last_edited_time"),
            "source_url": PROOF_POINTS_PAGE_URL,
            "pdf_filename": filename,
            "uploaded_to_slack": uploaded,
            "upload_error": upload_error,
            "proof_points_text": proof_text[:20000],
            "instruction": (
                "Answer only from proof_points_text. Use exact figures, "
                "customer names, and analyst designations from the PDF. Never "
                "combine stats from different studies or invent missing "
                "numbers. Prefer a short Slack-friendly answer (a few bullets). "
                "Always include source_url. If uploaded_to_slack is true, say "
                "the PDF is attached in this thread. If a number is not in the "
                "text, say it is not listed and point to the Notion page. "
                "Respect PDF 'Don't' guidance (e.g. N26 diagnostics are not "
                "production outcomes)."
            ),
        }
    )
