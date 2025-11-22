"""Tests for DeckData model enhancements (list-based metadata fields)."""

import pytest
from pydantic import ValidationError

from mtg_keep_or_mull.models import DeckData


class TestDeckDataMetadata:
    """Test DeckData model with list-based metadata (format, archetype, colors, tags)."""

    def test_deck_data_with_all_metadata_lists(self) -> None:
        """Test creating DeckData with all metadata fields as lists."""
        deck = DeckData(
            deck_id="grixis_storm_001",
            deck_name="Grixis Storm",
            main_deck=["Island", "Swamp", "Mountain", "Lightning Bolt"],
            sideboard=["Hydroblast"],
            total_games=0,
            format=["Pauper", "Modern"],
            archetype=["Aggro", "Combo"],
            colors=["Grixis", "U", "B", "R"],
            tags=["Storm", "spell-based", "graveyard"],
        )

        assert deck.format == ["Pauper", "Modern"]
        assert deck.archetype == ["Aggro", "Combo"]
        assert deck.colors == ["Grixis", "U", "B", "R"]
        assert deck.tags == ["Storm", "spell-based", "graveyard"]

    def test_deck_data_format_defaults_to_empty_list(self) -> None:
        """Test that format defaults to empty list if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.format == []
        assert isinstance(deck.format, list)

    def test_deck_data_archetype_defaults_to_empty_list(self) -> None:
        """Test that archetype defaults to empty list if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.archetype == []
        assert isinstance(deck.archetype, list)

    def test_deck_data_colors_defaults_to_empty_list(self) -> None:
        """Test that colors defaults to empty list if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.colors == []
        assert isinstance(deck.colors, list)

    def test_deck_data_tags_defaults_to_empty_list(self) -> None:
        """Test that tags defaults to empty list if not provided."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Mountain"],
            sideboard=[],
            total_games=0,
        )

        assert deck.tags == []
        assert isinstance(deck.tags, list)

    def test_deck_data_with_multiple_formats(self) -> None:
        """Test DeckData with multiple formats (multi-format legal deck)."""
        deck = DeckData(
            deck_id="mono_u_terror",
            deck_name="Mono-U Terror",
            main_deck=["Island", "Delver of Secrets"],
            sideboard=[],
            total_games=0,
            format=["Pauper", "Modern", "Legacy", "Vintage"],
            archetype=["Tempo"],
            colors=["U"],
        )

        assert len(deck.format) == 4
        assert "Pauper" in deck.format
        assert "Vintage" in deck.format

    def test_deck_data_with_multiple_archetypes(self) -> None:
        """Test DeckData with multiple archetypes (hybrid strategy)."""
        deck = DeckData(
            deck_id="delver_deck",
            deck_name="Delver",
            main_deck=["Island", "Delver of Secrets"],
            sideboard=[],
            total_games=0,
            format=["Pauper"],
            archetype=["Aggro", "Tempo", "Control"],
            colors=["U"],
        )

        assert len(deck.archetype) == 3
        assert "Tempo" in deck.archetype
        assert "Control" in deck.archetype

    def test_deck_data_with_color_identity(self) -> None:
        """Test DeckData with various color representations."""
        # Can represent colors multiple ways
        deck = DeckData(
            deck_id="grixis_deck",
            deck_name="Grixis Control",
            main_deck=["Island", "Swamp", "Mountain"],
            sideboard=[],
            total_games=0,
            format=["Modern"],
            archetype=["Control"],
            colors=["Grixis", "UBR", "U", "B", "R"],  # Multiple representations
        )

        assert "Grixis" in deck.colors
        assert "UBR" in deck.colors
        assert "U" in deck.colors

    def test_deck_data_with_tags(self) -> None:
        """Test DeckData with flexible tags."""
        deck = DeckData(
            deck_id="storm_deck",
            deck_name="Storm Combo",
            main_deck=["Island", "Grapeshot"],
            sideboard=[],
            total_games=0,
            format=["Pauper"],
            archetype=["Combo"],
            colors=["Grixis"],
            tags=["Storm", "spell-based", "graveyard", "budget", "tournament-viable"],
        )

        assert len(deck.tags) == 5
        assert "Storm" in deck.tags
        assert "budget" in deck.tags

    def test_deck_data_with_single_value_lists(self) -> None:
        """Test that single values still work in list form."""
        deck = DeckData(
            deck_id="mono_red",
            deck_name="Mono Red Burn",
            main_deck=["Mountain", "Lightning Bolt"],
            sideboard=[],
            total_games=0,
            format=["Pauper"],  # Single format
            archetype=["Aggro"],  # Single archetype
            colors=["R"],  # Single color
            tags=["Burn"],  # Single tag
        )

        assert deck.format == ["Pauper"]
        assert deck.archetype == ["Aggro"]
        assert deck.colors == ["R"]
        assert deck.tags == ["Burn"]

    def test_deck_data_json_serialization_with_list_metadata(self) -> None:
        """Test that DeckData with list metadata serializes correctly to JSON."""
        deck = DeckData(
            deck_id="test_deck",
            deck_name="Test Deck",
            main_deck=["Island", "Mountain"],
            sideboard=["Counterspell"],
            total_games=5,
            format=["Modern", "Pioneer"],
            archetype=["Control", "Midrange"],
            colors=["UR", "Izzet"],
            tags=["spell-based", "instants"],
        )

        deck_dict = deck.model_dump()

        assert deck_dict["format"] == ["Modern", "Pioneer"]
        assert deck_dict["archetype"] == ["Control", "Midrange"]
        assert deck_dict["colors"] == ["UR", "Izzet"]
        assert deck_dict["tags"] == ["spell-based", "instants"]
        assert deck_dict["deck_id"] == "test_deck"
        assert deck_dict["total_games"] == 5

    def test_deck_data_from_dict_with_list_metadata(self) -> None:
        """Test creating DeckData from dictionary with list metadata."""
        deck_dict = {
            "deck_id": "elves_001",
            "deck_name": "Pauper Elves",
            "main_deck": ["Forest", "Llanowar Elves", "Priest of Titania"],
            "sideboard": ["Natural State"],
            "total_games": 42,
            "format": ["Pauper", "Modern"],
            "archetype": ["Combo", "Aggro"],
            "colors": ["G", "Mono-Green"],
            "tags": ["tribal", "elves", "mana-dorks"],
        }

        deck = DeckData(**deck_dict)

        assert deck.deck_id == "elves_001"
        assert deck.deck_name == "Pauper Elves"
        assert deck.format == ["Pauper", "Modern"]
        assert deck.archetype == ["Combo", "Aggro"]
        assert deck.colors == ["G", "Mono-Green"]
        assert deck.tags == ["tribal", "elves", "mana-dorks"]
        assert deck.total_games == 42

    def test_deck_data_all_metadata_optional(self) -> None:
        """Test that all metadata fields are optional."""
        # Should not raise ValidationError
        deck = DeckData(
            deck_id="minimal",
            deck_name="Minimal Deck",
            main_deck=["Island"],
            sideboard=[],
            total_games=0,
        )

        assert deck.format == []
        assert deck.archetype == []
        assert deck.colors == []
        assert deck.tags == []

    def test_deck_data_partial_metadata(self) -> None:
        """Test providing only some metadata fields."""
        deck = DeckData(
            deck_id="partial",
            deck_name="Partial Metadata",
            main_deck=["Island"],
            sideboard=[],
            total_games=0,
            format=["Pauper"],
            tags=["budget"],
            # archetype and colors not provided
        )

        assert deck.format == ["Pauper"]
        assert deck.archetype == []
        assert deck.colors == []
        assert deck.tags == ["budget"]

    def test_deck_data_empty_lists_explicit(self) -> None:
        """Test explicitly providing empty lists."""
        deck = DeckData(
            deck_id="empty",
            deck_name="Empty Lists",
            main_deck=["Island"],
            sideboard=[],
            total_games=0,
            format=[],
            archetype=[],
            colors=[],
            tags=[],
        )

        assert deck.format == []
        assert deck.archetype == []
        assert deck.colors == []
        assert deck.tags == []

    def test_deck_data_with_common_format_combinations(self) -> None:
        """Test realistic multi-format combinations."""
        # Standard deck also legal in Pioneer, Modern, etc.
        standard_deck = DeckData(
            deck_id="std_001",
            deck_name="Standard Deck",
            main_deck=["Island"],
            format=["Standard", "Pioneer", "Modern", "Legacy", "Vintage"],
        )
        assert "Standard" in standard_deck.format
        assert "Vintage" in standard_deck.format

        # Pauper-only deck
        pauper_deck = DeckData(
            deck_id="pauper_001",
            deck_name="Pauper Only",
            main_deck=["Island"],
            format=["Pauper"],
        )
        assert pauper_deck.format == ["Pauper"]

    def test_deck_data_with_non_standard_formats(self) -> None:
        """Test custom/casual formats."""
        deck = DeckData(
            deck_id="casual_001",
            deck_name="Kitchen Table",
            main_deck=["Black Lotus"],  # Not legal anywhere!
            format=["Casual", "Kitchen Table", "Non-Standard"],
            tags=["house-rules", "vintage-cube"],
        )

        assert "Casual" in deck.format
        assert "Kitchen Table" in deck.format
        assert "house-rules" in deck.tags


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
