"""Tests for DeckData model enhancements (format and archetype fields)."""

import pytest
from pydantic import ValidationError

from mtg_keep_or_mull.models import DeckData


class TestDeckDataMetadata:
    """Test DeckData model with format and archetype metadata."""

    def test_deck_data_with_format_and_archetype(self) -> None:
        """Test creating DeckData with format and archetype fields."""
        deck = DeckData(
            deck_id="mono_u_terror_001",
            deck_name="Mono-U Terror",
            main_deck=["Island", "Delver of Secrets", "Counterspell"],
            sideboard=["Hydroblast"],
            total_games=0,
            format="Pauper",
            archetype="Tempo",
        )

        assert deck.format == "Pauper"
        assert deck.archetype == "Tempo"

    def test_deck_data_format_defaults_to_unknown(self) -> None:
        """Test that format defaults to 'Unknown' if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.format == "Unknown"

    def test_deck_data_archetype_defaults_to_unknown(self) -> None:
        """Test that archetype defaults to 'Unknown' if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.archetype == "Unknown"

    def test_deck_data_with_common_formats(self) -> None:
        """Test DeckData with various MTG formats."""
        formats = ["Pauper", "Modern", "Standard", "Legacy", "Vintage", "Commander", "Pioneer"]

        for fmt in formats:
            deck = DeckData(
                deck_id=f"deck_{fmt}",
                deck_name=f"{fmt} Deck",
                main_deck=["Island"],
                sideboard=[],
                total_games=0,
                format=fmt,
                archetype="Test",
            )
            assert deck.format == fmt

    def test_deck_data_with_common_archetypes(self) -> None:
        """Test DeckData with various MTG archetypes."""
        archetypes = [
            "Aggro",
            "Control",
            "Combo",
            "Midrange",
            "Tempo",
            "Burn",
            "Delver",
            "Tron",
            "Elves",
        ]

        for archetype in archetypes:
            deck = DeckData(
                deck_id=f"deck_{archetype}",
                deck_name=f"{archetype} Deck",
                main_deck=["Island"],
                sideboard=[],
                total_games=0,
                format="Modern",
                archetype=archetype,
            )
            assert deck.archetype == archetype

    def test_deck_data_format_is_optional(self) -> None:
        """Test that format field is optional."""
        # Should not raise ValidationError
        deck = DeckData(
            deck_id="test",
            deck_name="Test",
            main_deck=["Island"],
            sideboard=[],
            total_games=0,
            archetype="Control",  # Only provide archetype
        )
        assert deck.format == "Unknown"
        assert deck.archetype == "Control"

    def test_deck_data_archetype_is_optional(self) -> None:
        """Test that archetype field is optional."""
        # Should not raise ValidationError
        deck = DeckData(
            deck_id="test",
            deck_name="Test",
            main_deck=["Island"],
            sideboard=[],
            total_games=0,
            format="Pauper",  # Only provide format
        )
        assert deck.format == "Pauper"
        assert deck.archetype == "Unknown"

    def test_deck_data_json_serialization_with_metadata(self) -> None:
        """Test that DeckData with metadata serializes correctly to JSON."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Island", "Mountain"],
            sideboard=["Counterspell"],
            total_games=5,
            format="Modern",
            archetype="Control",
        )

        deck_dict = deck.model_dump()

        assert deck_dict["format"] == "Modern"
        assert deck_dict["archetype"] == "Control"
        assert deck_dict["deck_id"] == "test_deck"
        assert deck_dict["total_games"] == 5

    def test_deck_data_from_dict_with_metadata(self) -> None:
        """Test creating DeckData from dictionary with metadata."""
        deck_dict = {
            "deck_id": "elves_001",
            "deck_name": "Pauper Elves",
            "main_deck": ["Forest", "Llanowar Elves", "Priest of Titania"],
            "sideboard": ["Natural State"],
            "total_games": 42,
            "format": "Pauper",
            "archetype": "Combo",
        }

        deck = DeckData(**deck_dict)

        assert deck.deck_id == "elves_001"
        assert deck.deck_name == "Pauper Elves"
        assert deck.format == "Pauper"
        assert deck.archetype == "Combo"
        assert deck.total_games == 42


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
