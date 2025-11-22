"""Tests for PATCH /api/v1/decks/{deck_id} endpoint - updating deck metadata."""

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


def test_patch_deck_update_all_metadata(client: TestClient) -> None:
    """Test updating all metadata fields at once."""
    # Create a deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Original Deck",
            "format": ["Pauper"],
            "archetype": ["Tempo"],
            "colors": ["U"],
            "tags": ["test"],
        },
    )
    assert upload_response.status_code == 201
    deck_id = upload_response.json()["deck_id"]

    # Update all metadata
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "deck_name": "Updated Deck Name",
            "format": ["Pauper", "Modern", "Legacy"],
            "archetype": ["Tempo", "Control"],
            "colors": ["U", "Mono-Blue"],
            "tags": ["updated", "multi-format"],
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["deck_name"] == "Updated Deck Name"
    assert data["format"] == ["Pauper", "Modern", "Legacy"]
    assert data["archetype"] == ["Tempo", "Control"]
    assert data["colors"] == ["U", "Mono-Blue"]
    assert data["tags"] == ["updated", "multi-format"]

    # Verify the deck was actually updated by fetching it
    get_response = client.get(f"/api/v1/decks/{deck_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["deck_name"] == "Updated Deck Name"
    assert get_data["format"] == ["Pauper", "Modern", "Legacy"]


def test_patch_deck_partial_update_format_only(client: TestClient) -> None:
    """Test updating only the format field."""
    # Create a deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Test Deck",
            "format": ["Pauper"],
            "archetype": ["Tempo"],
            "colors": ["U"],
            "tags": ["test"],
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # Update only format
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "format": ["Modern", "Pioneer"],
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["format"] == ["Modern", "Pioneer"]
    # Other fields should remain unchanged
    assert data["archetype"] == ["Tempo"]
    assert data["colors"] == ["U"]
    assert data["tags"] == ["test"]
    assert data["deck_name"] == "Test Deck"


def test_patch_deck_add_colors_and_tags(client: TestClient) -> None:
    """Test adding colors and tags to a deck that had none."""
    # Create deck with minimal metadata
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Minimal Deck",
            "format": ["Pauper"],
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # Add colors and tags
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "colors": ["U", "Mono-Blue"],
            "tags": ["permission", "card-draw"],
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["colors"] == ["U", "Mono-Blue"]
    assert data["tags"] == ["permission", "card-draw"]
    assert data["format"] == ["Pauper"]  # Unchanged


def test_patch_deck_clear_metadata(client: TestClient) -> None:
    """Test clearing metadata by setting to empty lists."""
    # Create deck with metadata
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Test Deck",
            "format": ["Pauper"],
            "archetype": ["Tempo"],
            "colors": ["U"],
            "tags": ["test"],
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # Clear all metadata
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "format": [],
            "archetype": [],
            "colors": [],
            "tags": [],
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["format"] == []
    assert data["archetype"] == []
    assert data["colors"] == []
    assert data["tags"] == []


def test_patch_deck_update_deck_name_only(client: TestClient) -> None:
    """Test updating only the deck name."""
    # Create deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Original Name",
            "format": ["Pauper"],
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # Update name
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "deck_name": "New Name",
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["deck_name"] == "New Name"
    assert data["format"] == ["Pauper"]  # Unchanged


def test_patch_deck_nonexistent_deck_returns_404(client: TestClient) -> None:
    """Test that updating a non-existent deck returns 404."""
    patch_response = client.patch(
        "/api/v1/decks/nonexistent_deck_id",
        json={
            "deck_name": "Updated Name",
        },
    )

    assert patch_response.status_code == 404
    assert "not found" in patch_response.json()["detail"].lower()


def test_patch_deck_preserves_main_deck_and_sideboard(client: TestClient) -> None:
    """Test that updating metadata doesn't affect main deck or sideboard."""
    # Create deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island\n\n15 Hydroblast",
            "deck_name": "Test Deck",
            "format": ["Pauper"],
        },
    )
    deck_id = upload_response.json()["deck_id"]
    original_main_size = upload_response.json()["main_deck_size"]
    original_side_size = upload_response.json()["sideboard_size"]

    # Update metadata
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={
            "format": ["Modern"],
            "archetype": ["Aggro"],
        },
    )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["main_deck_size"] == original_main_size
    assert data["sideboard_size"] == original_side_size


def test_patch_deck_empty_request_body_returns_400(client: TestClient) -> None:
    """Test that an empty update request returns 400."""
    # Create deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Test Deck",
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # Empty update
    patch_response = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={},
    )

    assert patch_response.status_code == 400
    assert "at least one field" in patch_response.json()["detail"].lower()


def test_patch_deck_multiple_updates_sequential(client: TestClient) -> None:
    """Test multiple sequential updates to the same deck."""
    # Create deck
    upload_response = client.post(
        "/api/v1/decks",
        json={
            "deck_text": "60 Island",
            "deck_name": "Test Deck",
            "format": ["Pauper"],
        },
    )
    deck_id = upload_response.json()["deck_id"]

    # First update: add archetype
    patch1 = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={"archetype": ["Tempo"]},
    )
    assert patch1.status_code == 200
    assert patch1.json()["archetype"] == ["Tempo"]

    # Second update: add colors
    patch2 = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={"colors": ["U"]},
    )
    assert patch2.status_code == 200
    data2 = patch2.json()
    assert data2["colors"] == ["U"]
    assert data2["archetype"] == ["Tempo"]  # Still there from first update

    # Third update: change format
    patch3 = client.patch(
        f"/api/v1/decks/{deck_id}",
        json={"format": ["Modern"]},
    )
    assert patch3.status_code == 200
    data3 = patch3.json()
    assert data3["format"] == ["Modern"]
    assert data3["archetype"] == ["Tempo"]  # Still there
    assert data3["colors"] == ["U"]  # Still there


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
