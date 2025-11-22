"""Shared dependencies for the API."""

import uuid
from typing import Dict

from mtg_keep_or_mull.datastore import DataStore, MockDataStore
from mtg_keep_or_mull.mulligan import MulliganSimulator

# Global storage instances (will be dependency-injected)
_datastore: DataStore = MockDataStore()
_sessions: Dict[str, MulliganSimulator] = {}
_session_decks: Dict[str, str] = {}  # Maps session_id -> deck_id


def get_datastore() -> DataStore:
    """Get the global DataStore instance.

    Returns:
        DataStore instance
    """
    return _datastore


def get_sessions() -> Dict[str, MulliganSimulator]:
    """Get the global sessions dictionary.

    Returns:
        Dictionary mapping session_id -> MulliganSimulator
    """
    return _sessions


def get_session_decks() -> Dict[str, str]:
    """Get the session to deck mapping.

    Returns:
        Dictionary mapping session_id -> deck_id
    """
    return _session_decks


def create_session_id() -> str:
    """Generate a new unique session ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
