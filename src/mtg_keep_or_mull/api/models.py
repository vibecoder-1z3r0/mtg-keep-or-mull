"""API-specific Pydantic models for requests and responses."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


# ========== Deck API Models ==========


class DeckUploadRequest(BaseModel):
    """Request model for uploading a deck."""

    deck_text: str = Field(..., description="MTGO-format deck list text")
    deck_name: str = Field("", description="Optional human-readable deck name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_text": "4 Lightning Bolt\n20 Mountain\n\nSIDEBOARD:\n3 Pyroblast",
                "deck_name": "Red Deck Wins",
            }
        }
    )


class DeckResponse(BaseModel):
    """Response model for deck information."""

    deck_id: str = Field(..., description="Unique identifier for this deck")
    deck_name: str = Field(..., description="Human-readable deck name")
    main_deck_size: int = Field(..., description="Number of cards in main deck")
    sideboard_size: int = Field(..., description="Number of cards in sideboard")
    created_at: datetime = Field(..., description="When the deck was created")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_id": "mono_u_terror_20251122",
                "deck_name": "Mono U Terror",
                "main_deck_size": 60,
                "sideboard_size": 15,
                "created_at": "2025-11-22T10:30:00",
            }
        }
    )


class DeckListResponse(BaseModel):
    """Response model for listing decks."""

    decks: List[DeckResponse] = Field(..., description="List of available decks")
    total: int = Field(..., description="Total number of decks")


# ========== Session API Models ==========


class SessionStartRequest(BaseModel):
    """Request model for starting a new practice session."""

    deck_id: str = Field(..., description="ID of the deck to practice with")
    on_play: bool = Field(..., description="True if on the play, False if on the draw")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_id": "mono_u_terror_20251122",
                "on_play": True,
            }
        }
    )


class CardResponse(BaseModel):
    """Response model for a card."""

    name: str = Field(..., description="Card name")

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Island"}})


class HandResponse(BaseModel):
    """Response model for a hand of cards."""

    cards: List[CardResponse] = Field(..., description="Cards in hand (display order)")
    size: int = Field(..., description="Number of cards in hand")
    signature: str = Field(..., description="Normalized hand signature for statistics")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cards": [{"name": "Island"}, {"name": "Brainstorm"}, {"name": "Counterspell"}],
                "size": 3,
                "signature": "Brainstorm,Counterspell,Island",
            }
        }
    )


class SessionResponse(BaseModel):
    """Response model for session state."""

    session_id: str = Field(..., description="Unique session identifier")
    deck_id: str = Field(..., description="Deck being used")
    on_play: bool = Field(..., description="On the play or on the draw")
    mulligan_count: int = Field(..., description="Number of mulligans taken")
    current_hand: HandResponse = Field(..., description="Current hand")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "deck_id": "mono_u_terror_20251122",
                "on_play": True,
                "mulligan_count": 1,
                "current_hand": {
                    "cards": [{"name": "Island"}, {"name": "Brainstorm"}],
                    "size": 2,
                    "signature": "Brainstorm,Island",
                },
            }
        }
    )


class KeepHandRequest(BaseModel):
    """Request model for keeping a hand."""

    cards_to_bottom: List[str] = Field(
        ..., description="Card names to put on bottom (must match mulligan count)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"cards_to_bottom": ["Island", "Brainstorm"]}}
    )


class DecisionRequest(BaseModel):
    """Request model for recording a mulligan decision."""

    decision: str = Field(..., pattern="^(keep|mull)$", description="keep or mull")

    model_config = ConfigDict(json_schema_extra={"example": {"decision": "keep"}})


# ========== Statistics API Models ==========


class HandStatsResponse(BaseModel):
    """Response model for hand statistics."""

    hand_signature: str = Field(..., description="Normalized hand signature")
    times_kept: int = Field(..., description="Number of times this hand was kept")
    times_mulled: int = Field(..., description="Number of times this hand was mulliganed")
    keep_percentage: float = Field(..., description="Keep rate percentage")
    total_decisions: int = Field(..., description="Total decisions for this hand")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hand_signature": "Brainstorm,Counterspell,Island,Island,Mental Note",
                "times_kept": 8,
                "times_mulled": 2,
                "keep_percentage": 80.0,
                "total_decisions": 10,
            }
        }
    )


class AllHandStatsResponse(BaseModel):
    """Response model for all hand statistics."""

    hands: List[HandStatsResponse] = Field(..., description="Statistics for all unique hands")
    total: int = Field(..., description="Total number of unique hands")


class DeckStatsResponse(BaseModel):
    """Response model for deck-specific statistics."""

    deck_id: str = Field(..., description="Deck identifier")
    total_games: int = Field(..., description="Total games played with this deck")
    mulligan_distribution: dict[int, int] = Field(
        ..., description="Distribution of mulligan counts (0=no mull, 1=1 mull, etc.)"
    )
    average_mulligan_count: float = Field(..., description="Average mulligans per game")
    hands_kept_at_7: int = Field(..., description="Games where opening 7 was kept")
    hands_kept_at_6: int = Field(..., description="Games that mulled to 6")
    hands_kept_at_5: int = Field(..., description="Games that mulled to 5")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_id": "mono_u_terror_20251122",
                "total_games": 42,
                "mulligan_distribution": {"0": 25, "1": 12, "2": 4, "3": 1},
                "average_mulligan_count": 0.64,
                "hands_kept_at_7": 25,
                "hands_kept_at_6": 12,
                "hands_kept_at_5": 4,
            }
        }
    )


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
