"""Serialization processor for meeting data."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def process_meeting_data(raw_json: dict) -> dict[str, Any]:
    """
    Extract structured fields from raw JSON and generate formatted markdown.
    
    Args:
        raw_json: Raw meeting JSON from webhook
        
    Returns:
        Dictionary with all fields ready for database insertion
    """
    meeting_id = raw_json["id"]
    doc_id = f"doc_{meeting_id}"
    
    # Extract title
    title = raw_json.get("name", "")
    
    # Format date from createdAt
    created_at = raw_json.get("createdAt", "")
    date_str = ""
    if created_at:
        try:
            # Parse ISO format and format as YYYY-MM-DD
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = created_at[:10] if len(created_at) >= 10 else ""
    
    # Extract attendees
    attendees = raw_json.get("attendees", [])
    
    # Extract notes (may be empty)
    notes = raw_json.get("notes", "") or ""
    
    # Extract transcript
    transcript = raw_json.get("transcript", [])
    
    # Generate formatted markdown content
    formatted_parts = [
        f"# {title}",
        "",
        f"**Date:** {date_str}",
        "",
        "**Attendees:**",
    ]
    
    for attendee in attendees:
        name = attendee.get("name", "")
        email = attendee.get("email", "")
        formatted_parts.append(f"- {name} ({email})")
    
    formatted_parts.append("")
    
    if notes:
        formatted_parts.append("## Notes")
        formatted_parts.append(notes)
        formatted_parts.append("")
    
    formatted_parts.append("## Transcript")
    for entry in transcript:
        speaker = entry.get("speaker", "")
        text = entry.get("text", "")
        timestamp = entry.get("timestamp", 0)
        formatted_parts.append(f"[{timestamp}] {speaker}: {text}")
    
    formatted_content = "\n".join(formatted_parts)
    
    # Build complete meeting record
    return {
        "meeting_id": meeting_id,
        "doc_id": doc_id,
        "title": title,
        "date": date_str,
        "attendees": attendees,
        "transcript": transcript,
        "raw_payload": raw_json,
        "formatted_content": formatted_content,
        "source": "circleblock",
        "processed": True,
    }
