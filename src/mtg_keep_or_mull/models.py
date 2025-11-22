"""Pydantic data models for MTG Keep or Mull."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HandDecisionData(BaseModel):
    """Data model for a single hand decision (keep or mulligan).

    This model captures all relevant information about a mulligan decision,
    including the hand composition, game state, and user decision.
    """

    hand_signature: str = Field(
        ..., description="Normalized hand signature (sorted card names) for statistics"
    )
    hand_display: List[str] = Field(
        ..., description="Actual card order shown to user (prevents bias)"
    )
    mulligan_count: int = Field(..., ge=0, le=6, description="Number of mulligans taken (0-6)")
    decision: str = Field(..., pattern="^(keep|mull)$", description="User decision: keep or mull")
    lands_in_hand: int = Field(..., ge=0, le=7, description="Number of land cards in hand")
    on_play: bool = Field(..., description="True if on the play, False if on the draw")
    timestamp: datetime = Field(default_factory=datetime.now, description="When decision was made")
    deck_id: str = Field(..., description="Identifier for the deck being practiced")
    cards_bottomed: Optional[List[str]] = Field(
        default=None,
        description="Cards put on bottom when keeping after mulligan (London Mulligan rule)",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for the decision (e.g., 'Not enough lands', 'Good curve')",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hand_signature": "Brainstorm,Counterspell,Island,Island,Lórien Revealed,Mental Note,Thought Scour",  # noqa: E501
                "hand_display": [
                    "Island",
                    "Brainstorm",
                    "Counterspell",
                    "Thought Scour",
                    "Mental Note",
                    "Island",
                    "Lórien Revealed",
                ],
                "mulligan_count": 1,
                "decision": "keep",
                "lands_in_hand": 2,
                "on_play": True,
                "timestamp": "2025-11-22T10:30:00",
                "deck_id": "mono_u_terror",
                "cards_bottomed": ["Lórien Revealed"],
                "reason": "2 lands with cantrip, good enough at 6",
            }
        }
    )


class DeckData(BaseModel):
    """Data model for a deck list.

    Stores both main deck and sideboard, along with metadata.
    """

    deck_id: str = Field(..., description="Unique identifier for this deck")
    deck_name: str = Field(default="", description="Optional human-readable deck name")
    main_deck: List[str] = Field(..., description="Main deck card names (60 cards typically)")
    sideboard: List[str] = Field(
        default_factory=list, description="Sideboard card names (0-15 cards)"
    )
    total_games: int = Field(default=0, ge=0, description="Total games played with this deck")
    format: str = Field(
        default="Unknown",
        description="MTG format (e.g., Pauper, Modern, Standard, Legacy, Commander)",
    )
    archetype: str = Field(
        default="Unknown",
        description="Deck archetype (e.g., Aggro, Control, Combo, Tempo, Midrange)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deck_id": "mono_u_terror_20251122",
                "deck_name": "Mono U Terror (Pauper)",
                "main_deck": ["Island", "Island", "Delver of Secrets", "Brainstorm"],
                "sideboard": ["Hydroblast", "Annul"],
                "total_games": 42,
                "format": "Pauper",
                "archetype": "Tempo",
            }
        }
    )


class HandStats(BaseModel):
    """Statistics for a specific hand composition.

    Aggregates all decisions made for hands with the same signature.
    """

    hand_signature: str = Field(..., description="Normalized hand signature")
    times_kept: int = Field(default=0, ge=0, description="Number of times this hand was kept")
    times_mulled: int = Field(
        default=0, ge=0, description="Number of times this hand was mulliganed"
    )
    keep_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Keep rate %")

    @property
    def total_decisions(self) -> int:
        """Total number of decisions for this hand."""
        return self.times_kept + self.times_mulled

    def calculate_keep_percentage(self) -> None:
        """Recalculate keep percentage based on current counts."""
        if self.total_decisions > 0:
            self.keep_percentage = (self.times_kept / self.total_decisions) * 100.0
        else:
            self.keep_percentage = 0.0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hand_signature": "Forest,Forest,Forest,Land Grant,Llanowar Elves,Priest of Titania,Quirion Ranger",  # noqa: E501
                "times_kept": 8,
                "times_mulled": 2,
                "keep_percentage": 80.0,
            }
        }
    )


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
