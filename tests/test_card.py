"""Tests for the Card class."""

from mtg_keep_or_mull.card import Card


class TestCard:
    """Test cases for Card class."""

    def test_card_creation_with_name_only(self) -> None:
        """Test creating a card with just a name."""
        card = Card("Lightning Bolt")
        assert card.name == "Lightning Bolt"

    def test_card_equality(self) -> None:
        """Test that two cards with the same name are equal."""
        card1 = Card("Mountain")
        card2 = Card("Mountain")
        assert card1 == card2

    def test_card_inequality(self) -> None:
        """Test that cards with different names are not equal."""
        card1 = Card("Mountain")
        card2 = Card("Island")
        assert card1 != card2

    def test_card_string_representation(self) -> None:
        """Test card string representation."""
        card = Card("Forest")
        assert str(card) == "Forest"

    def test_card_repr(self) -> None:
        """Test card repr for debugging."""
        card = Card("Counterspell")
        assert repr(card) == "Card('Counterspell')"

    def test_card_equality_with_non_card(self) -> None:
        """Test that Card is not equal to non-Card objects."""
        card = Card("Mountain")
        assert card != "Mountain"
        assert card != 42
        assert card is not None

    def test_card_hashable(self) -> None:
        """Test that cards can be used in sets and as dict keys."""
        card1 = Card("Forest")
        card2 = Card("Forest")
        card3 = Card("Mountain")

        # Cards with same name should have same hash
        assert hash(card1) == hash(card2)

        # Cards can be added to sets
        card_set = {card1, card2, card3}
        assert len(card_set) == 2  # card1 and card2 are duplicates

        # Cards can be used as dict keys
        card_dict = {card1: 4, card3: 20}
        assert card_dict[card2] == 4  # card2 has same name as card1


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
