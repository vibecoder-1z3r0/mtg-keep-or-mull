"""Tests for deck filtering and random selection API endpoints."""

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


def test_get_random_deck_empty_datastore(client: TestClient) -> None:
    """Test getting random deck when no decks exist."""
    response = client.get("/api/v1/decks/random")
    assert response.status_code == 404
    assert "No decks available" in response.json()["detail"]


def test_get_random_deck_returns_deck(client: TestClient) -> None:
    """Test getting a random deck from populated datastore."""
    # Upload a deck
    deck_text = "4 Island\n4 Delver of Secrets"
    upload_response = client.post(
        "/api/v1/decks",
        json={"deck_text": deck_text, "deck_name": "Test Deck"},
    )
    assert upload_response.status_code == 201

    # Get random deck
    response = client.get("/api/v1/decks/random")
    assert response.status_code == 200
    data = response.json()
    assert "deck_id" in data
    assert "deck_name" in data
    assert data["deck_name"] == "Test Deck"


def test_get_random_deck_filtered_by_format(client: TestClient) -> None:
    """Test getting random deck filtered by format."""
    # Upload decks with different formats
    pauper_deck = """4 Island
4 Delver of Secrets"""
    modern_deck = """4 Scalding Tarn
4 Lightning Bolt"""

    client.post(
        "/api/v1/decks",
        json={"deck_text": pauper_deck, "deck_name": "Pauper Deck", "format": "Pauper"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": modern_deck, "deck_name": "Modern Deck", "format": "Modern"},
    )

    # Get random Pauper deck
    response = client.get("/api/v1/decks/random?format=Pauper")
    assert response.status_code == 200
    assert response.json()["format"] == "Pauper"

    # Get random Modern deck
    response = client.get("/api/v1/decks/random?format=Modern")
    assert response.status_code == 200
    assert response.json()["format"] == "Modern"


def test_get_random_deck_filtered_by_archetype(client: TestClient) -> None:
    """Test getting random deck filtered by archetype."""
    # Upload decks with different archetypes
    aggro_deck = """20 Mountain
4 Lightning Bolt"""
    control_deck = """20 Island
4 Counterspell"""

    client.post(
        "/api/v1/decks",
        json={"deck_text": aggro_deck, "deck_name": "Aggro Deck", "archetype": "Aggro"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": control_deck, "deck_name": "Control Deck", "archetype": "Control"},
    )

    # Get random Aggro deck
    response = client.get("/api/v1/decks/random?archetype=Aggro")
    assert response.status_code == 200
    assert response.json()["archetype"] == "Aggro"

    # Get random Control deck
    response = client.get("/api/v1/decks/random?archetype=Control")
    assert response.status_code == 200
    assert response.json()["archetype"] == "Control"


def test_get_random_deck_filtered_by_both(client: TestClient) -> None:
    """Test getting random deck filtered by both format and archetype."""
    # Upload multiple decks
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island\n4 Delver of Secrets",
            "deck_name": "Pauper Tempo",
            "format": "Pauper",
            "archetype": "Tempo",
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain\n4 Lightning Bolt",
            "deck_name": "Pauper Aggro",
            "format": "Pauper",
            "archetype": "Aggro",
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "4 Scalding Tarn\n4 Delver of Secrets",
            "deck_name": "Modern Tempo",
            "format": "Modern",
            "archetype": "Tempo",
        },
    )

    # Get random Pauper Tempo deck
    response = client.get("/api/v1/decks/random?format=Pauper&archetype=Tempo")
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "Pauper"
    assert data["archetype"] == "Tempo"


def test_get_random_deck_no_match_returns_404(client: TestClient) -> None:
    """Test that random deck returns 404 when no decks match filters."""
    # Upload a Pauper deck
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Deck",
            "format": "Pauper",
        },
    )

    # Try to get random Modern deck (should fail)
    response = client.get("/api/v1/decks/random?format=Modern")
    assert response.status_code == 404


def test_list_decks_filtered_by_format(client: TestClient) -> None:
    """Test listing decks filtered by format."""
    # Upload decks with different formats
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Island", "deck_name": "Pauper Deck 1", "format": "Pauper"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Island", "deck_name": "Pauper Deck 2", "format": "Pauper"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Island", "deck_name": "Modern Deck", "format": "Modern"},
    )

    # List Pauper decks
    response = client.get("/api/v1/decks?format=Pauper")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(deck["format"] == "Pauper" for deck in data["decks"])


def test_list_decks_filtered_by_archetype(client: TestClient) -> None:
    """Test listing decks filtered by archetype."""
    # Upload decks with different archetypes
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Mountain", "deck_name": "Aggro 1", "archetype": "Aggro"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Mountain", "deck_name": "Aggro 2", "archetype": "Aggro"},
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": "20 Island", "deck_name": "Control", "archetype": "Control"},
    )

    # List Aggro decks
    response = client.get("/api/v1/decks?archetype=Aggro")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(deck["archetype"] == "Aggro" for deck in data["decks"])


def test_list_decks_filtered_by_both(client: TestClient) -> None:
    """Test listing decks filtered by both format and archetype."""
    # Upload multiple decks
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Control",
            "format": "Pauper",
            "archetype": "Control",
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Pauper Aggro",
            "format": "Pauper",
            "archetype": "Aggro",
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Modern Control",
            "format": "Modern",
            "archetype": "Control",
        },
    )

    # List Pauper Control decks
    response = client.get("/api/v1/decks?format=Pauper&archetype=Control")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    deck = data["decks"][0]
    assert deck["format"] == "Pauper"
    assert deck["archetype"] == "Control"


def test_list_decks_no_filters_returns_all(client: TestClient) -> None:
    """Test listing all decks when no filters provided."""
    # Upload 3 decks
    for i in range(3):
        client.post(
            "/api/v1/decks",
            json={"deck_text": "20 Island", "deck_name": f"Deck {i}"},
        )

    # List all decks
    response = client.get("/api/v1/decks")
    assert response.status_code == 200
    assert response.json()["total"] == 3


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
