from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, List, Optional


@dataclass(frozen=True)
class Transcript:
    id: str
    title: str
    date: str
    content: str
    summary: Optional[str] = None


# Hardcoded sample transcripts kept as a fallback when no raw Markdown files exist
DEFAULT_TRANSCRIPTS: Final[dict[str, Transcript]] = {
    "doc_1": Transcript(
        id="doc_1",
        title="Q3 Planning — ACME (Sep 12, 2025)",
        date="2025-09-12",
        content=(
            "Kickoff for Q3 roadmap. Discussed key initiatives, budget allocations, "
            "risk register (supply chain, hiring), and success metrics."
            "sksljdnkdsjnksdjfnfksjnfksjnksj f bunch of garbage text to test the system"
        ),
        summary="Roadmap, risks, budgets.",
    ),
    "doc_2": Transcript(
        id="doc_2",
        title="Launch Sync — Phoenix App (Sep 18, 2025)",
        date="2025-09-18",
        content=(
            "Reviewed release checklist for Phoenix App. Identified blockers in QA "
            "automation and app store submission. Owners assigned and due dates set."
        ),
        summary="Release checklist, blockers, owners.",
    ),
    "doc_3": Transcript(
        id="doc_3",
        title="Client Review — Oxy Site (Sep 23, 2025)",
        date="2025-09-23",
        content=(
            "Client provided feedback on homepage hero, case studies, and nav IA. "
            "Scope changes approved for CMS components and analytics events."
        ),
        summary="Feedback, scope changes, next steps.",
    ),
    "doc_4": Transcript(
        id="doc_4",
        title="Research Debrief — Growth Experiments (Sep 25, 2025)",
        date="2025-09-25",
        content=(
            "Shared experiment findings on onboarding, pricing page, and referral. "
            "Prioritized hypotheses for A/B tests with target KPIs."
        ),
        summary="Findings, hypotheses, priorities.",
    ),
    "doc_5": Transcript(
        id="doc_5",
        title="Postmortem — Campaign Alpha (Sep 27, 2025)",
        date="2025-09-27",
        content=(
            "Reviewed campaign outcomes vs. goals. Lessons learned on targeting, "
            "creative fatigue, and channel mix. Action items assigned for next cycle."
        ),
        summary="Outcomes, lessons, action items.",
    ),
}


def _slugify_filename(stem: str) -> str:
    # Lowercase, replace non-alphanumeric with underscores, collapse repeats, trim
    s = stem.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def _load_transcripts_from_directory(directory: Path) -> dict[str, Transcript]:
    transcripts: dict[str, Transcript] = {}
    if not directory.exists() or not directory.is_dir():
        return transcripts

    md_files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".md")
    for p in md_files:
        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            # Skip unreadable files silently for this quick demo
            continue

        title = p.stem.strip()
        slug = _slugify_filename(title)
        if not slug:
            # Fallback slug if filename is entirely symbols/whitespace
            slug = _slugify_filename(p.name)
        transcript_id = f"doc_{slug}"

        # Preserve insertion order (sorted by filename) via dict order
        transcripts[transcript_id] = Transcript(
            id=transcript_id,
            title=title,
            date="",
            content=content,
            summary=None,
        )

    return transcripts


# Populate transcripts from raw Markdown if available; otherwise use defaults
_RAW_DIR = Path(__file__).parent / "raw_transcripts"
_LOADED = _load_transcripts_from_directory(_RAW_DIR)
TRANSCRIPTS: Final[dict[str, Transcript]] = _LOADED if _LOADED else DEFAULT_TRANSCRIPTS


def get_transcript(transcript_id: str) -> Optional[Transcript]:
    return TRANSCRIPTS.get(transcript_id)


def list_recent(limit: int = 10) -> List[Transcript]:
    # Return the last N entries in insertion order (most recently inserted last)
    items = list(TRANSCRIPTS.values())
    return items[-limit:]


