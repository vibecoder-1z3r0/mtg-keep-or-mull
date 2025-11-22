"""Tests for deck filtering and random selection API endpoints with list-based metadata."""

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
    # Upload a deck with list-based metadata
    deck_text = "4 Island\n4 Delver of Secrets"
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": deck_text,
            "deck_name": "Test Deck",
            "format": ["Pauper"],
            "archetype": ["Tempo"],
            "colors": ["U"],
            "tags": ["test"],
        },
    )
    assert upload_response.status_code == 201

    # Get random deck
    response = client.get("/api/v1/decks/random")
    assert response.status_code == 200
    data = response.json()
    assert "deck_id" in data
    assert "deck_name" in data
    assert data["deck_name"] == "Test Deck"
    assert data["format"] == ["Pauper"]
    assert data["archetype"] == ["Tempo"]
    assert data["colors"] == ["U"]
    assert data["tags"] == ["test"]


def test_get_random_deck_filtered_by_format(client: TestClient) -> None:
    """Test getting random deck filtered by format (value IN list logic)."""
    # Upload decks with different formats
    pauper_deck = """4 Island
4 Delver of Secrets"""
    modern_deck = """4 Scalding Tarn
4 Lightning Bolt"""

    client.post(
        "/api/v1/decks",
        json={
            "deck_text": pauper_deck,
            "deck_name": "Pauper Deck",
            "format": ["Pauper", "Legacy"],  # Multi-format deck
        },
    )
    client.post(
        "/api/v1/decks",
        json={"deck_text": modern_deck, "deck_name": "Modern Deck", "format": ["Modern"]},
    )

    # Get random Pauper deck (should match first deck which has Pauper IN its format list)
    response = client.get("/api/v1/decks/random?format=Pauper")
    assert response.status_code == 200
    data = response.json()
    assert "Pauper" in data["format"]

    # Get random Modern deck
    response = client.get("/api/v1/decks/random?format=Modern")
    assert response.status_code == 200
    data = response.json()
    assert "Modern" in data["format"]


def test_get_random_deck_filtered_by_archetype(client: TestClient) -> None:
    """Test getting random deck filtered by archetype (value IN list logic)."""
    # Upload decks with different archetypes
    aggro_deck = """20 Mountain
4 Lightning Bolt"""
    control_deck = """20 Island
4 Counterspell"""

    client.post(
        "/api/v1/decks",
        json={
            "deck_text": aggro_deck,
            "deck_name": "Aggro Deck",
            "archetype": ["Aggro", "Burn"],  # Hybrid archetype
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": control_deck,
            "deck_name": "Control Deck",
            "archetype": ["Control"],
        },
    )

    # Get random Aggro deck
    response = client.get("/api/v1/decks/random?archetype=Aggro")
    assert response.status_code == 200
    assert "Aggro" in response.json()["archetype"]

    # Get random Control deck
    response = client.get("/api/v1/decks/random?archetype=Control")
    assert response.status_code == 200
    assert "Control" in response.json()["archetype"]


def test_get_random_deck_filtered_by_colors(client: TestClient) -> None:
    """Test getting random deck filtered by colors."""
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Blue Deck",
            "colors": ["U", "Mono-Blue"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "10 Island\n10 Swamp",
            "deck_name": "Dimir Deck",
            "colors": ["Dimir", "U", "B", "UB"],
        },
    )

    # Get random deck with U
    response = client.get("/api/v1/decks/random?colors=U")
    assert response.status_code == 200
    assert "U" in response.json()["colors"]

    # Get random Dimir deck
    response = client.get("/api/v1/decks/random?colors=Dimir")
    assert response.status_code == 200
    assert "Dimir" in response.json()["colors"]


def test_get_random_deck_filtered_by_tags(client: TestClient) -> None:
    """Test getting random deck filtered by tags."""
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain\n4 Lightning Bolt",
            "deck_name": "Burn",
            "tags": ["burn", "aggro", "budget"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island\n4 Delver of Secrets",
            "deck_name": "Delver",
            "tags": ["delver", "tempo", "tournament"],
        },
    )

    # Get random burn deck
    response = client.get("/api/v1/decks/random?tags=burn")
    assert response.status_code == 200
    assert "burn" in response.json()["tags"]

    # Get random tournament deck
    response = client.get("/api/v1/decks/random?tags=tournament")
    assert response.status_code == 200
    assert "tournament" in response.json()["tags"]


def test_get_random_deck_filtered_by_multiple_criteria(client: TestClient) -> None:
    """Test getting random deck filtered by multiple criteria (AND logic)."""
    # Upload multiple decks
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island\n4 Delver of Secrets",
            "deck_name": "Pauper Tempo",
            "format": ["Pauper", "Modern"],
            "archetype": ["Tempo"],
            "colors": ["U"],
            "tags": ["delver"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain\n4 Lightning Bolt",
            "deck_name": "Pauper Aggro",
            "format": ["Pauper"],
            "archetype": ["Aggro"],
            "colors": ["R"],
            "tags": ["burn"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "4 Scalding Tarn\n4 Delver of Secrets",
            "deck_name": "Modern Tempo",
            "format": ["Modern"],
            "archetype": ["Tempo"],
            "colors": ["U", "R"],
            "tags": ["delver"],
        },
    )

    # Get random Pauper Tempo deck with delver tag
    response = client.get("/api/v1/decks/random?format=Pauper&archetype=Tempo&tags=delver")
    assert response.status_code == 200
    data = response.json()
    assert "Pauper" in data["format"]
    assert "Tempo" in data["archetype"]
    assert "delver" in data["tags"]
    assert data["deck_name"] == "Pauper Tempo"


