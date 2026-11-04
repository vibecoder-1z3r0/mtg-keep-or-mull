"""API-specific Pydantic models for requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ========== Deck API Models ==========


class DeckUploadRequest(BaseModel):
    """Request model for uploading a deck."""

    deck_text: str = Field(..., description="MTGO-format deck list text")
    deck_name: str = Field("", description="Optional human-readable deck name")
    format: List[str] = Field(
        default_factory=list, description="MTG formats (e.g., Pauper, Modern, Standard)"
    )
    archetype: List[str] = Field(
        default_factory=list, description="Deck archetypes (e.g., Aggro, Control, Combo)"
    )
    colors: List[str] = Field(
        default_factory=list, description="Color identity (e.g., U, Grixis, Mono-Blue)"
    )
    tags: List[str] = Field(default_factory=list, description="Custom tags for categorization")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_text": "4 Lightning Bolt\n20 Mountain\n\nSIDEBOARD:\n3 Pyroblast",
                "deck_name": "Red Deck Wins",
                "format": ["Modern", "Pioneer"],
                "archetype": ["Aggro", "Burn"],
                "colors": ["R", "Mono-Red"],
                "tags": ["burn", "budget"],
            }
        }
    )


class DeckUpdateRequest(BaseModel):
    """Request model for updating deck metadata."""

    deck_name: Optional[str] = Field(None, description="Optional human-readable deck name")
    format: Optional[List[str]] = Field(
        None, description="MTG formats (e.g., Pauper, Modern, Standard)"
    )
    archetype: Optional[List[str]] = Field(
        None, description="Deck archetypes (e.g., Aggro, Control, Combo)"
    )
    colors: Optional[List[str]] = Field(
        None, description="Color identity (e.g., U, Grixis, Mono-Blue)"
    )
    tags: Optional[List[str]] = Field(None, description="Custom tags for categorization")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_name": "Updated Deck Name",
                "format": ["Modern", "Pioneer"],
                "archetype": ["Control"],
                "colors": ["U", "W", "Azorius"],
                "tags": ["permission", "card-draw"],
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
    format: List[str] = Field(
        default_factory=list, description="MTG formats (e.g., Pauper, Modern, Standard)"
    )
    archetype: List[str] = Field(
        default_factory=list, description="Deck archetypes (e.g., Aggro, Control, Combo)"
    )
    colors: List[str] = Field(
        default_factory=list, description="Color identity (e.g., U, Grixis, Mono-Blue)"
    )
    tags: List[str] = Field(default_factory=list, description="Custom tags for categorization")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_id": "mono_u_terror_20251122",
                "deck_name": "Mono U Terror",
                "main_deck_size": 60,
                "sideboard_size": 15,
                "created_at": "2025-11-22T10:30:00",
                "format": ["Pauper", "Modern", "Legacy"],
                "archetype": ["Tempo", "Control"],
                "colors": ["U", "Mono-Blue"],
                "tags": ["delver", "permission", "cantrips"],
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
    reason: Optional[str] = Field(None, description="Optional reason for keeping this hand")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cards_to_bottom": ["Island", "Brainstorm"],
                "reason": "2 lands with cantrip",
            }
        }
    )


class MulliganRequest(BaseModel):
    """Request model for mulliganing a hand."""

    reason: Optional[str] = Field(None, description="Optional reason for mulliganing this hand")

    model_config = ConfigDict(json_schema_extra={"example": {"reason": "Too many lands"}})


class DecisionRequest(BaseModel):
    """Request model for recording a mulligan decision."""

    decision: str = Field(..., pattern="^(keep|mull)$", description="keep or mull")
    reason: Optional[str] = Field(None, description="Optional reason for this decision")

    model_config = ConfigDict(
        json_schema_extra={"example": {"decision": "keep", "reason": "2 lands with cantrip"}}
    )


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
    keep_rate_by_mulligan_count: dict[int, float] = Field(
        ...,
        description="Keep rate percentage at each mulligan depth (0=opening 7, 1=mull to 6, etc.)",
    )

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
                "keep_rate_by_mulligan_count": {"0": 65.0, "1": 45.0, "2": 85.0, "3": 95.0},
            }
        }
    )


class DecisionResponse(BaseModel):
    """Response model for a single decision in history."""

    hand_signature: str = Field(..., description="Normalized hand signature")
    hand_display: List[str] = Field(..., description="Cards in display order")
    mulligan_count: int = Field(..., description="Number of mulligans taken")
    decision: str = Field(..., description="keep or mull")
    lands_in_hand: int = Field(..., description="Number of lands")
    on_play: bool = Field(..., description="On the play or draw")
    timestamp: str = Field(..., description="ISO format timestamp")
    deck_id: str = Field(..., description="Deck identifier")
    cards_bottomed: Optional[List[str]] = Field(default=None, description="Cards put on bottom")
    reason: Optional[str] = Field(default=None, description="Reason for the decision")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hand_signature": "Brainstorm,Counterspell,Island,Island,Mental Note",
                "hand_display": ["Island", "Brainstorm", "Counterspell", "Mental Note", "Island"],
                "mulligan_count": 1,
                "decision": "keep",
                "lands_in_hand": 2,
                "on_play": True,
                "timestamp": "2025-11-22T10:30:00",
                "deck_id": "mono_u_terror_20251122",
                "cards_bottomed": ["Mental Note"],
                "reason": "2 lands with cantrip, good enough at 6",
            }
        }
    )


class DecisionHistoryResponse(BaseModel):
    """Response model for decision history list."""

    decisions: List[DecisionResponse] = Field(..., description="List of decisions")
    total: int = Field(..., description="Total number of decisions")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decisions": [
                    {
                        "hand_signature": "Brainstorm,Island,Island",
                        "hand_display": ["Island", "Brainstorm", "Island"],
                        "mulligan_count": 0,
                        "decision": "mull",
                        "lands_in_hand": 2,
                        "on_play": True,
                        "timestamp": "2025-11-22T10:29:00",
                        "deck_id": "mono_u_terror_20251122",
                        "cards_bottomed": None,
                    }
                ],
                "total": 1,
            }
        }
    )


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
