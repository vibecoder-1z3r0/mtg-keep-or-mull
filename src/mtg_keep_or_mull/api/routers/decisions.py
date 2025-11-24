"""Decision history API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from mtg_keep_or_mull.api.dependencies import get_datastore
from mtg_keep_or_mull.api.models import DecisionHistoryResponse, DecisionResponse
from mtg_keep_or_mull.datastore import DataStore

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("", response_model=DecisionHistoryResponse)
def get_decision_history(
    deck_id: Optional[str] = Query(None, description="Filter by deck ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    datastore: DataStore = Depends(get_datastore),
) -> DecisionHistoryResponse:
    """Get chronological history of all mulligan decisions.

    Args:
        deck_id: Optional deck ID to filter results
        limit: Maximum number of decisions to return
        offset: Number of decisions to skip (for pagination)
        datastore: DataStore dependency

    Returns:
        DecisionHistoryResponse with list of decisions and total count
    """
    # Get all decisions or filter by deck
    if deck_id:
        all_decisions = datastore.get_decisions_for_deck(deck_id)
    else:
        all_decisions = datastore.get_all_decisions()

    # Sort by timestamp (chronological order - oldest first)
    sorted_decisions = sorted(all_decisions, key=lambda d: d.timestamp)

    # Apply pagination
    paginated_decisions = sorted_decisions[offset : offset + limit]

    # Convert to response models
    decisions: List[DecisionResponse] = [
        DecisionResponse(
            hand_signature=d.hand_signature,
            hand_display=d.hand_display,
            mulligan_count=d.mulligan_count,
            decision=d.decision,
            lands_in_hand=d.lands_in_hand,
            on_play=d.on_play,
            timestamp=d.timestamp.isoformat(),
            deck_id=d.deck_id,
            cards_bottomed=d.cards_bottomed,
            reason=d.reason,
        )
        for d in paginated_decisions
    ]

    return DecisionHistoryResponse(decisions=decisions, total=len(sorted_decisions))


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
