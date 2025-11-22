"""Card representation for MTG Keep or Mull."""


class Card:
    """Represents a single Magic: The Gathering card.

    In MVP, this is a simple data container storing only the card name.
    Future enhancements will add card_type, mana_cost, cmc, colors, etc.
    """

    def __init__(self, name: str) -> None:
        """Initialize a Card with a name.

        Args:
            name: The card name (e.g., "Lightning Bolt", "Mountain")
        """
        self.name = name

    def __eq__(self, other: object) -> bool:
        """Check equality based on card name.

        Args:
            other: Another object to compare with

        Returns:
            True if both are Cards with the same name, False otherwise
        """
        if not isinstance(other, Card):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Make Card hashable based on name.

        Returns:
            Hash of the card name
        """
        return hash(self.name)

    def __str__(self) -> str:
        """String representation showing card name.

        Returns:
            The card name
        """
        return self.name

    def __repr__(self) -> str:
        """Detailed representation for debugging.

        Returns:
            Card constructor representation
        """
        return f"Card('{self.name}')"


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
