"""Tests for the main FastAPI application."""

import json

import pytest
from fastapi.testclient import TestClient
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from mtg_keep_or_mull.api.app import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API.

    Returns:
        TestClient instance
    """
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "MTG Keep or Mull API"
    assert data["version"] == "0.1.0"
    assert "docs_url" in data
    assert "openapi_url" in data
    assert "fan_content_notice" in data


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_openapi_spec_generation(client: TestClient) -> None:
    """Test that the OpenAPI spec can be generated."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec

    # Validate basic structure
    assert spec["info"]["title"] == "MTG Keep or Mull API"
    assert spec["info"]["version"] == "0.1.0"


def test_openapi_spec_validity(client: TestClient) -> None:
    """Test that the generated OpenAPI spec is valid."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()

    # Validate the spec using openapi-spec-validator
    # This will raise an exception if the spec is invalid
    try:
        validate(spec)
    except Exception as e:
        pytest.fail(f"OpenAPI spec validation failed: {e}")


def test_openapi_spec_contains_expected_endpoints(client: TestClient) -> None:
    """Test that the OpenAPI spec contains all expected endpoints."""
    response = client.get("/openapi.json")
    spec = response.json()

    paths = spec["paths"]

    # Check for deck endpoints
    assert "/api/v1/decks" in paths
    assert "/api/v1/decks/{deck_id}" in paths

    # Check for session endpoints
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}" in paths
    assert "/api/v1/sessions/{session_id}/mulligan" in paths
    assert "/api/v1/sessions/{session_id}/keep" in paths
    assert "/api/v1/sessions/{session_id}/decision" in paths

    # Check for statistics endpoints
    assert "/api/v1/statistics/hands" in paths
    assert "/api/v1/statistics/hands/{signature}" in paths
    assert "/api/v1/statistics/decks/{deck_id}" in paths


def test_openapi_spec_contains_expected_methods(client: TestClient) -> None:
    """Test that endpoints have the expected HTTP methods."""
    response = client.get("/openapi.json")
    spec = response.json()

    paths = spec["paths"]

    # Deck endpoints
    assert "post" in paths["/api/v1/decks"]
    assert "get" in paths["/api/v1/decks"]
    assert "get" in paths["/api/v1/decks/{deck_id}"]
    assert "delete" in paths["/api/v1/decks/{deck_id}"]

    # Session endpoints
    assert "post" in paths["/api/v1/sessions"]
    assert "get" in paths["/api/v1/sessions/{session_id}"]
    assert "delete" in paths["/api/v1/sessions/{session_id}"]
    assert "post" in paths["/api/v1/sessions/{session_id}/mulligan"]
    assert "post" in paths["/api/v1/sessions/{session_id}/keep"]
    assert "post" in paths["/api/v1/sessions/{session_id}/decision"]

    # Statistics endpoints
    assert "get" in paths["/api/v1/statistics/hands"]
    assert "get" in paths["/api/v1/statistics/hands/{signature}"]
    assert "get" in paths["/api/v1/statistics/decks/{deck_id}"]


def test_docs_endpoint_accessible(client: TestClient) -> None:
    """Test that the Swagger docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint_accessible(client: TestClient) -> None:
    """Test that the ReDoc docs are accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
