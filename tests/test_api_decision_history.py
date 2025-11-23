"""Tests for decision history API endpoint."""

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
    response = client.post("/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Test Deck"})
    deck_id: str = response.json()["deck_id"]
    return deck_id


def test_get_all_decisions_empty(client: TestClient) -> None:
    """Test getting decisions when none exist."""
    response = client.get("/api/v1/decisions")
    assert response.status_code == 200
    data = response.json()
    assert data["decisions"] == []
    assert data["total"] == 0


def test_get_all_decisions_returns_chronological_list(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that decisions are returned in chronological order."""
    # Create a session and make multiple decisions
    start = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = start.json()["session_id"]

    # Mull twice, then keep
    client.post(f"/api/v1/sessions/{session_id}/mulligan")
    client.post(f"/api/v1/sessions/{session_id}/mulligan")
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": [card_to_bottom]})

    # Get all decisions
    response = client.get("/api/v1/decisions")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 4  # 3 mulls + 1 keep
    assert len(data["decisions"]) == 4

    # Verify chronological order (oldest first)
    decisions = data["decisions"]
    for i in range(len(decisions) - 1):
        assert decisions[i]["timestamp"] <= decisions[i + 1]["timestamp"]

    # Verify decision types
    assert decisions[0]["decision"] == "mull"
    assert decisions[1]["decision"] == "mull"
    assert decisions[2]["decision"] == "mull"
    assert decisions[3]["decision"] == "keep"


def test_get_decisions_filtered_by_deck(client: TestClient, sample_deck_id: str) -> None:
    """Test filtering decisions by deck_id."""
    # Create second deck
    deck_text2 = "20 Mountain\n20 Lightning Bolt"
    deck2_response = client.post(
        "/api/v1/decks", json={"deck_text": deck_text2, "deck_name": "Red Deck"}
    )
    deck2_id = deck2_response.json()["deck_id"]

    # Make decisions for deck 1
    session1 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(
        f"/api/v1/sessions/{session1.json()['session_id']}/keep", json={"cards_to_bottom": []}
    )

    # Make decisions for deck 2
    session2 = client.post("/api/v1/sessions", json={"deck_id": deck2_id, "on_play": False})
    client.post(f"/api/v1/sessions/{session2.json()['session_id']}/mulligan")

    # Filter by deck 1
    response = client.get(f"/api/v1/decisions?deck_id={sample_deck_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["decisions"][0]["deck_id"] == sample_deck_id


def test_get_decisions_includes_cards_bottomed(client: TestClient, sample_deck_id: str) -> None:
    """Test that decision history includes cards_bottomed field."""
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Mulligan once
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]

    # Keep with bottomed card
    client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": [card_to_bottom]})

    # Get decisions
    response = client.get("/api/v1/decisions")
    data = response.json()

    # Find the keep decision
    keep_decisions = [d for d in data["decisions"] if d["decision"] == "keep"]
    assert len(keep_decisions) == 1
    assert "cards_bottomed" in keep_decisions[0]
    assert keep_decisions[0]["cards_bottomed"] == [card_to_bottom]


def test_get_decisions_includes_all_fields(client: TestClient, sample_deck_id: str) -> None:
    """Test that all decision fields are included in response."""
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": []})

    response = client.get("/api/v1/decisions")
    decisions = response.json()["decisions"]

    assert len(decisions) == 1
    decision = decisions[0]

    # Verify all expected fields are present
    assert "hand_signature" in decision
    assert "hand_display" in decision
    assert "mulligan_count" in decision
    assert "decision" in decision
    assert "lands_in_hand" in decision
    assert "on_play" in decision
    assert "timestamp" in decision
    assert "deck_id" in decision
    assert "cards_bottomed" in decision


def test_get_decisions_pagination(client: TestClient, sample_deck_id: str) -> None:
    """Test pagination of decision history."""
    # Create 15 decisions
    for _ in range(15):
        session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
        client.post(
            f"/api/v1/sessions/{session.json()['session_id']}/keep", json={"cards_to_bottom": []}
        )

    # Get first page
    response = client.get("/api/v1/decisions?limit=10")
    data = response.json()
    assert data["total"] == 15
    assert len(data["decisions"]) == 10

    # Get second page
    response2 = client.get("/api/v1/decisions?limit=10&offset=10")
    data2 = response2.json()
    assert data2["total"] == 15
    assert len(data2["decisions"]) == 5


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
