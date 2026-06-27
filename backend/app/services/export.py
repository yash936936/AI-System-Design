"""
Export Service — Real PDF, Markdown, and JSON generation.

Files are written to  ./static/exports/<session_id>.<format>  and served
via FastAPI's StaticFiles mount at  /static/...  so the download_url is a
real, durable URL (not a mock placeholder).

PDF generation uses WeasyPrint (pure-Python, no headless browser needed).
If WeasyPrint is unavailable the service falls back to a plain-text PDF
built with fpdf2 so the pipeline never hard-fails in dev.
"""
from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Export, GenerationOutput, Session as SessionModel
from app.schemas.schemas import ExportRequest, ExportResponse
from app.services.session import get_session

# ── Output directory ──────────────────────────────────────────────────────────
EXPORT_DIR = Path("static/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _naive_utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _server_base_url() -> str:
    return os.getenv("SERVER_BASE_URL", "http://localhost:8000")


def _download_url(filename: str) -> str:
    return f"{_server_base_url()}/static/exports/{filename}"


async def _collect_generation_content(
    db: AsyncSession,
    session_id: UUID,
    sections: list[str] | None,
) -> list[dict]:
    """Return GenerationOutput rows for the session, filtered by sections."""
    q = select(GenerationOutput).where(
        GenerationOutput.session_id == session_id,
        GenerationOutput.status == "complete",
    )
    result = await db.execute(q)
    rows = result.scalars().all()
    if sections:
        rows = [r for r in rows if r.section in sections]
    return [
        {
            "section": r.section,
            "payload": r.payload_json or {},
            "tokens_used": r.tokens_used,
        }
        for r in rows
    ]


# ── Format renderers ───────────────────────────────────────────────────────────

def _render_markdown(
    session: SessionModel,
    rows: list[dict],
) -> str:
    lines: list[str] = []
    lines.append(f"# System Design: {session.prompt}")
    lines.append(f"\n**Type:** {session.design_type or 'N/A'}  ")
    lines.append(f"**Generated:** {_naive_utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
    lines.append("---\n")

    for row in rows:
        section = row["section"].replace("_", " ").title()
        lines.append(f"## {section}\n")
        payload = row["payload"]

        if "content" in payload:
            lines.append(str(payload["content"]))
        elif "diagram" in payload:
            lines.append("```\n" + str(payload["diagram"]) + "\n```")
        elif "table" in payload:
            # Simple Markdown table
            table = payload["table"]
            if isinstance(table, list) and table:
                headers = list(table[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row_item in table:
                    lines.append("| " + " | ".join(str(row_item.get(h, "")) for h in headers) + " |")
        else:
            lines.append(json.dumps(payload, indent=2))

        lines.append("")  # blank line between sections

    return "\n".join(lines)


def _render_json(session: SessionModel, rows: list[dict]) -> str:
    data = {
        "session_id": str(session.id),
        "prompt": session.prompt,
        "design_type": session.design_type,
        "exported_at": _naive_utcnow().isoformat(),
        "sections": rows,
    }
    return json.dumps(data, indent=2, default=str)


def _render_pdf(session: SessionModel, rows: list[dict]) -> bytes:
    """Generate a real PDF using WeasyPrint; fall back to fpdf2."""
    md_content = _render_markdown(session, rows)
    html = _md_to_html(md_content, session.prompt or "System Design")

    try:
        from weasyprint import HTML  # type: ignore
        return HTML(string=html).write_pdf()
    except Exception:
        pass  # WeasyPrint failed or not installed — try fpdf2

    try:
        return _fpdf2_pdf(session.prompt or "System Design", rows)
    except Exception:
        pass

    # Last resort — minimal valid PDF built by hand
    return _minimal_pdf(md_content)


def _md_to_html(md: str, title: str) -> str:
    """Convert the markdown string to a styled HTML document for WeasyPrint."""
    # Very lightweight conversion — avoids an extra dep (markdown/mistune).
    import re
    body = md

    # Headings
    body = re.sub(r"^### (.+)$", r"<h3>\1</h3>", body, flags=re.M)
    body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", body, flags=re.M)
    body = re.sub(r"^# (.+)$", r"<h1>\1</h1>", body, flags=re.M)

    # Bold / italic
    body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
    body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", body)

    # Code blocks
    body = re.sub(r"```[\w]*\n(.*?)```", r"<pre><code>\1</code></pre>", body, flags=re.S)
    body = re.sub(r"`(.+?)`", r"<code>\1</code>", body)

    # HR
    body = body.replace("---", "<hr/>")

    # Paragraphs (double newline)
    paragraphs = re.split(r"\n\n+", body)
    body = "\n".join(
        p if re.match(r"<(h[1-6]|ul|ol|pre|hr|table)", p.strip()) else f"<p>{p.strip()}</p>"
        for p in paragraphs if p.strip()
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11pt;
         line-height: 1.6; color: #111; margin: 2cm; }}
  h1 {{ font-size: 20pt; border-bottom: 2px solid #FFC000; padding-bottom: 6px; }}
  h2 {{ font-size: 14pt; color: #222; margin-top: 24px; }}
  h3 {{ font-size: 12pt; color: #444; }}
  pre {{ background: #f5f5f5; padding: 12px; border-left: 3px solid #FFC000;
         font-size: 9pt; white-space: pre-wrap; word-break: break-word; }}
  code {{ background: #f0f0f0; padding: 2px 4px; font-size: 9pt; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  th {{ background: #FFC000; font-weight: bold; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _fpdf2_pdf(title: str, rows: list[dict]) -> bytes:
    from fpdf import FPDF  # type: ignore
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.ln(4)
    for row in rows:
        section = row["section"].replace("_", " ").title()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, section, ln=True)
        pdf.set_font("Helvetica", size=10)
        content = json.dumps(row["payload"], indent=2)
        for line in content.splitlines():
            for chunk in textwrap.wrap(line, width=100) or [""]:
                pdf.cell(0, 5, chunk, ln=True)
        pdf.ln(3)
    return pdf.output()


def _minimal_pdf(text: str) -> bytes:
    """Emergency fallback — returns a bare-minimum valid PDF."""
    safe = text[:4000].encode("latin-1", errors="replace").decode("latin-1")
    stream = f"BT /F1 10 Tf 50 750 Td ({safe[:200]}) Tj ET"
    body = (
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        "   /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font\n"
        "   /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n{stream}\nendstream\nendobj\n"
    )
    xref_offset = len(f"%PDF-1.4\n{body}")
    xref = (
        "xref\n0 5\n0000000000 65535 f \n"
        + "\n".join(f"{i*10:010d} 00000 n " for i in range(1, 5))
        + "\n"
    )
    trailer = f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    return f"%PDF-1.4\n{body}{xref}{trailer}".encode("latin-1", errors="replace")


# ── Public API ─────────────────────────────────────────────────────────────────

async def create_export(
    db: AsyncSession,
    session_id: UUID,
    request: ExportRequest,
    owner_id: str | None = None,
) -> ExportResponse:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    # Ownership check — only enforce when the session has a recorded user_id
    if owner_id and session.user_id and session.user_id != "anonymous" and session.user_id != owner_id:
        raise PermissionError("You do not own this session")

    rows = await _collect_generation_content(db, session_id, request.sections)
    if not rows:
        raise ValueError("No completed generation outputs found for this session")

    fmt = request.format.lower()
    filename = f"{session_id}.{fmt}"
    dest = EXPORT_DIR / filename

    if fmt == "md":
        content = _render_markdown(session, rows)
        dest.write_text(content, encoding="utf-8")
        size = dest.stat().st_size
    elif fmt == "json":
        content = _render_json(session, rows)
        dest.write_text(content, encoding="utf-8")
        size = dest.stat().st_size
    elif fmt == "pdf":
        pdf_bytes = _render_pdf(session, rows)
        dest.write_bytes(pdf_bytes)
        size = len(pdf_bytes)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    download_url = _download_url(filename)
    storage_key = f"exports/{filename}"
    expires_at = _naive_utcnow() + timedelta(days=7)

    export = Export(
        session_id=session_id,
        user_id=owner_id or session.user_id,
        format=fmt,
        sections=request.sections,
        download_url=download_url,
        storage_key=storage_key,
        size_bytes=size,
        expires_at=expires_at,
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)
    await db.commit()

    return ExportResponse(
        id=export.id,
        session_id=export.session_id,
        format=export.format,
        sections=export.sections,
        download_url=export.download_url,
        expires_at=export.expires_at,
        created_at=export.created_at,
    )


async def get_export(db: AsyncSession, export_id: UUID) -> ExportResponse | None:
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()
    if not export:
        return None
    return ExportResponse(
        id=export.id,
        session_id=export.session_id,
        format=export.format,
        sections=export.sections,
        download_url=export.download_url,
        expires_at=export.expires_at,
        created_at=export.created_at,
    )