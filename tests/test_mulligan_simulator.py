"""Tests for the MulliganSimulator class."""

from mtg_keep_or_mull.card import Card
from mtg_keep_or_mull.deck import Deck
from mtg_keep_or_mull.mulligan import MulliganSimulator


class TestMulliganSimulator:
    """Test cases for MulliganSimulator."""

    def test_start_game_draws_seven(self) -> None:
        """Test starting a game draws 7 cards."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        hand = sim.start_game()

        assert hand.size() == 7
        assert deck.size() == 53  # 60 - 7

    def test_mulligan_returns_and_redraws_seven(self) -> None:
        """Test mulligan returns hand and draws 7 again."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        sim.start_game()

        # Mulligan
        hand2 = sim.mulligan()

        # Should have 7 cards again
        assert hand2.size() == 7
        # Deck should be back to 53 (cards returned and reshuffled)
        assert deck.size() == 53
        # Mulligan count incremented
        assert sim.get_mulligan_count() == 1

    def test_keep_with_no_mulligans(self) -> None:
        """Test keeping opening hand with no mulligans."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        sim.start_game()

        # Keep without mulliganing
        final_hand = sim.keep()

        # No cards to bottom (0 mulligans)
        assert final_hand.size() == 7
        assert sim.get_mulligan_count() == 0

    def test_keep_after_one_mulligan(self) -> None:
        """Test keeping after 1 mulligan bottoms 1 card."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        sim.start_game()
        hand_after_mull = sim.mulligan()

        # User selects 1 card to bottom
        cards_to_bottom = [hand_after_mull.get_cards()[0]]

        # Keep (with 1 mulligan)
        final_hand = sim.keep(cards_to_bottom)

        # Final hand: 7 - 1 = 6 cards
        assert final_hand.size() == 6
        assert sim.get_mulligan_count() == 1

    def test_keep_after_two_mulligans(self) -> None:
        """Test keeping after 2 mulligans bottoms 2 cards."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        sim.start_game()
        sim.mulligan()
        hand_after_mull2 = sim.mulligan()

        # User selects 2 cards to bottom
        cards_to_bottom = hand_after_mull2.get_cards()[:2]

        final_hand = sim.keep(cards_to_bottom)

        # Final hand: 7 - 2 = 5 cards
        assert final_hand.size() == 5
        assert sim.get_mulligan_count() == 2

    def test_on_play_vs_on_draw(self) -> None:
        """Test on play vs on draw flag."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])

        sim_play = MulliganSimulator(deck, on_play=True)
        assert sim_play.on_play is True

        sim_draw = MulliganSimulator(deck, on_play=False)
        assert sim_draw.on_play is False

    def test_get_current_hand(self) -> None:
        """Test getting the current hand."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        hand = sim.start_game()

        current = sim.get_current_hand()
        assert current.size() == hand.size()

    def test_mulligan_to_zero_theoretical(self) -> None:
        """Test theoretical mulligan to 0 cards (Paris Mulligan style)."""
        deck = Deck([Card(f"Card{i}") for i in range(60)])
        deck.shuffle()

        sim = MulliganSimulator(deck, on_play=True)
        sim.start_game()

        # Mulligan 7 times
        for _ in range(7):
            sim.mulligan()

        assert sim.get_mulligan_count() == 7

        # If we keep, we'd bottom all 7 cards
        hand = sim.get_current_hand()
        all_cards = hand.get_cards()

        final_hand = sim.keep(all_cards)
        assert final_hand.size() == 0


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
