"""
Phase D — Generation SSE Streaming Endpoint
============================================
GET /api/sessions/{session_id}/stream
GET /api/sessions/{session_id}/generation/status
POST /api/sessions/{session_id}/generation/cancel
"""
import asyncio
import json
import logging
import time
import uuid
from typing import AsyncGenerator, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Session, GenerationOutput
from app.schemas.schemas import (
    GenerationStatusResponse,
    ErrorResponse,
)
from app.services.generation import stream_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Phase D — Generation"])


# ── Constants ─────────────────────────────────────────────────────────────────

HEARTBEAT_INTERVAL_SEC = 15.0
STREAM_CHUNK_DELAY_SEC = 0.05
MAX_SESSION_AGE_HOURS = 24

ALLOWED_PRE_GENERATION_STATES = frozenset({
    "creating", "queued", "retrieving", "clarifying", "ready"
})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _format_sse(event_type: str, data: Dict[str, Any], event_id: str) -> str:
    """Format SSE message per W3C spec."""
    return (
        f"id: {event_id}\n"
        f"event: {event_type}\n"
        f"data: {json.dumps(data, default=str)}\n\n"
    )


async def _fetch_session(
    session_id: str, db: AsyncSession
) -> Session:
    """Fetch session or raise 404."""
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Session not found: {session_id}",
                "error_code": "SESSION_NOT_FOUND",
            },
        )
    
    return session


# ── SSE Stream Generator ──────────────────────────────────────────────────────

async def _sse_event_stream(
    session_id: str,
    context: Dict[str, Any],
    design_type: str,
    db: AsyncSession,
    request_id: str,
) -> AsyncGenerator[str, None]:
    """Core SSE generator with heartbeat and error handling."""
    event_counter = 0
    heartbeat_queue: asyncio.Queue[str] = asyncio.Queue()

    def _next_event_id() -> str:
        nonlocal event_counter
        event_counter += 1
        return f"{request_id}-{event_counter}"

    # Initial ping
    yield _format_sse(
        event_type="ping",
        data={
            "type": "ping",
            "request_id": request_id,
            "session_id": session_id,
            "message": "SSE connection established",
            "timestamp": time.time(),
        },
        event_id=_next_event_id(),
    )

    # Heartbeat producer
    async def _heartbeat_producer() -> None:
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)
                await heartbeat_queue.put(
                    _format_sse(
                        event_type="heartbeat",
                        data={
                            "type": "heartbeat",
                            "timestamp": time.time(),
                            "request_id": request_id,
                        },
                        event_id=_next_event_id(),
                    )
                )
        except asyncio.CancelledError:
            raise

    heartbeat_task = asyncio.create_task(_heartbeat_producer())

    try:
        logger.info(
            "[%s] Starting generation for session %s (type=%s)",
            request_id, session_id, design_type,
        )

        async for event in stream_generation(session_id, context, design_type, db):
            # Drain heartbeats first
            while not heartbeat_queue.empty():
                yield await heartbeat_queue.get()

            event_status = event.get("status", "info")
            section = event.get("section")

            # Map to SSE event type
            if event_status == "started":
                sse_type = "section.start"
            elif event_status == "complete":
                sse_type = "section.done"
            elif event_status == "error":
                sse_type = "section.error"
            elif event_status == "done":
                sse_type = "pipeline.done"
            else:
                sse_type = "info"

            # Build payload
            payload = {
                "type": sse_type,
                "section": section,
                "status": event_status,
                "timestamp": time.time(),
            }

            if "payload" in event and event["payload"] is not None:
                payload["payload"] = event["payload"]
            if "tokens_used" in event:
                payload["tokens_used"] = event["tokens_used"]
            if "duration_ms" in event:
                payload["duration_ms"] = event["duration_ms"]
            if "cached" in event:
                payload["cached"] = event["cached"]
            if "error" in event:
                payload["error"] = event["error"]
                payload["error_code"] = "GENERATION_FAILED"

            yield _format_sse(
                event_type=sse_type,
                data=payload,
                event_id=_next_event_id(),
            )

            # Visual pacing
            if sse_type in ("section.done", "section.start"):
                await asyncio.sleep(STREAM_CHUNK_DELAY_SEC)

            # Break if pipeline done
            if section == "done" or event_status == "done":
                break

        # Drain remaining heartbeats
        while not heartbeat_queue.empty():
            yield await heartbeat_queue.get()

        logger.info("[%s] Generation complete for session %s", request_id, session_id)

    except asyncio.CancelledError:
        logger.info("[%s] Client disconnected for session %s", request_id, session_id)
        yield _format_sse(
            event_type="pipeline.error",
            data={
                "type": "pipeline.error",
                "error": "Client disconnected",
                "error_code": "CLIENT_DISCONNECT",
                "timestamp": time.time(),
            },
            event_id=_next_event_id(),
        )
        # Reset session state for retry
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session and session.status == "generating":
                session.status = "creating"
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to reset session: {e}")
        raise

    except Exception as e:
        logger.exception("[%s] Fatal error for session %s", request_id, session_id)
        yield _format_sse(
            event_type="pipeline.error",
            data={
                "type": "pipeline.error",
                "error": str(e),
                "error_code": "INTERNAL_ERROR",
                "timestamp": time.time(),
            },
            event_id=_next_event_id(),
        )
        # Mark session as error
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = "error"
                session.error_message = str(e)
                await db.commit()
        except Exception as cleanup_err:
            logger.warning(f"Failed to mark session as error: {cleanup_err}")

    finally:
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.debug("[%s] SSE stream cleanup complete", request_id)


