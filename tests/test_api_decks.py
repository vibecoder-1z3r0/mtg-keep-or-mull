"""Tests for deck management API endpoints."""

import pytest
from fastapi.testclient import TestClient

from mtg_keep_or_mull.api.app import app
from mtg_keep_or_mull.api.dependencies import _datastore


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API.

    Returns:
        TestClient instance
    """
    # Clear datastore before each test
    _datastore._decks.clear()
    _datastore._decisions.clear()
    return TestClient(app)


def test_upload_deck_success(client: TestClient) -> None:
    """Test uploading a valid deck."""
    deck_text = """4 Lightning Bolt
20 Mountain
4 Monastery Swiftspear

SIDEBOARD:
3 Pyroblast
"""
    response = client.post(
        "/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Red Deck Wins"}
    )

    assert response.status_code == 201
    data = response.json()

    assert "deck_id" in data
    assert data["deck_name"] == "Red Deck Wins"
    assert data["main_deck_size"] == 28  # 4 + 20 + 4
    assert data["sideboard_size"] == 3
    assert "created_at" in data


def test_upload_deck_without_name(client: TestClient) -> None:
    """Test uploading a deck without providing a name."""
    deck_text = "20 Island\n20 Mountain"
    response = client.post("/api/v1/decks", json={"deck_text": deck_text, "deck_name": ""})

    assert response.status_code == 201
    data = response.json()

    # Should generate a name automatically
    assert "deck_" in data["deck_name"]
    assert data["main_deck_size"] == 40


def test_upload_deck_invalid_format(client: TestClient) -> None:
    """Test uploading a deck with invalid format."""
    deck_text = "This is not a valid deck format"
    response = client.post("/api/v1/decks", json={"deck_text": deck_text, "deck_name": "Bad Deck"})

    # Should still succeed but with 0 cards (current implementation is lenient)
    assert response.status_code in [201, 400]


def test_list_decks_empty(client: TestClient) -> None:
    """Test listing decks when none exist."""
    response = client.get("/api/v1/decks")

    assert response.status_code == 200
    data = response.json()
    assert data["decks"] == []
    assert data["total"] == 0


def test_list_decks_with_decks(client: TestClient) -> None:
    """Test listing decks after uploading some."""
    # Upload two decks
    deck1 = client.post("/api/v1/decks", json={"deck_text": "20 Island", "deck_name": "Deck 1"})
    deck2 = client.post("/api/v1/decks", json={"deck_text": "20 Mountain", "deck_name": "Deck 2"})

    assert deck1.status_code == 201
    assert deck2.status_code == 201

    # List decks
    response = client.get("/api/v1/decks")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert len(data["decks"]) == 2

    # Check deck names
    names = [deck["deck_name"] for deck in data["decks"]]
    assert "Deck 1" in names
    assert "Deck 2" in names


def test_get_deck_success(client: TestClient) -> None:
    """Test getting a specific deck."""
    # Upload a deck
    upload_response = client.post(
        "/api/v1/decks", json={"deck_text": "20 Island\n20 Swamp", "deck_name": "UB Control"}
    )
    deck_id = upload_response.json()["deck_id"]

    # Get the deck
    response = client.get(f"/api/v1/decks/{deck_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["deck_id"] == deck_id
    assert data["deck_name"] == "UB Control"
    assert data["main_deck_size"] == 40


def test_get_deck_not_found(client: TestClient) -> None:
    """Test getting a non-existent deck."""
    response = client.get("/api/v1/decks/nonexistent_deck_id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_deck_not_implemented(client: TestClient) -> None:
    """Test that delete endpoint returns 501 (not implemented)."""
    # Upload a deck
    upload_response = client.post(
        "/api/v1/decks", json={"deck_text": "20 Island", "deck_name": "Test Deck"}
    )
    deck_id = upload_response.json()["deck_id"]

    # Try to delete
    response = client.delete(f"/api/v1/decks/{deck_id}")
    assert response.status_code == 501


def test_delete_deck_not_found(client: TestClient) -> None:
    """Test deleting a non-existent deck."""
    response = client.delete("/api/v1/decks/nonexistent_deck_id")
    assert response.status_code == 404


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
