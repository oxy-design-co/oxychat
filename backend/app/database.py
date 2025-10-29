"""PostgreSQL database setup and models for meeting storage."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Text,
    create_engine,
    Index,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Meeting(Base):
    """Meeting table storing webhook data and formatted content."""

    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, unique=True, nullable=False, index=True)
    doc_id = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False, index=True)
    date = Column(Text, nullable=False, index=True)
    attendees = Column(JSONB, nullable=False)
    transcript = Column(JSONB, nullable=False)
    raw_payload = Column(JSONB, nullable=False)
    formatted_content = Column(Text, nullable=False)
    source = Column(Text, nullable=False, default="circleblock")
    processed = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_meeting_id", "meeting_id"),
        Index("idx_doc_id", "doc_id"),
        Index("idx_date", "date"),
        Index("idx_title", "title"),
    )


# Database connection setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/oxychat")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session (generator for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session directly (not for FastAPI endpoints)."""
    return SessionLocal()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def save_meeting(meeting_data: dict, db: Session) -> Meeting:
    """Insert or update meeting in database."""
    existing = db.query(Meeting).filter(Meeting.meeting_id == meeting_data["meeting_id"]).first()
    
    if existing:
        # Update existing meeting
        for key, value in meeting_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Insert new meeting
        new_meeting = Meeting(**meeting_data)
        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)
        return new_meeting


def get_meeting_by_doc_id(doc_id: str, db: Session) -> Optional[Meeting]:
    """Retrieve meeting by doc_id."""
    return db.query(Meeting).filter(Meeting.doc_id == doc_id).first()


def get_recent_meetings(limit: int, db: Session) -> list[Meeting]:
    """Get last N meetings by date."""
    return (
        db.query(Meeting)
        .order_by(Meeting.date.desc(), Meeting.created_at.desc())
        .limit(limit)
        .all()
    )
