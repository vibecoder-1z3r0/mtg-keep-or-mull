"""DataStore interface and implementations for MTG Keep or Mull."""

# pylint: disable=too-many-lines  # Multiple storage implementations in one module

import json
import sqlite3
from datetime import datetime
from pathlib import Path
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

    def update_deck(self, deck: DeckData) -> None:
        """Update an existing deck's metadata.

        Args:
            deck: The deck data with updated metadata

        Raises:
            ValueError: If the deck doesn't exist
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

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks.

        Returns:
            List of all hand decisions
        """
        ...

    def list_decks_filtered(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> List[str]:
        """List deck IDs filtered by format, archetype, colors, and/or tags.

        Filters use "contains" logic - a deck matches if the filter value is IN the deck's list.
        Multiple filters use AND logic.

        Args:
            mtg_format: Optional format filter (e.g., "Pauper")
                - matches if value in deck.format list
            archetype: Optional archetype filter (e.g., "Aggro")
                - matches if value in deck.archetype list
            colors: Optional color filter (e.g., "U", "Grixis")
                - matches if value in deck.colors list
            tags: Optional tag filter (e.g., "burn")
                - matches if value in deck.tags list

        Returns:
            List of deck_id strings matching all provided filters
        """
        ...

    def get_random_deck(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Optional[DeckData]:
        """Get a random deck, optionally filtered by format, archetype, colors, and/or tags.

        Args:
            mtg_format: Optional format filter - matches if value in deck.format list
            archetype: Optional archetype filter - matches if value in deck.archetype list
            colors: Optional color filter - matches if value in deck.colors list
            tags: Optional tag filter - matches if value in deck.tags list

        Returns:
            Random DeckData matching the filters, or None if no decks match
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

    def update_deck(self, deck: DeckData) -> None:
        """Update an existing deck's metadata.

        Args:
            deck: The deck data with updated metadata

        Raises:
            ValueError: If the deck doesn't exist
        """
        if deck.deck_id not in self._decks:
            raise ValueError(f"Deck not found: {deck.deck_id}")
        self._decks[deck.deck_id] = deck

    def list_decks(self) -> List[str]:
        """List all available deck IDs."""
        return list(self._decks.keys())

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck."""
        return [d for d in self._decisions if d.deck_id == deck_id]

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks."""
        return list(self._decisions)

    def list_decks_filtered(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> List[str]:
        """List deck IDs filtered by format, archetype, colors, and/or tags.

        Uses "contains" logic - filters match if value is IN the deck's list.
        """
        deck_ids = []
        for deck_id, deck in self._decks.items():
            # If no filters provided, include all decks
            if mtg_format is None and archetype is None and colors is None and tags is None:
                deck_ids.append(deck_id)
                continue

            # Check format filter (value must be IN deck.format list)
            if mtg_format is not None and mtg_format not in deck.format:
                continue

            # Check archetype filter (value must be IN deck.archetype list)
            if archetype is not None and archetype not in deck.archetype:
                continue

            # Check colors filter (value must be IN deck.colors list)
            if colors is not None and colors not in deck.colors:
                continue

            # Check tags filter (value must be IN deck.tags list)
            if tags is not None and tags not in deck.tags:
                continue

            # Deck passed all filters
            deck_ids.append(deck_id)

        return deck_ids

    def get_random_deck(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Optional[DeckData]:
        """Get a random deck, optionally filtered by format, archetype, colors, and/or tags."""
        import random

        matching_deck_ids = self.list_decks_filtered(
            mtg_format=mtg_format, archetype=archetype, colors=colors, tags=tags
        )

        if not matching_deck_ids:
            return None

        random_deck_id = random.choice(matching_deck_ids)
        return self._decks.get(random_deck_id)


class JSONDataStore:
    """File-based implementation of DataStore using JSON files.

    This implementation stores data in JSON files organized by type:
    - Decks: data/decks/<deck_id>.json
    - Decisions: data/decisions/<deck_id>.json

    Data persists across sessions but is stored as human-readable JSON.
    """

    def __init__(self, base_path: Path | str | None = None) -> None:
        """Initialize the JSON data store.

        Args:
            base_path: Base directory for data storage. Defaults to ./data
        """
        if base_path is None:
            base_path = Path("data")
        elif isinstance(base_path, str):
            base_path = Path(base_path)

        self.base_path = base_path
        self.decks_dir = base_path / "decks"
        self.decisions_dir = base_path / "decisions"

        # Create directories if they don't exist
        self.decks_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck to a JSON file.

        Args:
            deck: The deck data to save

        Returns:
            The deck_id of the saved deck
        """
        deck_file = self.decks_dir / f"{deck.deck_id}.json"

        # Serialize to JSON with pretty printing
        with open(deck_file, "w", encoding="utf-8") as f:
            json.dump(deck.model_dump(), f, indent=2, ensure_ascii=False)

        return deck.deck_id

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck from a JSON file.

        Args:
            deck_id: The unique identifier for the deck

        Returns:
            DeckData if found, None otherwise
        """
        deck_file = self.decks_dir / f"{deck_id}.json"

        if not deck_file.exists():
            return None

        with open(deck_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return DeckData(**data)

    def update_deck(self, deck: DeckData) -> None:
        """Update an existing deck's metadata.

        Args:
            deck: The deck data with updated metadata

        Raises:
            ValueError: If the deck doesn't exist
        """
        deck_file = self.decks_dir / f"{deck.deck_id}.json"

        if not deck_file.exists():
            raise ValueError(f"Deck not found: {deck.deck_id}")

        # Save the updated deck
        with open(deck_file, "w", encoding="utf-8") as f:
            json.dump(deck.model_dump(), f, indent=2, ensure_ascii=False)

    def list_decks(self) -> List[str]:
        """List all available deck IDs.

        Returns:
            List of deck_id strings
        """
        # Get all .json files in decks directory
        deck_files = self.decks_dir.glob("*.json")
        # Extract deck IDs (filename without .json extension)
        return [f.stem for f in deck_files]

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a hand decision to a JSON file.

        Appends the decision to the list of decisions for this deck.

        Args:
            decision: The hand decision data to save
        """
        decisions_file = self.decisions_dir / f"{decision.deck_id}.json"

        # Load existing decisions if file exists
        if decisions_file.exists():
            with open(decisions_file, "r", encoding="utf-8") as f:
                decisions_data = json.load(f)
        else:
            decisions_data = []

        # Append new decision
        decisions_data.append(decision.model_dump(mode="json"))

        # Save back to file
        with open(decisions_file, "w", encoding="utf-8") as f:
            json.dump(decisions_data, f, indent=2, ensure_ascii=False)

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck.

        Args:
            deck_id: The deck identifier

        Returns:
            List of all hand decisions made with this deck
        """
        decisions_file = self.decisions_dir / f"{deck_id}.json"

        if not decisions_file.exists():
            return []

        with open(decisions_file, "r", encoding="utf-8") as f:
            decisions_data = json.load(f)

        # Convert JSON data to HandDecisionData objects
        return [HandDecisionData(**d) for d in decisions_data]

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks.

        Returns:
            List of all hand decisions
        """
        all_decisions = []
        for decisions_file in self.decisions_dir.glob("*.json"):
            with open(decisions_file, "r", encoding="utf-8") as f:
                decisions_data = json.load(f)
                all_decisions.extend([HandDecisionData(**d) for d in decisions_data])
        return all_decisions

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition.

        Args:
            hand_signature: Normalized hand signature (sorted card names)

        Returns:
            HandStats if decisions exist for this hand, None otherwise
        """
        # Get all decisions across all decks
        all_decisions = []
        for decisions_file in self.decisions_dir.glob("*.json"):
            with open(decisions_file, "r", encoding="utf-8") as f:
                decisions_data = json.load(f)
                all_decisions.extend([HandDecisionData(**d) for d in decisions_data])

        # Filter decisions for this hand signature
        matching_decisions = [d for d in all_decisions if d.hand_signature == hand_signature]

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
        """Get statistics for all recorded hand compositions.

        Returns:
            List of HandStats for all unique hand signatures
        """
        # Get all decisions across all decks
        all_decisions = []
        for decisions_file in self.decisions_dir.glob("*.json"):
            with open(decisions_file, "r", encoding="utf-8") as f:
                decisions_data = json.load(f)
                all_decisions.extend([HandDecisionData(**d) for d in decisions_data])

        # Get unique hand signatures
        signatures = set(d.hand_signature for d in all_decisions)

        # Generate stats for each
        all_stats = []
        for signature in signatures:
            stats = self.get_hand_statistics(signature)
            if stats:
                all_stats.append(stats)

        return all_stats

    def list_decks_filtered(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> List[str]:
        """List deck IDs filtered by format, archetype, colors, and/or tags.

        Uses "contains" logic - filters match if value is IN the deck's list.
        """
        all_deck_ids = self.list_decks()
        filtered_ids = []

        for deck_id in all_deck_ids:
            deck = self.load_deck(deck_id)
            if not deck:
                continue

            # If no filters provided, include all decks
            if mtg_format is None and archetype is None and colors is None and tags is None:
                filtered_ids.append(deck_id)
                continue

            # Check format filter (value must be IN deck.format list)
            if mtg_format is not None and mtg_format not in deck.format:
                continue

            # Check archetype filter (value must be IN deck.archetype list)
            if archetype is not None and archetype not in deck.archetype:
                continue

            # Check colors filter (value must be IN deck.colors list)
            if colors is not None and colors not in deck.colors:
                continue

            # Check tags filter (value must be IN deck.tags list)
            if tags is not None and tags not in deck.tags:
                continue

            # Deck passed all filters
            filtered_ids.append(deck_id)

        return filtered_ids

    def get_random_deck(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Optional[DeckData]:
        """Get a random deck, optionally filtered by format, archetype, colors, and/or tags."""
        import random

        matching_deck_ids = self.list_decks_filtered(
            mtg_format=mtg_format, archetype=archetype, colors=colors, tags=tags
        )

        if not matching_deck_ids:
            return None

        random_deck_id = random.choice(matching_deck_ids)
        return self.load_deck(random_deck_id)


class SQLiteDataStore:
    """SQLite database implementation of DataStore.

    This implementation stores data in a SQLite database file,
    providing efficient querying and persistence.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialize the SQLite data store.

        Args:
            db_path: Path to SQLite database file. Defaults to ./data/mtg_keep_or_mull.db
        """
        if db_path is None:
            db_path = Path("data/mtg_keep_or_mull.db")
        elif isinstance(db_path, str):
            db_path = Path(db_path)

        self.db_path = db_path

        # Create parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection to the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def _init_schema(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create decks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decks (
                deck_id TEXT PRIMARY KEY,
                deck_name TEXT NOT NULL DEFAULT '',
                main_deck TEXT NOT NULL,
                sideboard TEXT NOT NULL,
                total_games INTEGER NOT NULL DEFAULT 0,
                format TEXT NOT NULL DEFAULT '[]',
                archetype TEXT NOT NULL DEFAULT '[]',
                colors TEXT NOT NULL DEFAULT '[]',
                tags TEXT NOT NULL DEFAULT '[]'
            )
        """
        )

        # Create hand_decisions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hand_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id TEXT NOT NULL,
                hand_signature TEXT NOT NULL,
                hand_display TEXT NOT NULL,
                mulligan_count INTEGER NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN ('keep', 'mull')),
                lands_in_hand INTEGER NOT NULL,
                on_play INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_deck_id
            ON hand_decisions(deck_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_signature
            ON hand_decisions(hand_signature)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_timestamp
            ON hand_decisions(timestamp)
        """
        )

        conn.commit()
        conn.close()

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck to the database.

        Args:
            deck: The deck data to save

        Returns:
            The deck_id of the saved deck
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Serialize lists to JSON
        main_deck_json = json.dumps(deck.main_deck)
        sideboard_json = json.dumps(deck.sideboard)
        format_json = json.dumps(deck.format)
        archetype_json = json.dumps(deck.archetype)
        colors_json = json.dumps(deck.colors)
        tags_json = json.dumps(deck.tags)

        # Insert or replace deck
        cursor.execute(
            """
            INSERT OR REPLACE INTO decks (
                deck_id, deck_name, main_deck, sideboard, total_games,
                format, archetype, colors, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                deck.deck_id,
                deck.deck_name,
                main_deck_json,
                sideboard_json,
                deck.total_games,
                format_json,
                archetype_json,
                colors_json,
                tags_json,
            ),
        )

        conn.commit()
        conn.close()

        return deck.deck_id

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck from the database.

        Args:
            deck_id: The unique identifier for the deck

        Returns:
            DeckData if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, deck_name, main_deck, sideboard, total_games,
                   format, archetype, colors, tags
            FROM decks
            WHERE deck_id = ?
        """,
            (deck_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return DeckData(
            deck_id=row["deck_id"],
            deck_name=row["deck_name"],
            main_deck=json.loads(row["main_deck"]),
            sideboard=json.loads(row["sideboard"]),
            total_games=row["total_games"],
            format=json.loads(row["format"]),
            archetype=json.loads(row["archetype"]),
            colors=json.loads(row["colors"]),
            tags=json.loads(row["tags"]),
        )

    def update_deck(self, deck: DeckData) -> None:
        """Update an existing deck's metadata.

        Args:
            deck: The deck data with updated metadata

        Raises:
            ValueError: If the deck doesn't exist
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Serialize lists to JSON
        main_deck_json = json.dumps(deck.main_deck)
        sideboard_json = json.dumps(deck.sideboard)
        format_json = json.dumps(deck.format)
        archetype_json = json.dumps(deck.archetype)
        colors_json = json.dumps(deck.colors)
        tags_json = json.dumps(deck.tags)

        # Update deck
        cursor.execute(
            """
            UPDATE decks
            SET deck_name = ?, main_deck = ?, sideboard = ?, total_games = ?,
                format = ?, archetype = ?, colors = ?, tags = ?
            WHERE deck_id = ?
        """,
            (
                deck.deck_name,
                main_deck_json,
                sideboard_json,
                deck.total_games,
                format_json,
                archetype_json,
                colors_json,
                tags_json,
                deck.deck_id,
            ),
        )

        # Check if deck was found
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError(f"Deck not found: {deck.deck_id}")

        conn.commit()
        conn.close()

    def list_decks(self) -> List[str]:
        """List all available deck IDs.

        Returns:
            List of deck_id strings
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT deck_id FROM decks")
        rows = cursor.fetchall()
        conn.close()

        return [row["deck_id"] for row in rows]

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a hand decision to the database.

        Args:
            decision: The hand decision data to save
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Serialize hand_display to JSON
        hand_display_json = json.dumps(decision.hand_display)

        # Convert boolean to integer (SQLite doesn't have boolean type)
        on_play_int = 1 if decision.on_play else 0

        # Format timestamp as ISO format string
        timestamp_str = decision.timestamp.isoformat()

        cursor.execute(
            """
            INSERT INTO hand_decisions (
                deck_id, hand_signature, hand_display, mulligan_count,
                decision, lands_in_hand, on_play, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                decision.deck_id,
                decision.hand_signature,
                hand_display_json,
                decision.mulligan_count,
                decision.decision,
                decision.lands_in_hand,
                on_play_int,
                timestamp_str,
            ),
        )

        conn.commit()
        conn.close()

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck.

        Args:
            deck_id: The deck identifier

        Returns:
            List of all hand decisions made with this deck
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            WHERE deck_id = ?
            ORDER BY timestamp
        """,
            (deck_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row["deck_id"],
                    hand_signature=row["hand_signature"],
                    hand_display=json.loads(row["hand_display"]),
                    mulligan_count=row["mulligan_count"],
                    decision=row["decision"],
                    lands_in_hand=row["lands_in_hand"],
                    on_play=bool(row["on_play"]),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                )
            )

        return decisions

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks.

        Returns:
            List of all hand decisions
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            ORDER BY timestamp
        """
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row["deck_id"],
                    hand_signature=row["hand_signature"],
                    hand_display=json.loads(row["hand_display"]),
                    mulligan_count=row["mulligan_count"],
                    decision=row["decision"],
                    lands_in_hand=row["lands_in_hand"],
                    on_play=bool(row["on_play"]),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                )
            )

        return decisions

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition.

        Args:
            hand_signature: Normalized hand signature (sorted card names)

        Returns:
            HandStats if decisions exist for this hand, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            WHERE hand_signature = ?
        """,
            (hand_signature,),
        )

        row = cursor.fetchone()
        conn.close()

        # If no decisions found, return None
        if row is None or row["total_count"] == 0:
            return None

        stats = HandStats(
            hand_signature=hand_signature,
            times_kept=row["times_kept"] or 0,
            times_mulled=row["times_mulled"] or 0,
        )
        stats.calculate_keep_percentage()
        return stats

    def get_all_hand_statistics(self) -> List[HandStats]:
        """Get statistics for all recorded hand compositions.

        Returns:
            List of HandStats for all unique hand signatures
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                hand_signature,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            GROUP BY hand_signature
        """
        )

        rows = cursor.fetchall()
        conn.close()

        all_stats = []
        for row in rows:
            stats = HandStats(
                hand_signature=row["hand_signature"],
                times_kept=row["times_kept"] or 0,
                times_mulled=row["times_mulled"] or 0,
            )
            stats.calculate_keep_percentage()
            all_stats.append(stats)

        return all_stats


class PostgreSQLDataStore:  # pylint: disable=too-many-instance-attributes
    """PostgreSQL database implementation of DataStore.

    This implementation stores data in a PostgreSQL database,
    providing enterprise-grade reliability and scalability.

    Requires: psycopg2-binary
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "mtg_keep_or_mull",
        user: str = "postgres",
        password: str = "",
    ) -> None:
        """Initialize the PostgreSQL data store.

        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Database user
            password: Database password
        """
        try:
            import psycopg2  # type: ignore[import-untyped]
            import psycopg2.extras  # type: ignore[import-untyped] # noqa: F401
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires psycopg2. "
                "Install with: pip install mtg-keep-or-mull[postgres]"
            ) from e

        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self._psycopg2 = psycopg2

        # Initialize schema
        self._init_schema()

    def _get_connection(self):  # type: ignore
        """Get a connection to the database."""
        return self._psycopg2.connect(**self.conn_params)

    def _init_schema(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create decks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decks (
                deck_id VARCHAR(255) PRIMARY KEY,
                deck_name VARCHAR(255) NOT NULL DEFAULT '',
                main_deck TEXT NOT NULL,
                sideboard TEXT NOT NULL,
                total_games INTEGER NOT NULL DEFAULT 0
            )
        """
        )

        # Create hand_decisions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hand_decisions (
                id SERIAL PRIMARY KEY,
                deck_id VARCHAR(255) NOT NULL,
                hand_signature TEXT NOT NULL,
                hand_display TEXT NOT NULL,
                mulligan_count INTEGER NOT NULL,
                decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'mull')),
                lands_in_hand INTEGER NOT NULL,
                on_play BOOLEAN NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_deck_id
            ON hand_decisions(deck_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_signature
            ON hand_decisions(hand_signature)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_timestamp
            ON hand_decisions(timestamp)
        """
        )

        conn.commit()
        conn.close()

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        main_deck_json = json.dumps(deck.main_deck)
        sideboard_json = json.dumps(deck.sideboard)

        cursor.execute(
            """
            INSERT INTO decks (deck_id, deck_name, main_deck, sideboard, total_games)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (deck_id) DO UPDATE SET
                deck_name = EXCLUDED.deck_name,
                main_deck = EXCLUDED.main_deck,
                sideboard = EXCLUDED.sideboard,
                total_games = EXCLUDED.total_games
        """,
            (deck.deck_id, deck.deck_name, main_deck_json, sideboard_json, deck.total_games),
        )

        conn.commit()
        conn.close()
        return deck.deck_id

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, deck_name, main_deck, sideboard, total_games
            FROM decks WHERE deck_id = %s
        """,
            (deck_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return DeckData(
            deck_id=row[0],
            deck_name=row[1],
            main_deck=json.loads(row[2]),
            sideboard=json.loads(row[3]),
            total_games=row[4],
        )

    def list_decks(self) -> List[str]:
        """List all available deck IDs."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT deck_id FROM decks")
        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a hand decision to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        hand_display_json = json.dumps(decision.hand_display)

        cursor.execute(
            """
            INSERT INTO hand_decisions (
                deck_id, hand_signature, hand_display, mulligan_count,
                decision, lands_in_hand, on_play, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                decision.deck_id,
                decision.hand_signature,
                hand_display_json,
                decision.mulligan_count,
                decision.decision,
                decision.lands_in_hand,
                decision.on_play,
                decision.timestamp,
            ),
        )

        conn.commit()
        conn.close()

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            WHERE deck_id = %s
            ORDER BY timestamp
        """,
            (deck_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row[0],
                    hand_signature=row[1],
                    hand_display=json.loads(row[2]),
                    mulligan_count=row[3],
                    decision=row[4],
                    lands_in_hand=row[5],
                    on_play=row[6],
                    timestamp=row[7],
                )
            )

        return decisions

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            ORDER BY timestamp
        """
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row[0],
                    hand_signature=row[1],
                    hand_display=json.loads(row[2]),
                    mulligan_count=row[3],
                    decision=row[4],
                    lands_in_hand=row[5],
                    on_play=row[6],
                    timestamp=row[7],
                )
            )

        return decisions

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            WHERE hand_signature = %s
        """,
            (hand_signature,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None or row[0] == 0:
            return None

        stats = HandStats(
            hand_signature=hand_signature, times_kept=row[1] or 0, times_mulled=row[2] or 0
        )
        stats.calculate_keep_percentage()
        return stats

    def get_all_hand_statistics(self) -> List[HandStats]:
        """Get statistics for all recorded hand compositions."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                hand_signature,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            GROUP BY hand_signature
        """
        )

        rows = cursor.fetchall()
        conn.close()

        all_stats = []
        for row in rows:
            stats = HandStats(
                hand_signature=row[0], times_kept=row[1] or 0, times_mulled=row[2] or 0
            )
            stats.calculate_keep_percentage()
            all_stats.append(stats)

        return all_stats


