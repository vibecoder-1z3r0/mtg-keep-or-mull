"""Tests for the Hand class."""

from mtg_keep_or_mull.card import Card
from mtg_keep_or_mull.hand import Hand


class TestHand:
    """Test cases for Hand class."""

    def test_create_empty_hand(self) -> None:
        """Test creating an empty hand."""
        hand = Hand()
        assert hand.size() == 0

    def test_create_hand_with_cards(self) -> None:
        """Test creating a hand with initial cards."""
        cards = [Card("Island"), Card("Brainstorm"), Card("Counterspell")]
        hand = Hand(cards)
        assert hand.size() == 3

    def test_add_card_to_hand(self) -> None:
        """Test adding a card to a hand."""
        hand = Hand()
        hand.add_card(Card("Mountain"))
        assert hand.size() == 1

    def test_remove_card_from_hand(self) -> None:
        """Test removing a card from a hand."""
        cards = [Card("Forest"), Card("Llanowar Elves")]
        hand = Hand(cards)
        hand.remove_card(Card("Forest"))
        assert hand.size() == 1

    def test_get_cards(self) -> None:
        """Test getting all cards in display order."""
        cards = [Card("Island"), Card("Brainstorm"), Card("Island")]
        hand = Hand(cards)
        hand_cards = hand.get_cards()
        assert len(hand_cards) == 3
        assert hand_cards[0].name == "Island"
        assert hand_cards[1].name == "Brainstorm"
        assert hand_cards[2].name == "Island"

    def test_get_signature_normalized(self) -> None:
        """Test getting normalized hand signature (sorted)."""
        # Create hand in random order
        cards = [
            Card("Island"),
            Card("Brainstorm"),
            Card("Counterspell"),
            Card("Thought Scour"),
            Card("Mental Note"),
            Card("Island"),
            Card("Lórien Revealed"),
        ]
        hand = Hand(cards)

        # Signature should be alphabetically sorted
        signature = hand.get_signature()
        expected = "Brainstorm,Counterspell,Island,Island,Lórien Revealed,Mental Note,Thought Scour"
        assert signature == expected

    def test_get_signature_different_order_same_result(self) -> None:
        """Test that different orders produce the same signature."""
        # Two hands with same cards, different order
        hand1 = Hand(
            [
                Card("Counterspell"),
                Card("Island"),
                Card("Island"),
                Card("Lórien Revealed"),
                Card("Mental Note"),
                Card("Thought Scour"),
                Card("Brainstorm"),
            ]
        )

        hand2 = Hand(
            [
                Card("Island"),
                Card("Brainstorm"),
                Card("Counterspell"),
                Card("Thought Scour"),
                Card("Mental Note"),
                Card("Island"),
                Card("Lórien Revealed"),
            ]
        )

        # Both should have same signature
        assert hand1.get_signature() == hand2.get_signature()

    def test_count_lands_no_lands(self) -> None:
        """Test counting lands when there are none."""
        cards = [Card("Lightning Bolt"), Card("Monastery Swiftspear")]
        hand = Hand(cards)
        # Without card type info, can't determine lands yet
        # This will need card type metadata in future
        # For now, just test the method exists
        assert hasattr(hand, "count_lands")

    def test_empty_hand_signature(self) -> None:
        """Test signature of an empty hand."""
        hand = Hand()
        assert hand.get_signature() == ""


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
