"""Hand representation for MTG Keep or Mull."""

from typing import List

from mtg_keep_or_mull.card import Card


class Hand:
    """Represents a player's hand of cards.

    Stores cards in the order they were drawn/added (display order),
    but can generate a normalized signature for statistics.
    """

    def __init__(self, cards: List[Card] | None = None) -> None:
        """Initialize a hand with optional cards.

        Args:
            cards: Optional list of cards to start with
        """
        self._cards: List[Card] = cards if cards is not None else []

    def add_card(self, card: Card) -> None:
        """Add a card to the hand.

        Args:
            card: Card to add
        """
        self._cards.append(card)

    def remove_card(self, card: Card) -> None:
        """Remove a card from the hand.

        Args:
            card: Card to remove

        Raises:
            ValueError: If card is not in hand
        """
        self._cards.remove(card)

    def get_cards(self) -> List[Card]:
        """Get all cards in display order (as drawn/added).

        Returns:
            List of cards in their current order
        """
        return self._cards.copy()

    def size(self) -> int:
        """Get the number of cards in hand.

        Returns:
            Number of cards
        """
        return len(self._cards)

    def get_signature(self) -> str:
        """Get normalized hand signature for statistics.

        The signature is created by sorting card names alphabetically,
        ensuring identical hand compositions produce identical signatures
        regardless of card order.

        Returns:
            Comma-separated sorted card names (e.g., "Brainstorm,Island,Island")
        """
        if not self._cards:
            return ""

        sorted_names = sorted(card.name for card in self._cards)
        return ",".join(sorted_names)

    def count_lands(self) -> int:
        """Count the number of land cards in hand.

        Note: In MVP, this requires card type information which we don't have yet.
        This is a placeholder for future implementation when we add card metadata.

        Returns:
            Number of lands (currently always 0 - to be implemented)
        """
        # Placeholder: Will be implemented when card type metadata is added
        return 0


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
