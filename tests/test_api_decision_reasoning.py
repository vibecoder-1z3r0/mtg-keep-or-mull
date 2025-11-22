"""Tests for decision reasoning tracking feature."""

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
        "/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Test Deck"}
    )
    deck_id: str = response.json()["deck_id"]
    return deck_id


def test_decision_with_reason_via_manual_endpoint(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that a decision can be recorded with a reason via the manual decision endpoint."""
    # Create session
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Record decision with reason
    response = client.post(
        f"/api/v1/sessions/{session_id}/decision",
        json={"decision": "mull", "reason": "Only 1 land, no action"},
    )
    assert response.status_code == 201

    # Get decision history and verify reason was stored
    decisions = client.get("/api/v1/decisions").json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["reason"] == "Only 1 land, no action"


def test_decision_with_reason_via_keep_endpoint(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that the /keep endpoint can accept and store a reason."""
    # Create session
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Keep with reason
    response = client.post(
        f"/api/v1/sessions/{session_id}/keep",
        json={"cards_to_bottom": [], "reason": "2 lands with cantrip"},
    )
    assert response.status_code == 200

    # Get decision history and verify reason was stored
    decisions = client.get("/api/v1/decisions").json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "keep"
    assert decisions[0]["reason"] == "2 lands with cantrip"


def test_decision_with_reason_via_mulligan_endpoint(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that the /mulligan endpoint can accept and store a reason."""
    # Create session
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Mulligan with reason
    response = client.post(
        f"/api/v1/sessions/{session_id}/mulligan",
        json={"reason": "Too many lands, not enough spells"},
    )
    assert response.status_code == 200

    # Get decision history and verify reason was stored
    decisions = client.get("/api/v1/decisions").json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "mull"
    assert decisions[0]["reason"] == "Too many lands, not enough spells"


def test_decision_without_reason_defaults_to_none(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that reason is optional and defaults to None."""
    # Create session
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Keep without providing reason
    response = client.post(
        f"/api/v1/sessions/{session_id}/keep", json={"cards_to_bottom": []}
    )
    assert response.status_code == 200

    # Get decision history and verify reason is None
    decisions = client.get("/api/v1/decisions").json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["reason"] is None


def test_decision_history_includes_reason_field(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that decision history responses include the reason field."""
    # Create session
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    session_id = session.json()["session_id"]

    # Make multiple decisions with different reasons
    client.post(
        f"/api/v1/sessions/{session_id}/mulligan",
        json={"reason": "All lands"},
    )
    mull_response = client.post(f"/api/v1/sessions/{session_id}/mulligan", json={})
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(
        f"/api/v1/sessions/{session_id}/keep",
        json={"cards_to_bottom": [card_to_bottom], "reason": "Good enough at 5"},
    )

    # Get decision history
    decisions = client.get("/api/v1/decisions").json()["decisions"]
    assert len(decisions) == 3

    # Verify all have reason field
    assert "reason" in decisions[0]
    assert "reason" in decisions[1]
    assert "reason" in decisions[2]

    # Verify specific reasons
    assert decisions[0]["reason"] == "All lands"
    assert decisions[1]["reason"] is None  # No reason provided
    assert decisions[2]["reason"] == "Good enough at 5"


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
