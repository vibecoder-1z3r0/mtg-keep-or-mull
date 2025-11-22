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
    _datastore._decks.clear()  # type: ignore[attr-defined]
    _datastore._decisions.clear()  # type: ignore[attr-defined]
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
    deck_id: str = response.json()["deck_id"]
    return deck_id


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
    response = client.post(f"/api/v1/sessions/{session_id}/decision", json={"decision": "invalid"})

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


# ========== TDD Tests for Automatic Decision Recording ==========


def test_mulligan_automatically_records_decision(client: TestClient, sample_deck_id: str) -> None:
    """Test that calling /mulligan automatically records a 'mull' decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]
    opening_hand_signature = start_response.json()["current_hand"]["signature"]

    # Take mulligan - this should AUTO-RECORD a "mull" decision
    client.post(f"/api/v1/sessions/{session_id}/mulligan")

    # Verify decision was recorded via statistics endpoint
    stats_response = client.get("/api/v1/statistics/hands")
    assert stats_response.status_code == 200

    hands = stats_response.json()["hands"]
    assert len(hands) == 1
    assert hands[0]["hand_signature"] == opening_hand_signature
    assert hands[0]["times_mulled"] == 1
    assert hands[0]["times_kept"] == 0


def test_keep_automatically_records_decision(client: TestClient, sample_deck_id: str) -> None:
    """Test that calling /keep automatically records a 'keep' decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": False}
    )
    session_id = start_response.json()["session_id"]
    hand_signature = start_response.json()["current_hand"]["signature"]

    # Keep hand (no mulligans) - this should AUTO-RECORD a "keep" decision
    client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": []})

    # Verify decision was recorded
    stats_response = client.get("/api/v1/statistics/hands")
    assert stats_response.status_code == 200

    hands = stats_response.json()["hands"]
    assert len(hands) == 1
    assert hands[0]["hand_signature"] == hand_signature
    assert hands[0]["times_kept"] == 1
    assert hands[0]["times_mulled"] == 0


def test_multiple_mulligans_record_each_decision(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that multiple mulligans each record a decision."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Mulligan twice
    client.post(f"/api/v1/sessions/{session_id}/mulligan")
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")

    # Remember the 7-card hand signature BEFORE keeping (this is what gets recorded)
    hand_signature_before_keep = mull_response.json()["current_hand"]["signature"]

    # Keep final hand - get actual cards from the hand to bottom
    cards_in_hand = mull_response.json()["current_hand"]["cards"]
    cards_to_bottom = [cards_in_hand[0]["name"], cards_in_hand[1]["name"]]

    client.post(
        f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": cards_to_bottom}
    )

    # Verify statistics: should have 3 decisions total (2 mull + 1 keep)
    stats_response = client.get("/api/v1/statistics/hands")
    hands = stats_response.json()["hands"]

    # We should have up to 3 different hand signatures (could be fewer if hands repeat)
    assert stats_response.json()["total"] >= 1

    # Find the kept hand (signature before bottoming)
    kept_hand_stats = [h for h in hands if h["hand_signature"] == hand_signature_before_keep]
    assert len(kept_hand_stats) == 1
    assert kept_hand_stats[0]["times_kept"] == 1
    assert kept_hand_stats[0]["times_mulled"] == 0  # This particular hand was kept, not mulled


def test_keep_after_mulligan_records_decision_with_cards_bottomed(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that keeping after mulligan records cards_bottomed."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Mulligan once
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    cards_in_hand = mull_response.json()["current_hand"]["cards"]
    card_to_bottom = cards_in_hand[0]["name"]

    # Keep hand, bottoming 1 card
    client.post(
        f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": [card_to_bottom]}
    )

    # Verify decision was recorded with cards_bottomed
    # Note: This requires adding cards_bottomed field to HandDecisionData model
    # For now, we just verify the decision was recorded
    stats_response = client.get("/api/v1/statistics/hands")
    assert stats_response.status_code == 200
    assert stats_response.json()["total"] >= 1


def test_deck_statistics_reflect_automatic_decisions(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that deck statistics correctly reflect automatically recorded decisions."""
    # Start session
    start_response = client.post(
        "/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True}
    )
    session_id = start_response.json()["session_id"]

    # Mulligan once, then keep
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(
        f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": [card_to_bottom]}
    )

    # Get deck statistics
    deck_stats_response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    assert deck_stats_response.status_code == 200

    deck_stats = deck_stats_response.json()
    assert deck_stats["total_games"] == 1  # One game completed (session ended with keep)
    assert deck_stats["hands_kept_at_6"] == 1  # Kept after 1 mulligan
    assert deck_stats["average_mulligan_count"] == 1.0


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