def test_get_random_deck_no_match_returns_404(client: TestClient) -> None:
    """Test that random deck returns 404 when no decks match filters."""
    # Upload a Pauper deck
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Deck",
            "format": ["Pauper"],
        },
    )

    # Try to get random Modern deck (should fail)
    response = client.get("/api/v1/decks/random?format=Modern")
    assert response.status_code == 404

    # Try to get random deck with non-existent tag
    response = client.get("/api/v1/decks/random?tags=nonexistent")
    assert response.status_code == 404


def test_list_decks_filtered_by_format(client: TestClient) -> None:
    """Test listing decks filtered by format."""
    # Upload decks with different formats
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Deck 1",
            "format": ["Pauper", "Modern"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Deck 2",
            "format": ["Pauper"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Modern Only",
            "format": ["Modern"],
        },
    )

    # List Pauper decks (should find 2)
    response = client.get("/api/v1/decks?format=Pauper")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Pauper" in deck["format"] for deck in data["decks"])

    # List Modern decks (should find 2)
    response = client.get("/api/v1/decks?format=Modern")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_decks_filtered_by_archetype(client: TestClient) -> None:
    """Test listing decks filtered by archetype."""
    # Upload decks with different archetypes
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Aggro 1",
            "archetype": ["Aggro", "Burn"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Aggro 2",
            "archetype": ["Aggro"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Control",
            "archetype": ["Control"],
        },
    )

    # List Aggro decks
    response = client.get("/api/v1/decks?archetype=Aggro")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Aggro" in deck["archetype"] for deck in data["decks"])


def test_list_decks_filtered_by_colors(client: TestClient) -> None:
    """Test listing decks filtered by colors."""
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Blue 1",
            "colors": ["U", "Mono-Blue"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "10 Island\n10 Swamp",
            "deck_name": "Dimir",
            "colors": ["U", "B", "Dimir"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Red",
            "colors": ["R"],
        },
    )

    # List blue decks (should find Blue 1 and Dimir)
    response = client.get("/api/v1/decks?colors=U")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("U" in deck["colors"] for deck in data["decks"])


def test_list_decks_filtered_by_tags(client: TestClient) -> None:
    """Test listing decks filtered by tags."""
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Budget Burn",
            "tags": ["budget", "burn"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "4 Scalding Tarn",
            "deck_name": "Expensive Deck",
            "tags": ["tournament", "expensive"],
        },
    )

    # List budget decks
    response = client.get("/api/v1/decks?tags=budget")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "budget" in data["decks"][0]["tags"]


def test_list_decks_filtered_by_multiple_criteria(client: TestClient) -> None:
    """Test listing decks filtered by multiple criteria."""
    # Upload multiple decks
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Pauper Control",
            "format": ["Pauper"],
            "archetype": ["Control"],
            "colors": ["U"],
            "tags": ["permission"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Mountain",
            "deck_name": "Pauper Aggro",
            "format": ["Pauper"],
            "archetype": ["Aggro"],
            "colors": ["R"],
            "tags": ["burn"],
        },
    )
    client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Modern Control",
            "format": ["Modern"],
            "archetype": ["Control"],
            "colors": ["U"],
            "tags": ["permission"],
        },
    )

    # List Pauper Control decks with U
    response = client.get("/api/v1/decks?format=Pauper&archetype=Control&colors=U")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    deck = data["decks"][0]
    assert "Pauper" in deck["format"]
    assert "Control" in deck["archetype"]
    assert "U" in deck["colors"]


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


def test_upload_deck_with_list_metadata(client: TestClient) -> None:
    """Test uploading a deck with list-based metadata."""
    response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island\n4 Delver of Secrets",
            "deck_name": "Multi-format Delver",
            "format": ["Pauper", "Modern", "Legacy", "Vintage"],
            "archetype": ["Tempo", "Aggro"],
            "colors": ["U", "Mono-Blue"],
            "tags": ["delver", "permission", "cantrips", "tournament"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["format"] == ["Pauper", "Modern", "Legacy", "Vintage"]
    assert data["archetype"] == ["Tempo", "Aggro"]
    assert data["colors"] == ["U", "Mono-Blue"]
    assert data["tags"] == ["delver", "permission", "cantrips", "tournament"]


def test_upload_deck_with_empty_lists(client: TestClient) -> None:
    """Test uploading a deck with empty metadata lists (defaults)."""
    response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "20 Island",
            "deck_name": "Minimal Deck",
            # No metadata provided - should default to empty lists
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["format"] == []
    assert data["archetype"] == []
    assert data["colors"] == []
    assert data["tags"] == []


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
