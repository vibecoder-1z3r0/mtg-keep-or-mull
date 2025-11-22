"""Tests for SQLiteDataStore implementation."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mtg_keep_or_mull.datastore import SQLiteDataStore
from mtg_keep_or_mull.models import DeckData, HandDecisionData


class TestSQLiteDataStore:
    """Test suite for SQLiteDataStore class."""

    @pytest.fixture
    def temp_db_file(self) -> Path:
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            yield Path(tmpfile.name)
            # Cleanup
            Path(tmpfile.name).unlink(missing_ok=True)

    @pytest.fixture
    def datastore(self, temp_db_file: Path) -> SQLiteDataStore:
        """Create a SQLiteDataStore instance with temp database."""
        return SQLiteDataStore(db_path=temp_db_file)

    @pytest.fixture
    def sample_deck(self) -> DeckData:
        """Create a sample deck for testing."""
        return DeckData(
            deck_id="test_deck_001",
            deck_name="Test Deck",
            main_deck=["Island", "Island", "Brainstorm", "Counterspell"],
            sideboard=["Hydroblast", "Annul"],
            total_games=5,
        )

    @pytest.fixture
    def sample_decision(self) -> HandDecisionData:
        """Create a sample hand decision for testing."""
        return HandDecisionData(
            hand_signature="Brainstorm,Counterspell,Island,Island",
            hand_display=["Island", "Brainstorm", "Island", "Counterspell"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=2,
            on_play=True,
            timestamp=datetime(2025, 11, 22, 10, 30, 0),
            deck_id="test_deck_001",
        )

    def test_initialization_creates_tables(self, temp_db_file: Path) -> None:
        """Test that SQLiteDataStore creates necessary tables on init."""
        # When: Create a SQLiteDataStore
        store = SQLiteDataStore(db_path=temp_db_file)

        # Then: Database file should exist
        assert temp_db_file.exists()

        # Verify tables exist by querying them
        import sqlite3

        conn = sqlite3.connect(temp_db_file)
        cursor = conn.cursor()

        # Check decks table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decks'"
        )
        assert cursor.fetchone() is not None

        # Check hand_decisions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hand_decisions'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_save_and_load_deck(
        self, datastore: SQLiteDataStore, sample_deck: DeckData
    ) -> None:
        """Test that save_deck and load_deck work correctly."""
        # When: Save a deck
        deck_id = datastore.save_deck(sample_deck)

        # Then: Can load it back
        assert deck_id == "test_deck_001"
        loaded_deck = datastore.load_deck("test_deck_001")

        assert loaded_deck is not None
        assert loaded_deck.deck_id == sample_deck.deck_id
        assert loaded_deck.deck_name == sample_deck.deck_name
        assert loaded_deck.main_deck == sample_deck.main_deck
        assert loaded_deck.sideboard == sample_deck.sideboard
        assert loaded_deck.total_games == sample_deck.total_games

    def test_load_deck_returns_none_when_not_found(
        self, datastore: SQLiteDataStore
    ) -> None:
        """Test that load_deck returns None for non-existent deck."""
        # When: Try to load a deck that doesn't exist
        result = datastore.load_deck("nonexistent_deck")

        # Then: Should return None
        assert result is None

    def test_list_decks_returns_all_deck_ids(
        self, datastore: SQLiteDataStore, sample_deck: DeckData
    ) -> None:
        """Test that list_decks returns all saved deck IDs."""
        # Given: Multiple saved decks
        datastore.save_deck(sample_deck)
        deck2 = DeckData(deck_id="test_deck_002", main_deck=["Mountain"] * 20)
        datastore.save_deck(deck2)

        # When: List all decks
        deck_ids = datastore.list_decks()

        # Then: Should return both deck IDs
        assert sorted(deck_ids) == ["test_deck_001", "test_deck_002"]

    def test_list_decks_returns_empty_list_when_no_decks(
        self, datastore: SQLiteDataStore
    ) -> None:
        """Test that list_decks returns empty list when no decks saved."""
        # When: List decks with no saved decks
        deck_ids = datastore.list_decks()

        # Then: Should return empty list
        assert deck_ids == []

    def test_save_hand_decision(
        self, datastore: SQLiteDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that save_hand_decision stores decision correctly."""
        # When: Save a hand decision
        datastore.save_hand_decision(sample_decision)

        # Then: Can retrieve it
        decisions = datastore.get_decisions_for_deck("test_deck_001")
        assert len(decisions) == 1
        assert decisions[0].hand_signature == sample_decision.hand_signature
        assert decisions[0].decision == sample_decision.decision

    def test_save_multiple_hand_decisions(
        self, datastore: SQLiteDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that multiple hand decisions can be saved."""
        # Given: One saved decision
        datastore.save_hand_decision(sample_decision)

        # When: Save another decision
        decision2 = HandDecisionData(
            hand_signature="Island,Island,Island,Island,Island,Island,Island",
            hand_display=["Island"] * 7,
            mulligan_count=0,
            decision="mull",
            lands_in_hand=7,
            on_play=False,
            timestamp=datetime(2025, 11, 22, 11, 0, 0),
            deck_id="test_deck_001",
        )
        datastore.save_hand_decision(decision2)

        # Then: Both decisions should be stored
        decisions = datastore.get_decisions_for_deck("test_deck_001")
        assert len(decisions) == 2
        assert decisions[0].decision == "keep"
        assert decisions[1].decision == "mull"

    def test_get_decisions_for_deck_returns_empty_list_when_no_decisions(
        self, datastore: SQLiteDataStore
    ) -> None:
        """Test that get_decisions_for_deck returns empty list for unknown deck."""
        # When: Get decisions for a deck with no decisions
        decisions = datastore.get_decisions_for_deck("nonexistent_deck")

        # Then: Should return empty list
        assert decisions == []

    def test_get_hand_statistics_calculates_stats(
        self, datastore: SQLiteDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that get_hand_statistics aggregates decisions correctly."""
        # Given: Multiple decisions for the same hand signature
        datastore.save_hand_decision(sample_decision)

        decision2 = HandDecisionData(
            hand_signature="Brainstorm,Counterspell,Island,Island",
            hand_display=["Brainstorm", "Island", "Counterspell", "Island"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=2,
            on_play=False,
            timestamp=datetime(2025, 11, 22, 11, 0, 0),
            deck_id="test_deck_001",
        )
        datastore.save_hand_decision(decision2)

        decision3 = HandDecisionData(
            hand_signature="Brainstorm,Counterspell,Island,Island",
            hand_display=["Island", "Island", "Brainstorm", "Counterspell"],
            mulligan_count=1,
            decision="mull",
            lands_in_hand=2,
            on_play=True,
            timestamp=datetime(2025, 11, 22, 12, 0, 0),
            deck_id="test_deck_001",
        )
        datastore.save_hand_decision(decision3)

        # When: Get statistics for this hand
        stats = datastore.get_hand_statistics("Brainstorm,Counterspell,Island,Island")

        # Then: Should calculate correct statistics
        assert stats is not None
        assert stats.hand_signature == "Brainstorm,Counterspell,Island,Island"
        assert stats.times_kept == 2
        assert stats.times_mulled == 1
        assert stats.total_decisions == 3
        assert stats.keep_percentage == pytest.approx(66.67, rel=0.01)

    def test_get_hand_statistics_returns_none_when_no_decisions(
        self, datastore: SQLiteDataStore
    ) -> None:
        """Test that get_hand_statistics returns None for unknown hand."""
        # When: Get statistics for a hand with no decisions
        stats = datastore.get_hand_statistics("Unknown,Hand,Signature")

        # Then: Should return None
        assert stats is None

    def test_get_all_hand_statistics_returns_all_unique_hands(
        self, datastore: SQLiteDataStore
    ) -> None:
        """Test that get_all_hand_statistics returns stats for all unique hands."""
        # Given: Decisions for multiple different hands
        decision1 = HandDecisionData(
            hand_signature="Brainstorm,Island,Island",
            hand_display=["Island", "Island", "Brainstorm"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=2,
            on_play=True,
            timestamp=datetime.now(),
            deck_id="test_deck",
        )
        decision2 = HandDecisionData(
            hand_signature="Brainstorm,Island,Island",
            hand_display=["Brainstorm", "Island", "Island"],
            mulligan_count=0,
            decision="mull",
            lands_in_hand=2,
            on_play=False,
            timestamp=datetime.now(),
            deck_id="test_deck",
        )
        decision3 = HandDecisionData(
            hand_signature="Counterspell,Island,Island",
            hand_display=["Island", "Counterspell", "Island"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=2,
            on_play=True,
            timestamp=datetime.now(),
            deck_id="test_deck",
        )

        datastore.save_hand_decision(decision1)
        datastore.save_hand_decision(decision2)
        datastore.save_hand_decision(decision3)

        # When: Get all hand statistics
        all_stats = datastore.get_all_hand_statistics()

        # Then: Should return stats for both unique hands
        assert len(all_stats) == 2
        signatures = {stat.hand_signature for stat in all_stats}
        assert signatures == {"Brainstorm,Island,Island", "Counterspell,Island,Island"}

    def test_update_existing_deck(
        self, datastore: SQLiteDataStore, sample_deck: DeckData
    ) -> None:
        """Test that saving a deck with same ID updates it."""
        # Given: A saved deck
        datastore.save_deck(sample_deck)

        # When: Save a deck with the same ID but different data
        updated_deck = DeckData(
            deck_id="test_deck_001",
            deck_name="Updated Deck Name",
            main_deck=["Forest"] * 20,
            sideboard=[],
            total_games=10,
        )
        datastore.save_deck(updated_deck)

        # Then: Should load the updated version
        loaded_deck = datastore.load_deck("test_deck_001")
        assert loaded_deck is not None
        assert loaded_deck.deck_name == "Updated Deck Name"
        assert loaded_deck.main_deck == ["Forest"] * 20
        assert loaded_deck.total_games == 10

    def test_connection_closes_properly(self, temp_db_file: Path) -> None:
        """Test that database connections are managed properly."""
        # When: Create multiple stores with same database
        store1 = SQLiteDataStore(db_path=temp_db_file)
        store2 = SQLiteDataStore(db_path=temp_db_file)

        # Then: Both should work independently
        deck1 = DeckData(deck_id="deck_001", main_deck=["Island"] * 20)
        deck2 = DeckData(deck_id="deck_002", main_deck=["Mountain"] * 20)

        store1.save_deck(deck1)
        store2.save_deck(deck2)

        # Both stores should see both decks
        assert len(store1.list_decks()) == 2
        assert len(store2.list_decks()) == 2


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
