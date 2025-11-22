"""Tests for the Deck class."""

from pathlib import Path

from mtg_keep_or_mull.card import Card
from mtg_keep_or_mull.deck import Deck


class TestDeck:
    """Test cases for Deck class."""

    def test_create_empty_deck(self) -> None:
        """Test creating an empty deck."""
        deck = Deck()
        assert deck.size() == 0

    def test_load_deck_from_file(self) -> None:
        """Test loading a deck from MTGO format file."""
        fixture_path = Path("tests/fixtures/decks/pauper_elves.txt")
        deck = Deck.from_file(str(fixture_path))

        # Pauper Elves has 60 main deck cards
        assert deck.size() == 60

        # Should have 15 sideboard cards (not in main deck)
        assert len(deck.sideboard) == 15

    def test_parse_mtgo_format(self) -> None:
        """Test parsing MTGO format with quantity expansion."""
        # Simple deck: 4 Islands, 3 Lightning Bolts
        deck_text = "4 Island\n3 Lightning Bolt\n"
        deck = Deck.from_text(deck_text)

        assert deck.size() == 7

        # Check cards were expanded correctly
        island_count = sum(1 for card in deck._cards if card.name == "Island")
        bolt_count = sum(1 for card in deck._cards if card.name == "Lightning Bolt")

        assert island_count == 4
        assert bolt_count == 3

    def test_parse_with_sideboard(self) -> None:
        """Test parsing deck with sideboard section."""
        deck_text = """4 Island
3 Counterspell

SIDEBOARD:
2 Hydroblast
1 Annul
"""
        deck = Deck.from_text(deck_text)

        # Main deck: 7 cards
        assert deck.size() == 7

        # Sideboard: 3 cards (stored, not in main deck)
        assert len(deck.sideboard) == 3
        assert deck.sideboard[0].name == "Hydroblast"
        assert deck.sideboard[1].name == "Hydroblast"
        assert deck.sideboard[2].name == "Annul"

    def test_shuffle_deck(self) -> None:
        """Test shuffling randomizes deck order."""
        # Create deck with known order
        cards = [Card(f"Card{i}") for i in range(20)]
        deck = Deck(cards)

        original_order = [c.name for c in deck._cards]

        # Shuffle
        deck.shuffle()

        shuffled_order = [c.name for c in deck._cards]

        # Order should be different (extremely unlikely to be same after shuffle)
        assert original_order != shuffled_order

        # But size should be same
        assert deck.size() == 20

    def test_draw_cards(self) -> None:
        """Test drawing cards from top of deck."""
        deck_text = "7 Island\n"
        deck = Deck.from_text(deck_text)

        # Draw 3 cards
        drawn = deck.draw(3)

        assert len(drawn) == 3
        assert deck.size() == 4  # 7 - 3 = 4 remaining

    def test_draw_too_many_cards(self) -> None:
        """Test drawing more cards than available."""
        deck_text = "3 Island\n"
        deck = Deck.from_text(deck_text)

        # Try to draw 5 cards when only 3 available
        drawn = deck.draw(5)

        # Should only get 3
        assert len(drawn) == 3
        assert deck.size() == 0

    def test_return_cards_to_deck(self) -> None:
        """Test returning cards to deck (shuffle back)."""
        deck_text = "10 Island\n"
        deck = Deck.from_text(deck_text)

        # Draw 5
        drawn = deck.draw(5)
        assert deck.size() == 5

        # Return them
        deck.return_cards(drawn)
        assert deck.size() == 10

    def test_put_cards_on_bottom(self) -> None:
        """Test putting cards on bottom (London Mulligan)."""
        # Create deck with specific cards
        cards = [Card("Island"), Card("Mountain"), Card("Forest"), Card("Plains"), Card("Swamp")]
        deck = Deck(cards)

        # Draw all 5
        hand = deck.draw(5)

        # Put 2 on bottom
        to_bottom = [hand[0], hand[1]]
        deck.put_on_bottom(to_bottom)

        assert deck.size() == 2

        # The cards should be at the end
        # (we can verify by drawing - should get them last)

    def test_load_real_deck_mono_u_terror(self) -> None:
        """Test loading real tournament deck."""
        fixture_path = Path("tests/fixtures/decks/mono_u_terror.txt")
        deck = Deck.from_file(str(fixture_path))

        assert deck.size() == 60

        # Check for specific cards
        island_count = sum(1 for card in deck._cards if card.name == "Island")
        assert island_count == 16

    def test_deck_name_from_filename(self) -> None:
        """Test extracting deck name from filename."""
        fixture_path = Path("tests/fixtures/decks/affinity_grixis.txt")
        deck = Deck.from_file(str(fixture_path))

        assert deck.deck_name == "affinity_grixis"


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
