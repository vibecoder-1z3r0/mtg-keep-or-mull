"""DataStore interface and implementations for MTG Keep or Mull."""

from typing import List, Optional, Protocol

from mtg_keep_or_mull.models import DeckData, HandDecisionData, HandStats


class DataStore(Protocol):
    """Protocol defining the interface for data storage.

    This interface allows business logic to remain independent of the
    storage implementation (in-memory, JSON files, database, etc.).
    """

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a mulligan decision.

        Args:
            decision: The hand decision data to save
        """
        ...

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition.

        Args:
            hand_signature: Normalized hand signature (sorted card names)

        Returns:
            HandStats if decisions exist for this hand, None otherwise
        """
        ...

    def get_all_hand_statistics(self) -> List[HandStats]:
        """Get statistics for all recorded hand compositions.

        Returns:
            List of HandStats for all unique hand signatures
        """
        ...

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck.

        Args:
            deck: The deck data to save

        Returns:
            The deck_id of the saved deck
        """
        ...

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck by ID.

        Args:
            deck_id: The unique identifier for the deck

        Returns:
            DeckData if found, None otherwise
        """
        ...

    def list_decks(self) -> List[str]:
        """List all available deck IDs.

        Returns:
            List of deck_id strings
        """
        ...

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck.

        Args:
            deck_id: The deck identifier

        Returns:
            List of all hand decisions made with this deck
        """
        ...


class MockDataStore:
    """In-memory implementation of DataStore for testing and MVP.

    This implementation stores all data in memory using Python data structures.
    Data is lost when the process ends.
    """

    def __init__(self) -> None:
        """Initialize the mock data store."""
        self._decks: dict[str, DeckData] = {}
        self._decisions: list[HandDecisionData] = []

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a mulligan decision."""
        self._decisions.append(decision)

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition."""
        # Filter decisions for this hand signature
        matching_decisions = [d for d in self._decisions if d.hand_signature == hand_signature]

        if not matching_decisions:
            return None

        # Count keep vs mull
        times_kept = sum(1 for d in matching_decisions if d.decision == "keep")
        times_mulled = sum(1 for d in matching_decisions if d.decision == "mull")

        # Create stats object
        stats = HandStats(
            hand_signature=hand_signature, times_kept=times_kept, times_mulled=times_mulled
        )
        stats.calculate_keep_percentage()
        return stats

    def get_all_hand_statistics(self) -> List[HandStats]:
        """Get statistics for all recorded hand compositions."""
        # Get unique hand signatures
        signatures = set(d.hand_signature for d in self._decisions)

        # Generate stats for each
        all_stats = []
        for signature in signatures:
            stats = self.get_hand_statistics(signature)
            if stats:
                all_stats.append(stats)

        return all_stats

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck."""
        self._decks[deck.deck_id] = deck
        return deck.deck_id

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck by ID."""
        return self._decks.get(deck_id)

    def list_decks(self) -> List[str]:
        """List all available deck IDs."""
        return list(self._decks.keys())

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck."""
        return [d for d in self._decisions if d.deck_id == deck_id]


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
