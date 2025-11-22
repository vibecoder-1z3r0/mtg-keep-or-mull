"""Deck representation and MTGO format parsing."""

import random
from pathlib import Path
from typing import List

from mtg_keep_or_mull.card import Card


class Deck:
    """Represents a Magic: The Gathering deck.

    Parses MTGO-format deck lists, expands quantities into individual cards,
    and provides deck manipulation operations (shuffle, draw, etc.).
    """

    def __init__(self, cards: List[Card] | None = None) -> None:
        """Initialize a deck with optional cards.

        Args:
            cards: Optional list of cards to start with
        """
        self._cards: List[Card] = cards if cards is not None else []
        self.sideboard: List[Card] = []
        self.deck_name: str = ""

    @classmethod
    def from_file(cls, filepath: str) -> "Deck":
        """Load a deck from an MTGO-format text file.

        Args:
            filepath: Path to the deck file

        Returns:
            Loaded Deck instance
        """
        with open(filepath, "r", encoding="utf-8") as f:
            deck_text = f.read()

        deck = cls.from_text(deck_text)

        # Extract deck name from filename
        deck.deck_name = Path(filepath).stem

        return deck

    @classmethod
    def from_text(cls, deck_text: str) -> "Deck":
        """Parse a deck from MTGO-format text.

        Format:
            <quantity> <card name>
            ...
            SIDEBOARD:
            <quantity> <card name>

        Args:
            deck_text: MTGO-format deck list text

        Returns:
            Parsed Deck instance
        """
        deck = cls()
        lines = deck_text.strip().split("\n")
        parsing_sideboard = False

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for sideboard marker
            if line.upper() == "SIDEBOARD:":
                parsing_sideboard = True
                continue

            # Parse quantity and card name
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue

            try:
                quantity = int(parts[0])
                card_name = parts[1]
            except ValueError:
                # Skip lines that don't match format
                continue

            # Create cards
            cards_to_add = [Card(card_name) for _ in range(quantity)]

            if parsing_sideboard:
                deck.sideboard.extend(cards_to_add)
            else:
                deck._cards.extend(cards_to_add)

        return deck

    def shuffle(self) -> None:
        """Randomize the order of cards in the deck."""
        random.shuffle(self._cards)

    def draw(self, count: int) -> List[Card]:
        """Draw cards from the top of the deck.

        Args:
            count: Number of cards to draw

        Returns:
            List of drawn cards (may be fewer than requested if deck is too small)
        """
        actual_count = min(count, len(self._cards))
        drawn = self._cards[:actual_count]
        self._cards = self._cards[actual_count:]
        return drawn

    def return_cards(self, cards: List[Card]) -> None:
        """Return cards to the deck (for mulligan).

        Cards are added to the deck and should be shuffled afterward.

        Args:
            cards: Cards to return to deck
        """
        self._cards.extend(cards)

    def put_on_bottom(self, cards: List[Card]) -> None:
        """Put cards on the bottom of the deck (London Mulligan).

        Args:
            cards: Cards to put on bottom
        """
        self._cards.extend(cards)

    def size(self) -> int:
        """Get the current number of cards in the deck.

        Returns:
            Number of cards
        """
        return len(self._cards)


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
