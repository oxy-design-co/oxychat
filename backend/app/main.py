"""FastAPI entrypoint wiring the ChatKit server and REST endpoints."""

from __future__ import annotations

from typing import Any

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from .chat import (
    AgentControllerServer,
    create_chatkit_server,
)
from .database import get_db, init_db
from .webhook import webhook_circleblock

app = FastAPI(title="ChatKit API")

# Initialize database on startup
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database tables on startup."""
    init_db()

_chatkit_server: AgentControllerServer | None = create_chatkit_server()


def get_chatkit_server() -> AgentControllerServer:
    if _chatkit_server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ChatKit dependencies are missing. Install the ChatKit Python "
                "package to enable the conversational endpoint."
            ),
        )
    return _chatkit_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: AgentControllerServer = Depends(get_chatkit_server)
) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)




@app.post("/webhook/circleblock")
async def webhook_endpoint(
    payload: list[dict[str, Any]],
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Webhook endpoint for receiving meeting data."""
    return await webhook_circleblock(payload, request, db)


@app.get("/api/meetings/recent")
async def get_recent_meetings(
    limit: int = 10,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get last N processed meetings."""
    from .database import get_recent_meetings as db_get_recent
    meetings = db_get_recent(limit, db)
    return {
        "meetings": [
            {
                "id": meeting.doc_id,
                "title": meeting.title,
                "date": meeting.date,
            }
            for meeting in meetings
        ]
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