class MariaDBDataStore:  # pylint: disable=too-many-instance-attributes
    """MariaDB/MySQL database implementation of DataStore.

    This implementation stores data in a MariaDB or MySQL database,
    providing compatibility with MySQL ecosystem.

    Requires: mysql-connector-python
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "mtg_keep_or_mull",
        user: str = "root",
        password: str = "",
    ) -> None:
        """Initialize the MariaDB data store.

        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Database user
            password: Database password
        """
        try:
            import mysql.connector  # type: ignore[import-not-found]
        except ImportError as e:
            raise ImportError(
                "MariaDB/MySQL support requires mysql-connector-python. "
                "Install with: pip install mtg-keep-or-mull[mysql]"
            ) from e

        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self._mysql = mysql.connector

        # Initialize schema
        self._init_schema()

    def _get_connection(self):  # type: ignore
        """Get a connection to the database."""
        return self._mysql.connect(**self.conn_params)

    def _init_schema(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create decks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decks (
                deck_id VARCHAR(255) PRIMARY KEY,
                deck_name VARCHAR(255) NOT NULL DEFAULT '',
                main_deck TEXT NOT NULL,
                sideboard TEXT NOT NULL,
                total_games INT NOT NULL DEFAULT 0
            )
        """
        )

        # Create hand_decisions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hand_decisions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                deck_id VARCHAR(255) NOT NULL,
                hand_signature TEXT NOT NULL,
                hand_display TEXT NOT NULL,
                mulligan_count INT NOT NULL,
                decision VARCHAR(10) NOT NULL,
                lands_in_hand INT NOT NULL,
                on_play BOOLEAN NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE,
                CONSTRAINT chk_decision CHECK (decision IN ('keep', 'mull'))
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_deck_id
            ON hand_decisions(deck_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_signature
            ON hand_decisions(hand_signature(255))
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_hand_decisions_timestamp
            ON hand_decisions(timestamp)
        """
        )

        conn.commit()
        conn.close()

    def save_deck(self, deck: DeckData) -> str:
        """Save a deck to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        main_deck_json = json.dumps(deck.main_deck)
        sideboard_json = json.dumps(deck.sideboard)

        cursor.execute(
            """
            INSERT INTO decks (deck_id, deck_name, main_deck, sideboard, total_games)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                deck_name = VALUES(deck_name),
                main_deck = VALUES(main_deck),
                sideboard = VALUES(sideboard),
                total_games = VALUES(total_games)
        """,
            (deck.deck_id, deck.deck_name, main_deck_json, sideboard_json, deck.total_games),
        )

        conn.commit()
        conn.close()
        return deck.deck_id

    def load_deck(self, deck_id: str) -> Optional[DeckData]:
        """Load a deck from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, deck_name, main_deck, sideboard, total_games
            FROM decks WHERE deck_id = %s
        """,
            (deck_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return DeckData(
            deck_id=row[0],
            deck_name=row[1],
            main_deck=json.loads(row[2]),
            sideboard=json.loads(row[3]),
            total_games=row[4],
        )

    def list_decks(self) -> List[str]:
        """List all available deck IDs."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT deck_id FROM decks")
        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def save_hand_decision(self, decision: HandDecisionData) -> None:
        """Save a hand decision to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        hand_display_json = json.dumps(decision.hand_display)

        cursor.execute(
            """
            INSERT INTO hand_decisions (
                deck_id, hand_signature, hand_display, mulligan_count,
                decision, lands_in_hand, on_play, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                decision.deck_id,
                decision.hand_signature,
                hand_display_json,
                decision.mulligan_count,
                decision.decision,
                decision.lands_in_hand,
                decision.on_play,
                decision.timestamp,
            ),
        )

        conn.commit()
        conn.close()

    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]:
        """Get all hand decisions for a specific deck."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            WHERE deck_id = %s
            ORDER BY timestamp
        """,
            (deck_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row[0],
                    hand_signature=row[1],
                    hand_display=json.loads(row[2]),
                    mulligan_count=row[3],
                    decision=row[4],
                    lands_in_hand=row[5],
                    on_play=row[6],
                    timestamp=row[7],
                )
            )

        return decisions

    def get_all_decisions(self) -> List[HandDecisionData]:
        """Get all hand decisions across all decks."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deck_id, hand_signature, hand_display, mulligan_count,
                   decision, lands_in_hand, on_play, timestamp
            FROM hand_decisions
            ORDER BY timestamp
        """
        )

        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            decisions.append(
                HandDecisionData(
                    deck_id=row[0],
                    hand_signature=row[1],
                    hand_display=json.loads(row[2]),
                    mulligan_count=row[3],
                    decision=row[4],
                    lands_in_hand=row[5],
                    on_play=row[6],
                    timestamp=row[7],
                )
            )

        return decisions

    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]:
        """Get aggregated statistics for a specific hand composition."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            WHERE hand_signature = %s
        """,
            (hand_signature,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None or row[0] == 0:
            return None

        stats = HandStats(
            hand_signature=hand_signature, times_kept=row[1] or 0, times_mulled=row[2] or 0
        )
        stats.calculate_keep_percentage()
        return stats

    def get_all_hand_statistics(self) -> List[HandStats]:
        """Get statistics for all recorded hand compositions."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                hand_signature,
                SUM(CASE WHEN decision = 'keep' THEN 1 ELSE 0 END) as times_kept,
                SUM(CASE WHEN decision = 'mull' THEN 1 ELSE 0 END) as times_mulled
            FROM hand_decisions
            GROUP BY hand_signature
        """
        )

        rows = cursor.fetchall()
        conn.close()

        all_stats = []
        for row in rows:
            stats = HandStats(
                hand_signature=row[0], times_kept=row[1] or 0, times_mulled=row[2] or 0
            )
            stats.calculate_keep_percentage()
            all_stats.append(stats)

        return all_stats

    def list_decks_filtered(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> List[str]:
        """List deck IDs filtered by format, archetype, colors, and/or tags.

        Since metadata is stored as JSON arrays, we load all decks and filter in Python
        for better compatibility across SQLite versions.
        """
        all_deck_ids = self.list_decks()
        filtered_ids = []

        for deck_id in all_deck_ids:
            deck = self.load_deck(deck_id)
            if not deck:
                continue

            # If no filters provided, include all decks
            if mtg_format is None and archetype is None and colors is None and tags is None:
                filtered_ids.append(deck_id)
                continue

            # Check format filter (value must be IN deck.format list)
            if mtg_format is not None and mtg_format not in deck.format:
                continue

            # Check archetype filter (value must be IN deck.archetype list)
            if archetype is not None and archetype not in deck.archetype:
                continue

            # Check colors filter (value must be IN deck.colors list)
            if colors is not None and colors not in deck.colors:
                continue

            # Check tags filter (value must be IN deck.tags list)
            if tags is not None and tags not in deck.tags:
                continue

            # Deck passed all filters
            filtered_ids.append(deck_id)

        return filtered_ids

    def get_random_deck(
        self,
        mtg_format: Optional[str] = None,
        archetype: Optional[str] = None,
        colors: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Optional[DeckData]:
        """Get a random deck, optionally filtered by format, archetype, colors, and/or tags."""
        import random

        matching_deck_ids = self.list_decks_filtered(
            mtg_format=mtg_format, archetype=archetype, colors=colors, tags=tags
        )

        if not matching_deck_ids:
            return None

        random_deck_id = random.choice(matching_deck_ids)
        return self.load_deck(random_deck_id)


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
