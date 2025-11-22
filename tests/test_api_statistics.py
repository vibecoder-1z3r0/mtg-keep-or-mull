"""Tests for statistics API endpoints."""

import pytest
from fastapi.testclient import TestClient

from mtg_keep_or_mull.api.app import app
from mtg_keep_or_mull.api.dependencies import _datastore, _session_decks, _sessions


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API.

    Returns:
        TestClient instance
    """
    # Clear state before each test
    _datastore._decks.clear()
    _datastore._decisions.clear()
    _sessions.clear()
    _session_decks.clear()
    return TestClient(app)


@pytest.fixture
def sample_deck_id(client: TestClient) -> str:
    """Create and upload a sample deck, return its ID.

    Args:
        client: Test client

    Returns:
        Deck ID
    """
    deck_text = """4 Brainstorm
4 Counterspell
20 Island
"""
    response = client.post("/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Test Deck"})
    return response.json()["deck_id"]


def test_get_all_hand_statistics_empty(client: TestClient) -> None:
    """Test getting all hand statistics when none exist."""
    response = client.get("/api/v1/statistics/hands")

    assert response.status_code == 200
    data = response.json()
    assert data["hands"] == []
    assert data["total"] == 0


def test_get_all_hand_statistics_with_data(client: TestClient, sample_deck_id: str) -> None:
    """Test getting all hand statistics after recording decisions."""
    # Start session and record some decisions
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Record a keep decision
    client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "keep"})

    # Start another session and record a mull decision
    start_response2 = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": False}
    )
    session_id2 = start_response2.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id2}/decision", json={"decision": "mull"})

    # Get statistics
    response = client.get("/api/v1/statistics/hands")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1  # At least one unique hand
    assert len(data["hands"]) >= 1


def test_get_hand_statistics_success(client: TestClient, sample_deck_id: str) -> None:
    """Test getting statistics for a specific hand."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]
    hand_signature = start_response.json()["current_hand"]["signature"]

    # Record a keep decision
    client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "keep"})

    # Get statistics for this hand
    response = client.get(f"/api/v1/statistics/hands/{hand_signature}")
    assert response.status_code == 200

    data = response.json()
    assert data["hand_signature"] == hand_signature
    assert data["times_kept"] == 1
    assert data["times_mulled"] == 0
    assert data["keep_percentage"] == 100.0
    assert data["total_decisions"] == 1


def test_get_hand_statistics_not_found(client: TestClient) -> None:
    """Test getting statistics for a hand that hasn't been seen."""
    response = client.get("/api/v1/statistics/hands/NonexistentHandSignature")
    assert response.status_code == 404


def test_get_hand_statistics_multiple_decisions(client: TestClient, sample_deck_id: str) -> None:
    """Test hand statistics with multiple decisions for same hand."""
    # We'll need to create the same hand multiple times
    # This is tricky with random shuffling, but we can record multiple decisions
    # on different hands and verify the aggregation works

    # Start session 1
    start1 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session1 = start1.json()["session_id"]
    client.post(f"/api/v1/sessions/{session1}/decision", json={"decision": "keep"})

    # Start session 2
    start2 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session2 = start2.json()["session_id"]
    client.post(f"/api/v1/sessions/{session2}/decision", json={"decision": "mull"})

    # Get all statistics - should have recorded 2 decisions
    response = client.get("/api/v1/statistics/hands")
    assert response.status_code == 200

    data = response.json()
    # We should have decisions recorded
    total_decisions = sum(hand["total_decisions"] for hand in data["hands"])
    assert total_decisions == 2


def test_get_deck_statistics_success(client: TestClient, sample_deck_id: str) -> None:
    """Test getting statistics for a specific deck."""
    # Start session and record a keep decision
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "keep"})

    # Get deck statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["deck_id"] == sample_deck_id
    assert data["total_games"] >= 1
    assert "mulligan_distribution" in data
    assert "average_mulligan_count" in data
    assert "hands_kept_at_7" in data


def test_get_deck_statistics_deck_not_found(client: TestClient) -> None:
    """Test getting statistics for non-existent deck."""
    response = client.get("/api/v1/statistics/decks/nonexistent_deck_id")
    assert response.status_code == 404


def test_get_deck_statistics_no_games(client: TestClient, sample_deck_id: str) -> None:
    """Test getting statistics for deck with no games played."""
    # Deck exists but no decisions recorded
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    assert response.status_code == 404
    assert "No statistics available" in response.json()["detail"]


def test_get_deck_statistics_multiple_games(client: TestClient, sample_deck_id: str) -> None:
    """Test deck statistics with multiple games."""
    # Game 1: Keep opening hand
    start1 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session1 = start1.json()["session_id"]
    client.post(f"/api/v1/sessions/{session1}/decision", json={"decision": "keep"})

    # Game 2: Mulligan once then keep
    start2 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session2 = start2.json()["session_id"]
    client.post(f"/api/v1/sessions/{session2}/decision", json={"decision": "mull"})
    client.post(f"/api/v1/sessions/{session2}/mulligan")
    client.post(f"/api/v1/sessions/{session2}/decision", json={"decision": "keep"})

    # Get statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total_games"] == 3  # 1 keep + 1 mull + 1 keep
    # JSON serializes int keys as strings
    assert data["mulligan_distribution"]["0"] == 1  # 1 hand kept at 7
    assert data["mulligan_distribution"]["1"] == 1  # 1 hand kept at 6


def test_deck_statistics_mulligan_distribution(client: TestClient, sample_deck_id: str) -> None:
    """Test that mulligan distribution is calculated correctly."""
    # Keep at 7
    start1 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session1 = start1.json()["session_id"]
    client.post(f"/api/v1/sessions/{session1}/decision", json={"decision": "keep"})

    # Mulligan to 6
    start2 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session2 = start2.json()["session_id"]
    client.post(f"/api/v1/sessions/{session2}/mulligan")
    client.post(f"/api/v1/sessions/{session2}/decision", json={"decision": "keep"})

    # Mulligan to 5
    start3 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session3 = start3.json()["session_id"]
    client.post(f"/api/v1/sessions/{session3}/mulligan")
    client.post(f"/api/v1/sessions/{session3}/mulligan")
    client.post(f"/api/v1/sessions/{session3}/decision", json={"decision": "keep"})

    # Get statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    data = response.json()

    assert data["hands_kept_at_7"] == 1
    assert data["hands_kept_at_6"] == 1
    assert data["hands_kept_at_5"] == 1
    assert data["average_mulligan_count"] == 1.0  # (0 + 1 + 2) / 3


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
