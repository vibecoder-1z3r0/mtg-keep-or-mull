"""Tests for the MockDataStore implementation."""

from datetime import datetime

from mtg_keep_or_mull.datastore import MockDataStore
from mtg_keep_or_mull.models import DeckData, HandDecisionData


class TestMockDataStore:
    """Test cases for MockDataStore."""

    def test_save_and_load_deck(self) -> None:
        """Test saving and loading a deck."""
        store = MockDataStore()
        deck = DeckData(
            deck_id="test_deck_1",
            deck_name="Test Deck",
            main_deck=["Island", "Island", "Counterspell", "Counterspell"],
            sideboard=["Hydroblast", "Hydroblast"],
            total_games=0,
        )

        # Save deck
        saved_id = store.save_deck(deck)
        assert saved_id == "test_deck_1"

        # Load deck
        loaded_deck = store.load_deck("test_deck_1")
        assert loaded_deck is not None
        assert loaded_deck.deck_id == "test_deck_1"
        assert loaded_deck.deck_name == "Test Deck"
        assert len(loaded_deck.main_deck) == 4
        assert len(loaded_deck.sideboard) == 2

    def test_load_nonexistent_deck(self) -> None:
        """Test loading a deck that doesn't exist."""
        store = MockDataStore()
        result = store.load_deck("nonexistent")
        assert result is None

    def test_list_decks(self) -> None:
        """Test listing all deck IDs."""
        store = MockDataStore()

        # Initially empty
        assert not store.list_decks()

        # Add decks
        deck1 = DeckData(deck_id="deck1", main_deck=["Island"])
        deck2 = DeckData(deck_id="deck2", main_deck=["Forest"])
        store.save_deck(deck1)
        store.save_deck(deck2)

        # List should contain both
        deck_ids = store.list_decks()
        assert len(deck_ids) == 2
        assert "deck1" in deck_ids
        assert "deck2" in deck_ids

    def test_save_hand_decision(self) -> None:
        """Test saving a hand decision."""
        store = MockDataStore()
        decision = HandDecisionData(
            hand_signature="Counterspell,Island,Island",
            hand_display=["Island", "Counterspell", "Island"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=2,
            on_play=True,
            timestamp=datetime(2025, 11, 22, 10, 30),
            deck_id="test_deck",
        )

        store.save_hand_decision(decision)

        # Verify it was saved
        decisions = store.get_decisions_for_deck("test_deck")
        assert len(decisions) == 1
        assert decisions[0].hand_signature == "Counterspell,Island,Island"
        assert decisions[0].decision == "keep"

    def test_get_hand_statistics_no_data(self) -> None:
        """Test getting statistics for a hand with no recorded decisions."""
        store = MockDataStore()
        stats = store.get_hand_statistics("Brainstorm,Island,Island")
        assert stats is None

    def test_get_hand_statistics_with_data(self) -> None:
        """Test getting statistics for a hand with recorded decisions."""
        store = MockDataStore()

        # Add multiple decisions for the same hand
        hand_sig = "Counterspell,Island,Island"
        for i in range(8):
            decision = HandDecisionData(
                hand_signature=hand_sig,
                hand_display=["Island", "Counterspell", "Island"],
                mulligan_count=0,
                decision="keep",
                lands_in_hand=2,
                on_play=True,
                timestamp=datetime.now(),
                deck_id=f"deck{i}",
            )
            store.save_hand_decision(decision)

        # Add 2 mulligan decisions
        for i in range(2):
            decision = HandDecisionData(
                hand_signature=hand_sig,
                hand_display=["Island", "Island", "Counterspell"],
                mulligan_count=0,
                decision="mull",
                lands_in_hand=2,
                on_play=True,
                timestamp=datetime.now(),
                deck_id=f"deck{i}",
            )
            store.save_hand_decision(decision)

        # Get statistics
        stats = store.get_hand_statistics(hand_sig)
        assert stats is not None
        assert stats.hand_signature == hand_sig
        assert stats.times_kept == 8
        assert stats.times_mulled == 2
        assert stats.keep_percentage == 80.0

    def test_get_all_hand_statistics(self) -> None:
        """Test getting statistics for all hands."""
        store = MockDataStore()

        # Add decisions for two different hands
        hand1 = HandDecisionData(
            hand_signature="Brainstorm,Island",
            hand_display=["Island", "Brainstorm"],
            mulligan_count=0,
            decision="keep",
            lands_in_hand=1,
            on_play=True,
            timestamp=datetime.now(),
            deck_id="deck1",
        )
        hand2 = HandDecisionData(
            hand_signature="Forest,Llanowar Elves",
            hand_display=["Forest", "Llanowar Elves"],
            mulligan_count=0,
            decision="mull",
            lands_in_hand=1,
            on_play=False,
            timestamp=datetime.now(),
            deck_id="deck2",
        )

        store.save_hand_decision(hand1)
        store.save_hand_decision(hand2)

        # Get all statistics
        all_stats = store.get_all_hand_statistics()
        assert len(all_stats) == 2

        signatures = [s.hand_signature for s in all_stats]
        assert "Brainstorm,Island" in signatures
        assert "Forest,Llanowar Elves" in signatures

    def test_get_decisions_for_deck_empty(self) -> None:
        """Test getting decisions for a deck with no recorded decisions."""
        store = MockDataStore()
        decisions = store.get_decisions_for_deck("nonexistent_deck")
        assert decisions == []

    def test_get_decisions_for_deck_with_data(self) -> None:
        """Test getting all decisions for a specific deck."""
        store = MockDataStore()

        # Add decisions for multiple decks
        for i in range(3):
            decision = HandDecisionData(
                hand_signature=f"hand_{i}",
                hand_display=[f"Card{i}"],
                mulligan_count=0,
                decision="keep",
                lands_in_hand=0,
                on_play=True,
                timestamp=datetime.now(),
                deck_id="deck_a",
            )
            store.save_hand_decision(decision)

        for i in range(2):
            decision = HandDecisionData(
                hand_signature=f"hand_{i}",
                hand_display=[f"Card{i}"],
                mulligan_count=0,
                decision="mull",
                lands_in_hand=0,
                on_play=True,
                timestamp=datetime.now(),
                deck_id="deck_b",
            )
            store.save_hand_decision(decision)

        # Get decisions for deck_a only
        deck_a_decisions = store.get_decisions_for_deck("deck_a")
        assert len(deck_a_decisions) == 3
        assert all(d.deck_id == "deck_a" for d in deck_a_decisions)

        # Get decisions for deck_b only
        deck_b_decisions = store.get_decisions_for_deck("deck_b")
        assert len(deck_b_decisions) == 2
        assert all(d.deck_id == "deck_b" for d in deck_b_decisions)


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
