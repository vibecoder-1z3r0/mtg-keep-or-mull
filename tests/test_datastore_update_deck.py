"""Tests for updating deck metadata in DataStore."""

import pytest

from mtg_keep_or_mull.datastore import MockDataStore
from mtg_keep_or_mull.models import DeckData


class TestDataStoreUpdateDeck:
    """Test updating deck metadata across all DataStore implementations."""

    @pytest.fixture
    def datastore_with_deck(self) -> MockDataStore:
        """Create a datastore with a sample deck."""
        store = MockDataStore()
        deck = DeckData(
            deck_id="test_deck_001",
            deck_name="Original Deck",
            main_deck=["Island"] * 60,
            sideboard=["Hydroblast"] * 15,
            format=["Pauper"],
            archetype=["Tempo"],
            colors=["U"],
            tags=["test"],
        )
        store.save_deck(deck)
        return store

    def test_update_deck_metadata_all_fields(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test updating all metadata fields at once."""
        updated_deck = DeckData(
            deck_id="test_deck_001",
            deck_name="Updated Deck Name",
            main_deck=["Island"] * 60,
            sideboard=["Hydroblast"] * 15,
            format=["Pauper", "Modern", "Legacy"],
            archetype=["Tempo", "Control"],
            colors=["U", "Mono-Blue"],
            tags=["updated", "multi-format"],
        )

        datastore_with_deck.update_deck(updated_deck)

        loaded = datastore_with_deck.load_deck("test_deck_001")
        assert loaded is not None
        assert loaded.deck_name == "Updated Deck Name"
        assert loaded.format == ["Pauper", "Modern", "Legacy"]
        assert loaded.archetype == ["Tempo", "Control"]
        assert loaded.colors == ["U", "Mono-Blue"]
        assert loaded.tags == ["updated", "multi-format"]

    def test_update_deck_format_only(self, datastore_with_deck: MockDataStore) -> None:
        """Test updating only the format field."""
        original = datastore_with_deck.load_deck("test_deck_001")
        assert original is not None

        # Update only format
        updated = DeckData(
            deck_id=original.deck_id,
            deck_name=original.deck_name,
            main_deck=original.main_deck,
            sideboard=original.sideboard,
            format=["Modern", "Pioneer"],  # Changed
            archetype=original.archetype,  # Unchanged
            colors=original.colors,  # Unchanged
            tags=original.tags,  # Unchanged
        )

        datastore_with_deck.update_deck(updated)

        loaded = datastore_with_deck.load_deck("test_deck_001")
        assert loaded is not None
        assert loaded.format == ["Modern", "Pioneer"]
        assert loaded.archetype == ["Tempo"]  # Should remain unchanged
        assert loaded.colors == ["U"]  # Should remain unchanged
        assert loaded.tags == ["test"]  # Should remain unchanged

    def test_update_deck_add_colors_and_tags(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test adding colors and tags to a deck that had none."""
        # Create deck with empty colors and tags
        minimal_deck = DeckData(
            deck_id="minimal_deck",
            deck_name="Minimal",
            main_deck=["Island"] * 60,
            sideboard=[],
            format=["Pauper"],
            archetype=["Control"],
            colors=[],
            tags=[],
        )
        datastore_with_deck.save_deck(minimal_deck)

        # Update to add colors and tags
        updated = DeckData(
            deck_id="minimal_deck",
            deck_name="Minimal",
            main_deck=["Island"] * 60,
            sideboard=[],
            format=["Pauper"],
            archetype=["Control"],
            colors=["U", "Mono-Blue"],
            tags=["permission", "card-draw"],
        )

        datastore_with_deck.update_deck(updated)

        loaded = datastore_with_deck.load_deck("minimal_deck")
        assert loaded is not None
        assert loaded.colors == ["U", "Mono-Blue"]
        assert loaded.tags == ["permission", "card-draw"]

    def test_update_deck_clear_metadata(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test clearing metadata by setting to empty lists."""
        original = datastore_with_deck.load_deck("test_deck_001")
        assert original is not None

        # Clear all metadata
        updated = DeckData(
            deck_id=original.deck_id,
            deck_name=original.deck_name,
            main_deck=original.main_deck,
            sideboard=original.sideboard,
            format=[],
            archetype=[],
            colors=[],
            tags=[],
        )

        datastore_with_deck.update_deck(updated)

        loaded = datastore_with_deck.load_deck("test_deck_001")
        assert loaded is not None
        assert loaded.format == []
        assert loaded.archetype == []
        assert loaded.colors == []
        assert loaded.tags == []

    def test_update_deck_preserves_main_deck_and_sideboard(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test that updating metadata doesn't affect main deck or sideboard."""
        original = datastore_with_deck.load_deck("test_deck_001")
        assert original is not None
        original_main = original.main_deck.copy()
        original_side = original.sideboard.copy()

        # Update only metadata
        updated = DeckData(
            deck_id=original.deck_id,
            deck_name=original.deck_name,
            main_deck=original.main_deck,
            sideboard=original.sideboard,
            format=["Modern"],
            archetype=["Aggro"],
            colors=["R"],
            tags=["burn"],
        )

        datastore_with_deck.update_deck(updated)

        loaded = datastore_with_deck.load_deck("test_deck_001")
        assert loaded is not None
        assert loaded.main_deck == original_main
        assert loaded.sideboard == original_side

    def test_update_deck_nonexistent_deck_raises_error(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test that updating a non-existent deck raises an error."""
        nonexistent_deck = DeckData(
            deck_id="does_not_exist",
            deck_name="Ghost Deck",
            main_deck=["Island"] * 60,
            sideboard=[],
            format=["Pauper"],
            archetype=["Control"],
            colors=["U"],
            tags=[],
        )

        with pytest.raises(ValueError, match="Deck not found"):
            datastore_with_deck.update_deck(nonexistent_deck)

    def test_update_deck_preserves_total_games(
        self, datastore_with_deck: MockDataStore
    ) -> None:
        """Test that updating metadata preserves the total_games count."""
        # Create deck with game count
        deck_with_games = DeckData(
            deck_id="played_deck",
            deck_name="Played Deck",
            main_deck=["Mountain"] * 60,
            sideboard=[],
            total_games=42,
            format=["Pauper"],
            archetype=["Aggro"],
            colors=["R"],
            tags=["burn"],
        )
        datastore_with_deck.save_deck(deck_with_games)

        # Update metadata
        updated = DeckData(
            deck_id="played_deck",
            deck_name="Played Deck",
            main_deck=["Mountain"] * 60,
            sideboard=[],
            total_games=42,  # Should remain 42
            format=["Modern"],  # Changed
            archetype=["Aggro"],
            colors=["R"],
            tags=["burn"],
        )

        datastore_with_deck.update_deck(updated)

        loaded = datastore_with_deck.load_deck("played_deck")
        assert loaded is not None
        assert loaded.total_games == 42
        assert loaded.format == ["Modern"]


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
