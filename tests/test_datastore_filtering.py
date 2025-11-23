"""Tests for DataStore filtering functionality (list-based metadata)."""

import pytest

from mtg_keep_or_mull.datastore import MockDataStore
from mtg_keep_or_mull.models import DeckData


class TestDataStoreFiltering:
    """Test filtering decks by format, archetype, colors, and tags using list-based fields."""

    @pytest.fixture
    def datastore_with_decks(self) -> MockDataStore:
        """Create a datastore populated with various decks using list-based metadata."""
        store = MockDataStore()

        # Mono-U Terror: Pauper (but also legal in other formats)
        store.save_deck(
            DeckData(
                deck_id="mono_u_terror",
                deck_name="Mono-U Terror",
                main_deck=["Island"] * 60,
                sideboard=["Hydroblast"] * 15,
                format=["Pauper", "Modern", "Legacy", "Vintage"],
                archetype=["Tempo", "Control"],
                colors=["U", "Mono-Blue"],
                tags=["Delver", "permission", "cantrips"],
            )
        )

        # Pauper Elves: Combo deck
        store.save_deck(
            DeckData(
                deck_id="pauper_elves",
                deck_name="Pauper Elves",
                main_deck=["Forest"] * 60,
                sideboard=["Natural State"] * 15,
                format=["Pauper"],
                archetype=["Combo", "Aggro"],
                colors=["G", "Mono-Green"],
                tags=["tribal", "elves", "mana-dorks"],
            )
        )

        # Pauper Burn: Pure Aggro
        store.save_deck(
            DeckData(
                deck_id="pauper_burn",
                deck_name="Pauper Burn",
                main_deck=["Mountain"] * 60,
                sideboard=["Pyroblast"] * 15,
                format=["Pauper"],
                archetype=["Aggro"],
                colors=["R", "Mono-Red"],
                tags=["burn", "direct-damage"],
            )
        )

        # Modern Burn: Similar to Pauper but Modern-only
        store.save_deck(
            DeckData(
                deck_id="modern_burn",
                deck_name="Modern Burn",
                main_deck=["Mountain"] * 60,
                sideboard=["Leyline of the Void"] * 15,
                format=["Modern"],
                archetype=["Aggro"],
                colors=["R"],
                tags=["burn"],
            )
        )

        # Modern Tron: Combo/Control hybrid
        store.save_deck(
            DeckData(
                deck_id="modern_tron",
                deck_name="Modern Tron",
                main_deck=["Urza's Tower"] * 60,
                sideboard=["Nature's Claim"] * 15,
                format=["Modern"],
                archetype=["Combo", "Control"],
                colors=["Colorless"],
                tags=["ramp", "big-mana"],
            )
        )

        # Standard Control: Blue-based control
        store.save_deck(
            DeckData(
                deck_id="standard_control",
                deck_name="Standard Control",
                main_deck=["Island"] * 60,
                sideboard=["Negate"] * 15,
                format=["Standard", "Pioneer", "Modern"],
                archetype=["Control"],
                colors=["U"],
                tags=["permission", "card-draw"],
            )
        )

        # Grixis Storm: Multi-color combo
        store.save_deck(
            DeckData(
                deck_id="grixis_storm",
                deck_name="Grixis Storm",
                main_deck=["Island", "Swamp", "Mountain"] * 20,
                sideboard=[],
                format=["Pauper", "Modern"],
                archetype=["Combo"],
                colors=["Grixis", "U", "B", "R", "UBR"],
                tags=["Storm", "spell-based", "graveyard"],
            )
        )

        return store

    def test_list_decks_filtered_by_single_format(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test filtering decks that contain a specific format in their format list."""
        # Pauper-legal decks
        pauper_decks = datastore_with_decks.list_decks_filtered(format="Pauper")
        assert len(pauper_decks) == 4  # mono_u, elves, burn, grixis
        assert "mono_u_terror" in pauper_decks
        assert "pauper_elves" in pauper_decks
        assert "pauper_burn" in pauper_decks
        assert "grixis_storm" in pauper_decks

        # Modern-legal decks
        modern_decks = datastore_with_decks.list_decks_filtered(format="Modern")
        assert len(modern_decks) == 5  # mono_u, modern_burn, tron, standard, grixis
        assert "mono_u_terror" in modern_decks
        assert "modern_burn" in modern_decks

        # Standard-only
        standard_decks = datastore_with_decks.list_decks_filtered(format="Standard")
        assert len(standard_decks) == 1
        assert "standard_control" in standard_decks

    def test_list_decks_filtered_by_single_archetype(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test filtering decks that contain a specific archetype in their archetype list."""
        # Aggro decks
        aggro_decks = datastore_with_decks.list_decks_filtered(archetype="Aggro")
        assert len(aggro_decks) == 3  # elves, pauper_burn, modern_burn
        assert "pauper_elves" in aggro_decks
        assert "pauper_burn" in aggro_decks
        assert "modern_burn" in aggro_decks

        # Combo decks
        combo_decks = datastore_with_decks.list_decks_filtered(archetype="Combo")
        assert len(combo_decks) == 3  # elves, tron, grixis
        assert "pauper_elves" in combo_decks
        assert "modern_tron" in combo_decks
        assert "grixis_storm" in combo_decks

        # Control decks
        control_decks = datastore_with_decks.list_decks_filtered(archetype="Control")
        assert len(control_decks) == 3  # mono_u, tron, standard
        assert "mono_u_terror" in control_decks
        assert "modern_tron" in control_decks
        assert "standard_control" in control_decks

        # Tempo decks
        tempo_decks = datastore_with_decks.list_decks_filtered(archetype="Tempo")
        assert len(tempo_decks) == 1
        assert "mono_u_terror" in tempo_decks

    def test_list_decks_filtered_by_colors(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering decks by color identity."""
        # Decks with U (blue)
        blue_decks = datastore_with_decks.list_decks_filtered(colors="U")
        assert len(blue_decks) == 3  # mono_u, standard, grixis
        assert "mono_u_terror" in blue_decks
        assert "standard_control" in blue_decks
        assert "grixis_storm" in blue_decks

        # Decks with Grixis identity
        grixis_decks = datastore_with_decks.list_decks_filtered(colors="Grixis")
        assert len(grixis_decks) == 1
        assert "grixis_storm" in grixis_decks

        # Mono-Green decks
        green_decks = datastore_with_decks.list_decks_filtered(colors="Mono-Green")
        assert len(green_decks) == 1
        assert "pauper_elves" in green_decks

    def test_list_decks_filtered_by_tags(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering decks by tags."""
        # Decks with burn tag
        burn_decks = datastore_with_decks.list_decks_filtered(tags="burn")
        assert len(burn_decks) == 2  # pauper_burn, modern_burn
        assert "pauper_burn" in burn_decks
        assert "modern_burn" in burn_decks

        # Decks with permission tag
        permission_decks = datastore_with_decks.list_decks_filtered(tags="permission")
        assert len(permission_decks) == 2  # mono_u, standard
        assert "mono_u_terror" in permission_decks
        assert "standard_control" in permission_decks

        # Decks with Storm tag
        storm_decks = datastore_with_decks.list_decks_filtered(tags="Storm")
        assert len(storm_decks) == 1
        assert "grixis_storm" in storm_decks

    def test_list_decks_filtered_by_multiple_criteria(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test filtering by multiple criteria (AND logic)."""
        # Pauper + Aggro
        pauper_aggro = datastore_with_decks.list_decks_filtered(format="Pauper", archetype="Aggro")
        assert len(pauper_aggro) == 2  # elves, burn
        assert "pauper_elves" in pauper_aggro
        assert "pauper_burn" in pauper_aggro

        # Modern + Combo
        modern_combo = datastore_with_decks.list_decks_filtered(format="Modern", archetype="Combo")
        assert len(modern_combo) == 2  # tron, grixis
        assert "modern_tron" in modern_combo
        assert "grixis_storm" in modern_combo

        # Pauper + Tempo
        pauper_tempo = datastore_with_decks.list_decks_filtered(format="Pauper", archetype="Tempo")
        assert len(pauper_tempo) == 1
        assert "mono_u_terror" in pauper_tempo

        # Format + Colors
        pauper_blue = datastore_with_decks.list_decks_filtered(format="Pauper", colors="U")
        assert len(pauper_blue) == 2  # mono_u, grixis
        assert "mono_u_terror" in pauper_blue
        assert "grixis_storm" in pauper_blue

        # Archetype + Tags
        combo_storm = datastore_with_decks.list_decks_filtered(archetype="Combo", tags="Storm")
        assert len(combo_storm) == 1
        assert "grixis_storm" in combo_storm

    def test_list_decks_filtered_all_criteria(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering by all four criteria simultaneously."""
        # Very specific filter
        result = datastore_with_decks.list_decks_filtered(
            format="Pauper", archetype="Combo", colors="Grixis", tags="Storm"
        )
        assert len(result) == 1
        assert "grixis_storm" in result

    def test_list_decks_filtered_no_match(self, datastore_with_decks: MockDataStore) -> None:
        """Test filtering with no matching decks."""
        # Non-existent format
        vintage_decks = datastore_with_decks.list_decks_filtered(format="Vintage")
        assert len(vintage_decks) == 1  # mono_u is Vintage-legal
        assert "mono_u_terror" in vintage_decks

        # Non-existent archetype
        midrange_decks = datastore_with_decks.list_decks_filtered(archetype="Midrange")
        assert len(midrange_decks) == 0

        # Impossible combination
        legacy_burn = datastore_with_decks.list_decks_filtered(format="Legacy", tags="ramp")
        assert len(legacy_burn) == 0

    def test_list_decks_filtered_no_filters_returns_all(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test that calling list_decks_filtered with no filters returns all decks."""
        all_decks = datastore_with_decks.list_decks_filtered()
        assert len(all_decks) == 7

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
            "grixis_storm",
        ]

    def test_get_random_deck_filtered_by_format(self, datastore_with_decks: MockDataStore) -> None:
        """Test getting a random deck filtered by format."""
        # Get multiple random decks to verify they're all from correct format
        pauper_decks_found = set()
        for _ in range(20):
            deck = datastore_with_decks.get_random_deck(format="Pauper")
            assert deck is not None
            assert "Pauper" in deck.format  # Check format IN list
            pauper_decks_found.add(deck.deck_id)

        # Should find at least 3 different pauper decks in 20 tries
        assert len(pauper_decks_found) >= 3

    def test_get_random_deck_filtered_by_archetype(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test getting a random deck filtered by archetype."""
        # Get multiple random decks to verify they're all from correct archetype
        aggro_decks_found = set()
        for _ in range(20):
            deck = datastore_with_decks.get_random_deck(archetype="Aggro")
            assert deck is not None
            assert "Aggro" in deck.archetype  # Check archetype IN list
            aggro_decks_found.add(deck.deck_id)

        # Should find all 3 aggro decks in 20 tries
        assert len(aggro_decks_found) == 3
        assert "pauper_elves" in aggro_decks_found
        assert "pauper_burn" in aggro_decks_found
        assert "modern_burn" in aggro_decks_found

    def test_get_random_deck_filtered_by_colors(self, datastore_with_decks: MockDataStore) -> None:
        """Test getting a random deck filtered by colors."""
        # Get blue decks
        blue_decks_found = set()
        for _ in range(15):
            deck = datastore_with_decks.get_random_deck(colors="U")
            assert deck is not None
            assert "U" in deck.colors
            blue_decks_found.add(deck.deck_id)

        # Should find multiple blue decks
        assert len(blue_decks_found) >= 2

    def test_get_random_deck_filtered_by_tags(self, datastore_with_decks: MockDataStore) -> None:
        """Test getting a random deck filtered by tags."""
        # Get permission decks
        for _ in range(10):
            deck = datastore_with_decks.get_random_deck(tags="permission")
            assert deck is not None
            assert "permission" in deck.tags
            assert deck.deck_id in ["mono_u_terror", "standard_control"]

    def test_get_random_deck_filtered_by_multiple_criteria(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test getting a random deck filtered by multiple criteria."""
        # Pauper + Combo
        pauper_combo_found = set()
        for _ in range(10):
            deck = datastore_with_decks.get_random_deck(format="Pauper", archetype="Combo")
            assert deck is not None
            assert "Pauper" in deck.format
            assert "Combo" in deck.archetype
            pauper_combo_found.add(deck.deck_id)

        # Should find elves and grixis
        assert len(pauper_combo_found) >= 2

    def test_get_random_deck_filtered_by_all_criteria(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test getting a random deck with all filter criteria."""
        # Very specific: should always return grixis_storm
        for _ in range(5):
            deck = datastore_with_decks.get_random_deck(
                format="Pauper", archetype="Combo", colors="Grixis", tags="Storm"
            )
            assert deck is not None
            assert deck.deck_id == "grixis_storm"
            assert "Pauper" in deck.format
            assert "Combo" in deck.archetype
            assert "Grixis" in deck.colors
            assert "Storm" in deck.tags

    def test_get_random_deck_no_match_returns_none(
        self, datastore_with_decks: MockDataStore
    ) -> None:
        """Test that get_random_deck returns None when no decks match filters."""
        deck = datastore_with_decks.get_random_deck(archetype="Midrange")
        assert deck is None

        deck = datastore_with_decks.get_random_deck(colors="Jeskai")
        assert deck is None

        deck = datastore_with_decks.get_random_deck(tags="nonexistent-tag")
        assert deck is None

        deck = datastore_with_decks.get_random_deck(format="Legacy", tags="ramp")
        assert deck is None

    def test_get_random_deck_empty_datastore(self) -> None:
        """Test that get_random_deck returns None for empty datastore."""
        store = MockDataStore()
        deck = store.get_random_deck()
        assert deck is None


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
