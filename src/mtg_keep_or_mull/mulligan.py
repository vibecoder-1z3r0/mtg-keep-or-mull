"""Mulligan simulator for London Mulligan rules."""

from typing import List

from mtg_keep_or_mull.card import Card
from mtg_keep_or_mull.deck import Deck
from mtg_keep_or_mull.hand import Hand


class MulliganSimulator:
    """Simulates the London Mulligan process.

    London Mulligan Rules:
    1. Always draw 7 cards
    2. Decide to keep or mulligan
    3. If mulligan: shuffle hand back, draw 7 again, increment counter
    4. When keeping: bottom N cards (where N = mulligan count)
    5. Final hand size = 7 - N
    """

    def __init__(self, deck: Deck, on_play: bool) -> None:
        """Initialize the mulligan simulator.

        Args:
            deck: The deck to use
            on_play: True if on the play, False if on the draw
        """
        self._deck = deck
        self.on_play = on_play
        self._mulligan_count = 0
        self._current_hand: Hand | None = None

    def start_game(self) -> Hand:
        """Start a new game and draw opening hand of 7 cards.

        Returns:
            Hand with 7 cards
        """
        # Reset mulligan count
        self._mulligan_count = 0

        # Draw 7 cards
        cards = self._deck.draw(7)
        self._current_hand = Hand(cards)

        return self._current_hand

    def mulligan(self) -> Hand:
        """Mulligan: return current hand, shuffle, and draw 7 again.

        Returns:
            New hand with 7 cards
        """
        if self._current_hand is None:
            raise ValueError("No hand to mulligan - call start_game() first")

        # Return cards to deck
        cards_to_return = self._current_hand.get_cards()
        self._deck.return_cards(cards_to_return)

        # Shuffle
        self._deck.shuffle()

        # Increment mulligan count
        self._mulligan_count += 1

        # Draw 7 again
        cards = self._deck.draw(7)
        self._current_hand = Hand(cards)

        return self._current_hand

    def keep(self, cards_to_bottom: List[Card] | None = None) -> Hand:
        """Keep the current hand and bottom cards if needed.

        Args:
            cards_to_bottom: Cards to put on bottom (should equal mulligan count)

        Returns:
            Final hand after bottoming cards
        """
        if self._current_hand is None:
            raise ValueError("No hand to keep - call start_game() first")

        if cards_to_bottom is None:
            cards_to_bottom = []

        # Validate bottom count matches mulligan count
        if len(cards_to_bottom) != self._mulligan_count:
            raise ValueError(
                f"Must bottom {self._mulligan_count} cards, " f"but received {len(cards_to_bottom)}"
            )

        # Remove cards from hand and put on bottom of deck
        for card in cards_to_bottom:
            self._current_hand.remove_card(card)

        self._deck.put_on_bottom(cards_to_bottom)

        return self._current_hand

    def get_mulligan_count(self) -> int:
        """Get the current mulligan count.

        Returns:
            Number of times mulliganed
        """
        return self._mulligan_count

    def get_current_hand(self) -> Hand:
        """Get the current hand.

        Returns:
            Current hand

        Raises:
            ValueError: If no hand exists yet
        """
        if self._current_hand is None:
            raise ValueError("No current hand - call start_game() first")

        return self._current_hand


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
