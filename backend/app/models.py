"""Pydantic models for meeting data validation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Meeting(BaseModel):
    """Meeting Pydantic model compatible with database schema."""

    id: Optional[int] = None  # Database auto-generated
    meeting_id: int  # Original ID from JSON
    doc_id: str  # Formatted as doc_{meeting_id}
    title: str
    date: str  # Formatted date YYYY-MM-DD
    attendees: list[dict]
    notes: Optional[str] = None
    transcript: list[dict]
    raw_payload: dict  # Full original JSON
    formatted_content: str  # Full markdown-formatted string
    source: str = "circleblock"
    processed: bool = True

    class Config:
        """Pydantic config."""

        from_attributes = True
