"""Tests for keep rate by mulligan depth statistics."""

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


def test_deck_stats_includes_keep_rate_by_depth(client: TestClient, sample_deck_id: str) -> None:
    """Test that deck statistics include keep_rate_by_mulligan_count."""
    # Play several games with different mulligan depths
    # Game 1: Keep opening 7
    session1 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(
        f"/api/v1/sessions/{session1.json()['session_id']}/keep",
        json={"cards_to_bottom": []},
    )

    # Game 2: Mull to 6, then keep
    session2 = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    mull_response = client.post(f"/api/v1/sessions/{session2.json()['session_id']}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(
        f"/api/v1/sessions/{session2.json()['session_id']}/keep",
        json={"cards_to_bottom": [card_to_bottom]},
    )

    # Get deck statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    assert response.status_code == 200

    stats = response.json()
    assert "keep_rate_by_mulligan_count" in stats
    assert isinstance(stats["keep_rate_by_mulligan_count"], dict)


def test_keep_rate_by_depth_calculates_correctly(client: TestClient, sample_deck_id: str) -> None:
    """Test that keep rates are calculated correctly for each mulligan depth."""
    # Create multiple sessions at mulligan depth 0 (opening 7)
    # Keep 2 out of 3
    for _ in range(2):
        session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
        client.post(
            f"/api/v1/sessions/{session.json()['session_id']}/keep",
            json={"cards_to_bottom": []},
        )

    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    # This game ends without a keep, so we need to complete it
    mull_response = client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(
        f"/api/v1/sessions/{session.json()['session_id']}/keep",
        json={"cards_to_bottom": [card_to_bottom]},
    )

    # Create sessions at mulligan depth 1 (mull to 6)
    # Keep 1 out of 2
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    mull_response = client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    card_to_bottom = mull_response.json()["current_hand"]["cards"][0]["name"]
    client.post(
        f"/api/v1/sessions/{session.json()['session_id']}/keep",
        json={"cards_to_bottom": [card_to_bottom]},
    )

    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    mull_response = client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    cards_to_bottom = [
        mull_response.json()["current_hand"]["cards"][0]["name"],
        mull_response.json()["current_hand"]["cards"][1]["name"],
    ]
    client.post(
        f"/api/v1/sessions/{session.json()['session_id']}/keep",
        json={"cards_to_bottom": cards_to_bottom},
    )

    # Get deck statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    stats = response.json()

    # Check keep rates by depth
    keep_rates = stats["keep_rate_by_mulligan_count"]

    # At depth 0 (opening 7): 2 keeps, 3 total hands seen (2 kept + 1 mulled)
    # Actually, we need to count ALL hands seen at depth 0 across all games
    # In the games above:
    # Game 1: kept at 0
    # Game 2: kept at 0
    # Game 3: mulled from 0, mulled from 1, kept at 2
    # Game 4: mulled from 0, kept at 1
    # Game 5: mulled from 0, mulled from 1, kept at 2
    # So at depth 0: 2 keeps + 3 mulls = 5 total, keep rate = 2/5 = 40%
    assert "0" in keep_rates
    assert keep_rates["0"] == pytest.approx(40.0, abs=0.1)

    # At depth 1 (mull to 6):
    # Game 3: mulled from 1
    # Game 4: kept at 1
    # Game 5: mulled from 1
    # So 1 keep at depth 1, 3 total decisions at depth 1 = 1/3 = 33.33%
    assert "1" in keep_rates
    assert keep_rates["1"] == pytest.approx(33.33, abs=0.1)


def test_keep_rate_by_depth_handles_no_decisions_at_depth(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test that keep rate by depth handles depths with no decisions gracefully."""
    # Only keep at depth 0
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(
        f"/api/v1/sessions/{session.json()['session_id']}/keep",
        json={"cards_to_bottom": []},
    )

    # Get deck statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    stats = response.json()

    keep_rates = stats["keep_rate_by_mulligan_count"]

    # Should have data for depth 0
    assert "0" in keep_rates
    assert keep_rates["0"] == 100.0  # 1 keep, 1 total hand at depth 0

    # Should not have data for depths with no decisions
    assert "1" not in keep_rates or keep_rates["1"] == 0.0
    assert "2" not in keep_rates or keep_rates["2"] == 0.0


def test_keep_rate_by_depth_with_all_mulls_at_depth(
    client: TestClient, sample_deck_id: str
) -> None:
    """Test keep rate when all hands at a depth are mulliganed."""
    # Mull from 7, mull from 6, keep at 5
    session = client.post("/api/v1/sessions", json={"deck_id": sample_deck_id, "on_play": True})
    client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    mull_response = client.post(f"/api/v1/sessions/{session.json()['session_id']}/mulligan")
    cards_to_bottom = [
        mull_response.json()["current_hand"]["cards"][0]["name"],
        mull_response.json()["current_hand"]["cards"][1]["name"],
    ]
    client.post(
        f"/api/v1/sessions/{session.json()['session_id']}/keep",
        json={"cards_to_bottom": cards_to_bottom},
    )

    # Get deck statistics
    response = client.get(f"/api/v1/statistics/decks/{sample_deck_id}")
    stats = response.json()

    keep_rates = stats["keep_rate_by_mulligan_count"]

    # At depth 0: 0 keeps, 1 total hand = 0%
    assert "0" in keep_rates
    assert keep_rates["0"] == 0.0

    # At depth 1: 0 keeps, 1 total hand = 0%
    assert "1" in keep_rates
    assert keep_rates["1"] == 0.0

    # At depth 2: 1 keep, 1 total hand = 100%
    assert "2" in keep_rates
    assert keep_rates["2"] == 100.0


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
