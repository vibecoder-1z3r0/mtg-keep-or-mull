"""Tests for session management API endpoints."""

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
4 Mental Note
20 Island
"""
    response = client.post(
        "/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Mono U Terror"}
    )
    return response.json()["deck_id"]


def test_start_session_success(client: TestClient, sample_deck_id: str) -> None:
    """Test starting a new practice session."""
    response = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})

    assert response.status_code == 201
    data = response.json()

    assert "session_id" in data
    assert data["deck_id"] == sample_deck_id
    assert data["on_play"] is True
    assert data["mulligan_count"] == 0
    assert "current_hand" in data
    assert data["current_hand"]["size"] == 7  # Opening hand is always 7


def test_start_session_deck_not_found(client: TestClient) -> None:
    """Test starting a session with non-existent deck."""
    response = client.post(
        "/api/v1/sessions", json={"deck_id": "nonexistent_deck", "on_play": True}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_session_success(client: TestClient, sample_deck_id: str) -> None:
    """Test getting session state."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": False}
    )
    session_id = start_response.json()["session_id"]

    # Get session
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session_id
    assert data["deck_id"] == sample_deck_id
    assert data["on_play"] is False
    assert data["mulligan_count"] == 0


def test_get_session_not_found(client: TestClient) -> None:
    """Test getting non-existent session."""
    response = client.get("/api/v1/sessions/nonexistent_session_id")
    assert response.status_code == 404


def test_mulligan_hand_success(client: TestClient, sample_deck_id: str) -> None:
    """Test taking a mulligan."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]
    original_hand = start_response.json()["current_hand"]["signature"]

    # Take mulligan
    response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    assert response.status_code == 200

    data = response.json()
    assert data["mulligan_count"] == 1
    assert data["current_hand"]["size"] == 7  # Still 7 cards (London mulligan)

    # Hand should be different (very unlikely to be the same)
    # Note: This could theoretically fail if we get the exact same hand
    new_hand = data["current_hand"]["signature"]
    # We won't assert they're different due to randomness, but check structure
    assert isinstance(new_hand, str)


def test_mulligan_session_not_found(client: TestClient) -> None:
    """Test mulliganing non-existent session."""
    response = client.post("/api/v1/sessions/nonexistent_session_id/mulligan")
    assert response.status_code == 404


def test_keep_hand_no_mulligan(client: TestClient, sample_deck_id: str) -> None:
    """Test keeping opening hand (no cards to bottom)."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Keep hand (no mulligans, so no cards to bottom)
    response = client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": []})

    assert response.status_code == 200
    data = response.json()
    assert data["current_hand"]["size"] == 7  # Full hand kept


def test_keep_hand_after_mulligan(client: TestClient, sample_deck_id: str) -> None:
    """Test keeping hand after one mulligan (bottom 1 card)."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Take mulligan
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    cards_in_hand = mull_response.json()["current_hand"]["cards"]
    card_to_bottom = cards_in_hand[0]["name"]

    # Keep hand, bottom 1 card
    response = client.post(
        f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": [card_to_bottom]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_hand"]["size"] == 6  # 7 - 1 bottomed


def test_keep_hand_wrong_count(client: TestClient, sample_deck_id: str) -> None:
    """Test keeping hand with wrong number of cards to bottom."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Take mulligan (should bottom 1)
    client.post(f"/api/v1/sessions/{session_id}/mulligan")

    # Try to keep without bottoming (should fail)
    response = client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": []})

    assert response.status_code == 400


def test_keep_hand_invalid_card(client: TestClient, sample_deck_id: str) -> None:
    """Test keeping hand with card not in hand."""
    # Start session and mulligan
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id}/mulligan")

    # Try to bottom a card not in hand
    response = client.post(
        f"/api/v1/sessions/{session_id}/keep",
        json={"cards_to_bottom": ["Card Not In Hand"]},
    )

    assert response.status_code == 400


def test_record_decision_keep(client: TestClient, sample_deck_id: str) -> None:
    """Test recording a keep decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Record decision
    response = client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "keep"})

    assert response.status_code == 201
    data = response.json()
    assert "message" in data


def test_record_decision_mull(client: TestClient, sample_deck_id: str) -> None:
    """Test recording a mulligan decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Record decision
    response = client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "mull"})

    assert response.status_code == 201


def test_record_decision_invalid(client: TestClient, sample_deck_id: str) -> None:
    """Test recording an invalid decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Try to record invalid decision
    response = client.post(
        f"/api/v1/sessions/{session_id}/decision", json={"decision": "invalid"}
    )

    assert response.status_code == 422  # Validation error


def test_end_session_success(client: TestClient, sample_deck_id: str) -> None:
    """Test ending a session."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # End session
    response = client.delete(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 204

    # Verify session is gone
    get_response = client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 404


def test_end_session_not_found(client: TestClient) -> None:
    """Test ending non-existent session."""
    response = client.delete("/api/v1/sessions/nonexistent_session_id")
    assert response.status_code == 404


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
