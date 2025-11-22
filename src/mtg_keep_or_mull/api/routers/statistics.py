"""Statistics API endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from mtg_keep_or_mull.api.dependencies import get_datastore
from mtg_keep_or_mull.api.models import (
    AllHandStatsResponse,
    DeckStatsResponse,
    HandStatsResponse,
)
from mtg_keep_or_mull.datastore import DataStore
from mtg_keep_or_mull.models import HandDecisionData

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/hands", response_model=AllHandStatsResponse)
def get_all_hand_statistics(
    datastore: DataStore = Depends(get_datastore),
) -> AllHandStatsResponse:
    """Get statistics for all recorded hand compositions.

    Args:
        datastore: DataStore dependency

    Returns:
        AllHandStatsResponse with statistics for all unique hands
    """
    all_stats = datastore.get_all_hand_statistics()

    hands = [
        HandStatsResponse(
            hand_signature=stats.hand_signature,
            times_kept=stats.times_kept,
            times_mulled=stats.times_mulled,
            keep_percentage=stats.keep_percentage,
            total_decisions=stats.total_decisions,
        )
        for stats in all_stats
    ]

    return AllHandStatsResponse(hands=hands, total=len(hands))


@router.get("/hands/{signature:path}", response_model=HandStatsResponse)
def get_hand_statistics(
    signature: str, datastore: DataStore = Depends(get_datastore)
) -> HandStatsResponse:
    """Get statistics for a specific hand composition.

    Args:
        signature: Normalized hand signature (sorted card names, comma-separated)
        datastore: DataStore dependency

    Returns:
        HandStatsResponse with statistics for this hand

    Raises:
        HTTPException: If no statistics found for this hand
    """
    stats = datastore.get_hand_statistics(signature)
    if not stats:
        raise HTTPException(status_code=404, detail=f"No statistics found for hand: {signature}")

    return HandStatsResponse(
        hand_signature=stats.hand_signature,
        times_kept=stats.times_kept,
        times_mulled=stats.times_mulled,
        keep_percentage=stats.keep_percentage,
        total_decisions=stats.total_decisions,
    )


@router.get("/decks/{deck_id}", response_model=DeckStatsResponse)
def get_deck_statistics(
    deck_id: str, datastore: DataStore = Depends(get_datastore)
) -> DeckStatsResponse:
    """Get statistics for a specific deck.

    Args:
        deck_id: Deck identifier
        datastore: DataStore dependency

    Returns:
        DeckStatsResponse with deck statistics

    Raises:
        HTTPException: If deck not found or no statistics available
    """
    # Verify deck exists
    deck_data = datastore.load_deck(deck_id)
    if not deck_data:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")

    # Get all decisions for this deck
    decisions = datastore.get_decisions_for_deck(deck_id)
    if not decisions:
        raise HTTPException(status_code=404, detail=f"No statistics available for deck: {deck_id}")

    # Calculate statistics
    total_games = len(decisions)

    # Count mulligan distribution (only count "keep" decisions)
    mulligan_distribution: Dict[int, int] = {}
    for decision in decisions:
        if decision.decision == "keep":
            count = decision.mulligan_count
            mulligan_distribution[count] = mulligan_distribution.get(count, 0) + 1

    # Calculate average mulligan count (only from "keep" decisions)
    kept_decisions = [d for d in decisions if d.decision == "keep"]
    if kept_decisions:
        total_mulligans = sum(d.mulligan_count for d in kept_decisions)
        average_mulligan_count = total_mulligans / len(kept_decisions)
    else:
        average_mulligan_count = 0.0

    # Count hands kept at each size
    hands_kept_at_7 = mulligan_distribution.get(0, 0)
    hands_kept_at_6 = mulligan_distribution.get(1, 0)
    hands_kept_at_5 = mulligan_distribution.get(2, 0)

    return DeckStatsResponse(
        deck_id=deck_id,
        total_games=total_games,
        mulligan_distribution=mulligan_distribution,
        average_mulligan_count=round(average_mulligan_count, 2),
        hands_kept_at_7=hands_kept_at_7,
        hands_kept_at_6=hands_kept_at_6,
        hands_kept_at_5=hands_kept_at_5,
    )


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
