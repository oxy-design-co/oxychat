from __future__ import annotations

from dataclasses import dataclass
from typing import Final, List, Optional


@dataclass(frozen=True)
class Transcript:
    id: str
    title: str
    date: str
    summary: str
    content: str


TRANSCRIPTS: Final[dict[str, Transcript]] = {
    "doc_1": Transcript(
        id="doc_1",
        title="Q3 Planning — ACME (Sep 12, 2025)",
        date="2025-09-12",
        summary="Roadmap, risks, budgets.",
        content=(
            "Kickoff for Q3 roadmap. Discussed key initiatives, budget allocations, "
            "risk register (supply chain, hiring), and success metrics."
        ),
    ),
    "doc_2": Transcript(
        id="doc_2",
        title="Launch Sync — Phoenix App (Sep 18, 2025)",
        date="2025-09-18",
        summary="Release checklist, blockers, owners.",
        content=(
            "Reviewed release checklist for Phoenix App. Identified blockers in QA "
            "automation and app store submission. Owners assigned and due dates set."
        ),
    ),
    "doc_3": Transcript(
        id="doc_3",
        title="Client Review — Oxy Site (Sep 23, 2025)",
        date="2025-09-23",
        summary="Feedback, scope changes, next steps.",
        content=(
            "Client provided feedback on homepage hero, case studies, and nav IA. "
            "Scope changes approved for CMS components and analytics events."
        ),
    ),
    "doc_4": Transcript(
        id="doc_4",
        title="Research Debrief — Growth Experiments (Sep 25, 2025)",
        date="2025-09-25",
        summary="Findings, hypotheses, priorities.",
        content=(
            "Shared experiment findings on onboarding, pricing page, and referral. "
            "Prioritized hypotheses for A/B tests with target KPIs."
        ),
    ),
    "doc_5": Transcript(
        id="doc_5",
        title="Postmortem — Campaign Alpha (Sep 27, 2025)",
        date="2025-09-27",
        summary="Outcomes, lessons, action items.",
        content=(
            "Reviewed campaign outcomes vs. goals. Lessons learned on targeting, "
            "creative fatigue, and channel mix. Action items assigned for next cycle."
        ),
    ),
}


def get_transcript(transcript_id: str) -> Optional[Transcript]:
    return TRANSCRIPTS.get(transcript_id)


def list_recent(limit: int = 10) -> List[Transcript]:
    # Assuming later items are more recent; adjust if we add timestamps
    items = list(TRANSCRIPTS.values())
    items.reverse()
    return items[:limit]