# ── Main Endpoints ────────────────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/stream",
    summary="Stream generation events via SSE",
    description="Opens an SSE stream for the 5-section generation pipeline.",
    responses={
        200: {"description": "SSE stream opened"},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def stream_endpoint(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE endpoint for generation streaming."""
    request_id = _generate_request_id()
    start_time = time.time()

    logger.info("[%s] Stream request for session %s", request_id, session_id)

    # Fetch and validate session
    session = await _fetch_session(session_id, db)

    # Validate state
    if session.status not in ALLOWED_PRE_GENERATION_STATES:
        if session.status == "generating":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Generation already in progress",
                    "error_code": "CONCURRENT_GENERATION",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": f"Invalid state: {session.status}",
                "error_code": "INVALID_STATE",
            },
        )

    # Check context
    context = session.context_json or {}
    design_type = session.design_type or "HLD"

    if not context:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Session has no context",
                "error_code": "NO_CONTEXT",
            },
        )

    # Transition to generating
    session.status = "generating"
    session.started_at = __import__("datetime").datetime.utcnow()

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("[%s] Failed to update session", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to start generation",
                "error_code": "DB_ERROR",
            },
        )

    # Build stream
    async def _wrapped_stream() -> AsyncGenerator[str, None]:
        try:
            async for chunk in _sse_event_stream(
                session_id=session_id,
                context=context,
                design_type=design_type,
                db=db,
                request_id=request_id,
            ):
                yield chunk
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "[%s] Stream closed for session %s after %dms",
                request_id, session_id, duration_ms,
            )
            # Mark session complete
            try:
                session.status = "complete"
                session.completed_at = __import__("datetime").datetime.utcnow()
                await db.commit()
            except Exception as e:
                logger.warning(f"Failed to mark session complete: {e}")

    return StreamingResponse(
        _wrapped_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
            "X-Session-ID": session_id,
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get(
    "/sessions/{session_id}/generation/status",
    response_model=GenerationStatusResponse,
    summary="Check generation status",
    description="Poll generation status without streaming.",
)
async def get_generation_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> GenerationStatusResponse:
    """Get current generation status for all sections."""
    session = await _fetch_session(session_id, db)

    result = await db.execute(
        select(GenerationOutput).where(GenerationOutput.session_id == session_id)
    )
    outputs = result.scalars().all()

    sections = {}
    for output in outputs:
        sections[output.section] = {
            "status": output.status,
            "tokens_used": output.tokens_used,
            "duration_ms": output.duration_ms,
            "cached": output.cached,
        }

    total_tokens = sum(s.get("tokens_used") or 0 for s in sections.values())
    total_duration = sum(s.get("duration_ms") or 0 for s in sections.values())

    return GenerationStatusResponse(
        session_id=session_id,
        session_status=session.status,
        sections=sections,
        total_tokens=total_tokens,
        total_duration_ms=total_duration,
    )


@router.post(
    "/sessions/{session_id}/generation/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel generation",
    description="Cancel an in-progress generation.",
)
async def cancel_generation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel in-progress generation."""
    session = await _fetch_session(session_id, db)

    if session.status != "generating":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "No generation in progress",
                "error_code": "INVALID_STATE",
            },
        )

    session.status = "creating"

    # Mark pending outputs as cancelled
    result = await db.execute(
        select(GenerationOutput).where(
            GenerationOutput.session_id == session_id,
            GenerationOutput.status == "pending",
        )
    )
    for output in result.scalars().all():
        output.status = "cancelled"

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception(f"Failed to cancel generation for {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to cancel generation",
                "error_code": "DB_ERROR",
            },
        )

    logger.info(f"Generation cancelled for session {session_id}")