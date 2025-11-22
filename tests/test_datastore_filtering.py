"""Tests for DataStore filtering functionality (format and archetype)."""

import pytest

from mtg_keep_or_mull.datastore import MockDataStore
from mtg_keep_or_mull.models import DeckData


class TestDataStoreFiltering:
    """Test filtering decks by format and archetype."""

    @pytest.fixture
    def datastore_with_decks(self) -> MockDataStore:
        """Create a datastore populated with various decks."""
        store = MockDataStore()

        # Pauper decks
        store.save_deck(
            DeckData(
                deck_id="mono_u_terror",
                deck_name="Mono-U Terror",
                main_deck=["Island"] * 60,
                sideboard=["Hydroblast"] * 15,
                format="Pauper",
                archetype="Tempo",
            )
        )

        store.save_deck(
            DeckData(
                deck_id="pauper_elves",
                deck_name="Pauper Elves",
                main_deck=["Forest"] * 60,
                sideboard=["Natural State"] * 15,
                format="Pauper",
                archetype="Combo",
            )
        )

        store.save_deck(
            DeckData(
                deck_id="pauper_burn",
                deck_name="Pauper Burn",
                main_deck=["Mountain"] * 60,
                sideboard=["Pyroblast"] * 15,
                format="Pauper",
                archetype="Aggro",
            )
        )

        # Modern decks
        store.save_deck(
            DeckData(
                deck_id="modern_burn",
                deck_name="Modern Burn",
                main_deck=["Mountain"] * 60,
                sideboard=["Leyline of the Void"] * 15,
                format="Modern",
                archetype="Aggro",
            )
        )

        store.save_deck(
            DeckData(
                deck_id="modern_tron",
                deck_name="Modern Tron",
                main_deck=["Urza's Tower"] * 60,
                sideboard=["Nature's Claim"] * 15,
                format="Modern",
                archetype="Combo",
            )
        )

        # Standard deck
        store.save_deck(
            DeckData(
                deck_id="standard_control",
                deck_name="Standard Control",
                main_deck=["Island"] * 60,
                sideboard=["Negate"] * 15,
                format="Standard",
                archetype="Control",
            )
        )

        return store

    def test_list_decks_filtered_by_format(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering decks by format."""
        pauper_decks = datastore_with_decks.list_decks_filtered(format="Pauper")
        assert len(pauper_decks) == 3
        assert "mono_u_terror" in pauper_decks
        assert "pauper_elves" in pauper_decks
        assert "pauper_burn" in pauper_decks

        modern_decks = datastore_with_decks.list_decks_filtered(format="Modern")
        assert len(modern_decks) == 2
        assert "modern_burn" in modern_decks
        assert "modern_tron" in modern_decks

        standard_decks = datastore_with_decks.list_decks_filtered(format="Standard")
        assert len(standard_decks) == 1
        assert "standard_control" in standard_decks

    def test_list_decks_filtered_by_archetype(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering decks by archetype."""
        aggro_decks = datastore_with_decks.list_decks_filtered(archetype="Aggro")
        assert len(aggro_decks) == 2
        assert "pauper_burn" in aggro_decks
        assert "modern_burn" in aggro_decks

        combo_decks = datastore_with_decks.list_decks_filtered(archetype="Combo")
        assert len(combo_decks) == 2
        assert "pauper_elves" in combo_decks
        assert "modern_tron" in combo_decks

        control_decks = datastore_with_decks.list_decks_filtered(archetype="Control")
        assert len(control_decks) == 1
        assert "standard_control" in control_decks

        tempo_decks = datastore_with_decks.list_decks_filtered(archetype="Tempo")
        assert len(tempo_decks) == 1
        assert "mono_u_terror" in tempo_decks

    def test_list_decks_filtered_by_both_format_and_archetype(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test filtering decks by both format and archetype."""
        pauper_aggro = datastore_with_decks.list_decks_filtered(
            format="Pauper", archetype="Aggro"
        )
        assert len(pauper_aggro) == 1
        assert "pauper_burn" in pauper_aggro

        modern_combo = datastore_with_decks.list_decks_filtered(format="Modern", archetype="Combo")
        assert len(modern_combo) == 1
        assert "modern_tron" in modern_combo

        pauper_tempo = datastore_with_decks.list_decks_filtered(
            format="Pauper", archetype="Tempo"
        )
        assert len(pauper_tempo) == 1
        assert "mono_u_terror" in pauper_tempo

    def test_list_decks_filtered_no_match(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering with no matching decks."""
        vintage_decks = datastore_with_decks.list_decks_filtered(format="Vintage")
        assert len(vintage_decks) == 0

        midrange_decks = datastore_with_decks.list_decks_filtered(archetype="Midrange")
        assert len(midrange_decks) == 0

        legacy_burn = datastore_with_decks.list_decks_filtered(format="Legacy", archetype="Aggro")
        assert len(legacy_burn) == 0

    def test_list_decks_filtered_no_filters_returns_all(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test that calling list_decks_filtered with no filters returns all decks."""
        all_decks = datastore_with_decks.list_decks_filtered()
        assert len(all_decks) == 6

    def test_get_random_deck_no_filters(self, datastore_with_decks: MockDataStore) -> None:
        """Test getting a random deck with no filters."""
        deck = datastore_with_decks.get_random_deck()
        assert deck is not None
        assert deck.deck_id in [
            "mono_u_terror",
            "pauper_elves",
            "pauper_burn",
            "modern_burn",
            "modern_tron",
            "standard_control",
        ]

    def test_get_random_deck_filtered_by_format(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test getting a random deck filtered by format."""
        # Get multiple random decks to verify they're all from correct format
        pauper_decks_found = set()
        for _ in range(10):
            deck = datastore_with_decks.get_random_deck(format="Pauper")
            assert deck is not None
            assert deck.format == "Pauper"
            pauper_decks_found.add(deck.deck_id)

        # Should find at least 2 different pauper decks in 10 tries
        assert len(pauper_decks_found) >= 2

    def test_get_random_deck_filtered_by_archetype(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test getting a random deck filtered by archetype."""
        # Get multiple random decks to verify they're all from correct archetype
        aggro_decks_found = set()
        for _ in range(10):
            deck = datastore_with_decks.get_random_deck(archetype="Aggro")
            assert deck is not None
            assert deck.archetype == "Aggro"
            aggro_decks_found.add(deck.deck_id)

        # Should find both aggro decks in 10 tries
        assert len(aggro_decks_found) == 2
        assert "pauper_burn" in aggro_decks_found
        assert "modern_burn" in aggro_decks_found

    def test_get_random_deck_filtered_by_both(self, datastore_with_decks: MockDataStore) -> None:
        """Test getting a random deck filtered by both format and archetype."""
        # With only one match, should always return the same deck
        for _ in range(5):
            deck = datastore_with_decks.get_random_deck(format="Pauper", archetype="Tempo")
            assert deck is not None
            assert deck.deck_id == "mono_u_terror"
            assert deck.format == "Pauper"
            assert deck.archetype == "Tempo"

    def test_get_random_deck_no_match_returns_none(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test that get_random_deck returns None when no decks match filters."""
        deck = datastore_with_decks.get_random_deck(format="Vintage")
        assert deck is None

        deck = datastore_with_decks.get_random_deck(archetype="Midrange")
        assert deck is None

        deck = datastore_with_decks.get_random_deck(format="Legacy", archetype="Control")
        assert deck is None

    def test_get_random_deck_empty_datastore(self) -> None:
        """Test that get_random_deck returns None for empty datastore."""
        store = MockDataStore()
        deck = store.get_random_deck()
        assert deck is None


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
