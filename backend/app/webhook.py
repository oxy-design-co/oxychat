"""Webhook listener for meeting data ingestion."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from .database import get_db, save_meeting
from .processor import process_meeting_data

logger = logging.getLogger(__name__)

# SECURITY NOTE: For production, validate webhook secret via header
# Currently open/unauthenticated for local development
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


def validate_webhook_secret(request: Request) -> None:
    """
    Validate webhook secret if configured.
    
    SECURITY NOTE: For production, ensure WEBHOOK_SECRET is set and
    validate incoming requests. For local dev, this is optional.
    """
    if WEBHOOK_SECRET:
        x_webhook_secret = request.headers.get("X-Webhook-Secret")
        if x_webhook_secret != WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret",
            )


async def webhook_circleblock(
    payload: list[dict[str, Any]],
    request: Request,
    db: Session,
) -> dict[str, Any]:
    """
    Process webhook payload containing array of meeting objects.
    
    Args:
        payload: Array of meeting JSON objects
        request: FastAPI request object
        db: Database session
        
    Returns:
        Success response with count of processed meetings
    """
    # Validate webhook secret if configured
    validate_webhook_secret(request)
    
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must be an array of meeting objects",
        )
    
    processed_count = 0
    errors = []
    
    for meeting_json in payload:
        try:
            # Validate required fields
            if "id" not in meeting_json:
                errors.append(f"Missing 'id' field in meeting: {meeting_json.get('name', 'unknown')}")
                continue
            
            # Process meeting data
            meeting_data = process_meeting_data(meeting_json)
            
            # Save to database (insert or update)
            save_meeting(meeting_data, db)
            processed_count += 1
            
            logger.info(f"Processed meeting: {meeting_data['doc_id']} - {meeting_data['title']}")
            
        except Exception as e:
            error_msg = f"Error processing meeting {meeting_json.get('id', 'unknown')}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    if processed_count == 0 and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process any meetings: {', '.join(errors)}",
        )
    
    return {
        "status": "success",
        "processed": processed_count,
        "total": len(payload),
        "errors": errors if errors else None,
    }
