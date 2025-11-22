"""Tests for JSONDataStore implementation."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from mtg_keep_or_mull.datastore import JSONDataStore
from mtg_keep_or_mull.models import DeckData, HandDecisionData


class TestJSONDataStore:
    """Test suite for JSONDataStore class."""

    @pytest.fixture
    def temp_data_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def datastore(self, temp_data_dir: Path) -> JSONDataStore:
        """Create a JSONDataStore instance with temp directory."""
        return JSONDataStore(base_path=temp_data_dir)

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

    def test_initialization_creates_directories(self, temp_data_dir: Path) -> None:
        """Test that JSONDataStore creates necessary directories on init."""
        # When: Create a JSONDataStore
        store = JSONDataStore(base_path=temp_data_dir)

        # Then: Directories should exist
        assert store.decks_dir.exists()
        assert store.decisions_dir.exists()
        assert store.decks_dir == temp_data_dir / "decks"
        assert store.decisions_dir == temp_data_dir / "decisions"

    def test_save_deck_creates_file(
        self, datastore: JSONDataStore, sample_deck: DeckData, temp_data_dir: Path
    ) -> None:
        """Test that save_deck creates a JSON file with correct data."""
        # When: Save a deck
        deck_id = datastore.save_deck(sample_deck)

        # Then: File should exist and contain correct data
        assert deck_id == "test_deck_001"
        deck_file = temp_data_dir / "decks" / "test_deck_001.json"
        assert deck_file.exists()

        # Verify file content
        with open(deck_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["deck_id"] == "test_deck_001"
        assert data["deck_name"] == "Test Deck"
        assert data["main_deck"] == ["Island", "Island", "Brainstorm", "Counterspell"]
        assert data["sideboard"] == ["Hydroblast", "Annul"]
        assert data["total_games"] == 5

    def test_load_deck_returns_deck_data(
        self, datastore: JSONDataStore, sample_deck: DeckData
    ) -> None:
        """Test that load_deck retrieves saved deck data."""
        # Given: A saved deck
        datastore.save_deck(sample_deck)

        # When: Load the deck
        loaded_deck = datastore.load_deck("test_deck_001")

        # Then: Should return correct DeckData
        assert loaded_deck is not None
        assert loaded_deck.deck_id == sample_deck.deck_id
        assert loaded_deck.deck_name == sample_deck.deck_name
        assert loaded_deck.main_deck == sample_deck.main_deck
        assert loaded_deck.sideboard == sample_deck.sideboard
        assert loaded_deck.total_games == sample_deck.total_games

    def test_load_deck_returns_none_when_not_found(self, datastore: JSONDataStore) -> None:
        """Test that load_deck returns None for non-existent deck."""
        # When: Try to load a deck that doesn't exist
        result = datastore.load_deck("nonexistent_deck")

        # Then: Should return None
        assert result is None

    def test_list_decks_returns_all_deck_ids(
        self, datastore: JSONDataStore, sample_deck: DeckData
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

    def test_list_decks_returns_empty_list_when_no_decks(self, datastore: JSONDataStore) -> None:
        """Test that list_decks returns empty list when no decks saved."""
        # When: List decks with no saved decks
        deck_ids = datastore.list_decks()

        # Then: Should return empty list
        assert deck_ids == []

    def test_save_hand_decision_creates_file(
        self, datastore: JSONDataStore, sample_decision: HandDecisionData, temp_data_dir: Path
    ) -> None:
        """Test that save_hand_decision creates a JSON file."""
        # When: Save a hand decision
        datastore.save_hand_decision(sample_decision)

        # Then: File should exist
        decisions_file = temp_data_dir / "decisions" / "test_deck_001.json"
        assert decisions_file.exists()

        # Verify file content
        with open(decisions_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["hand_signature"] == "Brainstorm,Counterspell,Island,Island"
        assert data[0]["decision"] == "keep"

    def test_save_hand_decision_appends_to_existing_file(
        self, datastore: JSONDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that save_hand_decision appends to existing decisions."""
        # Given: One saved decision
        datastore.save_hand_decision(sample_decision)

        # When: Save another decision for the same deck
        decision2 = HandDecisionData(
            hand_signature="Brainstorm,Island,Island,Island,Island,Island,Island",
            hand_display=["Island"] * 6 + ["Brainstorm"],
            mulligan_count=0,
            decision="mull",
            lands_in_hand=6,
            on_play=True,
            timestamp=datetime(2025, 11, 22, 10, 35, 0),
            deck_id="test_deck_001",
        )
        datastore.save_hand_decision(decision2)

        # Then: Both decisions should be in the file
        decisions = datastore.get_decisions_for_deck("test_deck_001")
        assert len(decisions) == 2
        assert decisions[0].decision == "keep"
        assert decisions[1].decision == "mull"

    def test_get_decisions_for_deck_returns_all_decisions(
        self, datastore: JSONDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that get_decisions_for_deck returns all saved decisions."""
        # Given: Multiple saved decisions
        datastore.save_hand_decision(sample_decision)
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

        # When: Get all decisions for the deck
        decisions = datastore.get_decisions_for_deck("test_deck_001")

        # Then: Should return all decisions
        assert len(decisions) == 2
        assert all(isinstance(d, HandDecisionData) for d in decisions)
        assert decisions[0].hand_signature == "Brainstorm,Counterspell,Island,Island"
        assert decisions[1].hand_signature == "Island,Island,Island,Island,Island,Island,Island"

    def test_get_decisions_for_deck_returns_empty_list_when_no_decisions(
        self, datastore: JSONDataStore
    ) -> None:
        """Test that get_decisions_for_deck returns empty list for unknown deck."""
        # When: Get decisions for a deck with no decisions
        decisions = datastore.get_decisions_for_deck("nonexistent_deck")

        # Then: Should return empty list
        assert decisions == []

    def test_get_hand_statistics_calculates_stats(
        self, datastore: JSONDataStore, sample_decision: HandDecisionData
    ) -> None:
        """Test that get_hand_statistics aggregates decisions correctly."""
        # Given: Multiple decisions for the same hand signature
        datastore.save_hand_decision(sample_decision)

        # Add more decisions with same signature
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
        self, datastore: JSONDataStore
    ) -> None:
        """Test that get_hand_statistics returns None for unknown hand."""
        # When: Get statistics for a hand with no decisions
        stats = datastore.get_hand_statistics("Unknown,Hand,Signature")

        # Then: Should return None
        assert stats is None

    def test_get_all_hand_statistics_returns_all_unique_hands(
        self, datastore: JSONDataStore
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

    def test_json_files_are_formatted_correctly(
        self, datastore: JSONDataStore, sample_deck: DeckData, temp_data_dir: Path
    ) -> None:
        """Test that JSON files are written with proper formatting."""
        # When: Save data
        datastore.save_deck(sample_deck)

        # Then: File should be properly formatted (indented)
        deck_file = temp_data_dir / "decks" / "test_deck_001.json"
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Should have newlines and indentation (not single-line JSON)
        assert "\n" in content
        assert "  " in content  # Indentation


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
