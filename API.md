# MTG Keep or Mull - REST API Documentation

## Overview

The MTG Keep or Mull API provides a RESTful interface for practicing mulligan decisions in Magic: The Gathering using the London Mulligan rules.

**Base URL:** `http://localhost:8000`
**API Version:** v1
**OpenAPI Spec:** `http://localhost:8000/openapi.json`
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)
**Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

## Quick Start

### Running the API Server

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
uvicorn mtg_keep_or_mull.api.app:app --reload

# Server will be available at http://localhost:8000
```

### Example Workflow

1. **Upload a deck**
2. **Start a practice session** → Get opening hand
3. **Make decision**: Keep or Mulligan
4. **Record decision** for statistics
5. **View statistics** for hands and decks

## API Endpoints

### Root & Health

#### `GET /`
Returns API metadata and links.

**Response:**
```json
{
  "name": "MTG Keep or Mull API",
  "version": "0.1.0",
  "description": "Mulligan practice simulator for Magic: The Gathering",
  "docs_url": "/docs",
  "openapi_url": "/openapi.json"
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Deck Management

### `POST /api/v1/decks`
Upload a new deck in MTGO format.

**Request Body:**
```json
{
  "deck_text": "4 Lightning Bolt\n20 Mountain\n\nSIDEBOARD:\n3 Pyroblast",
  "deck_name": "Red Deck Wins"
}
```

**Response (201 Created):**
```json
{
  "deck_id": "Red Deck Wins_20251122123456",
  "deck_name": "Red Deck Wins",
  "main_deck_size": 24,
  "sideboard_size": 3,
  "created_at": "2025-11-22T12:34:56"
}
```

### `GET /api/v1/decks`
List all uploaded decks.

**Response (200 OK):**
```json
{
  "decks": [
    {
      "deck_id": "Red Deck Wins_20251122123456",
      "deck_name": "Red Deck Wins",
      "main_deck_size": 24,
      "sideboard_size": 3,
      "created_at": "2025-11-22T12:34:56"
    }
  ],
  "total": 1
}
```

### `GET /api/v1/decks/{deck_id}`
Get details about a specific deck.

**Response (200 OK):**
```json
{
  "deck_id": "Red Deck Wins_20251122123456",
  "deck_name": "Red Deck Wins",
  "main_deck_size": 24,
  "sideboard_size": 3,
  "created_at": "2025-11-22T12:34:56"
}
```

**Errors:**
- `404 Not Found` - Deck doesn't exist

### `DELETE /api/v1/decks/{deck_id}`
Delete a deck.

**Response:**
- `501 Not Implemented` - Delete functionality not yet implemented
- `404 Not Found` - Deck doesn't exist

---

## Practice Sessions

### `POST /api/v1/sessions`
Start a new mulligan practice session.

**Request Body:**
```json
{
  "deck_id": "Red Deck Wins_20251122123456",
  "on_play": true
}
```

**Response (201 Created):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "Red Deck Wins_20251122123456",
  "on_play": true,
  "mulligan_count": 0,
  "current_hand": {
    "cards": [
      {"name": "Lightning Bolt"},
      {"name": "Mountain"},
      {"name": "Mountain"},
      {"name": "Lightning Bolt"},
      {"name": "Mountain"},
      {"name": "Lightning Bolt"},
      {"name": "Mountain"}
    ],
    "size": 7,
    "signature": "Lightning Bolt,Lightning Bolt,Lightning Bolt,Mountain,Mountain,Mountain,Mountain"
  }
}
```

**Errors:**
- `404 Not Found` - Deck doesn't exist

### `GET /api/v1/sessions/{session_id}`
Get the current state of a practice session.

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "Red Deck Wins_20251122123456",
  "on_play": true,
  "mulligan_count": 0,
  "current_hand": {
    "cards": [...],
    "size": 7,
    "signature": "..."
  }
}
```

**Errors:**
- `404 Not Found` - Session doesn't exist

### `POST /api/v1/sessions/{session_id}/mulligan`
Mulligan the current hand (shuffle back, draw 7 again).

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "Red Deck Wins_20251122123456",
  "on_play": true,
  "mulligan_count": 1,
  "current_hand": {
    "cards": [...],
    "size": 7,
    "signature": "..."
  }
}
```

**Errors:**
- `404 Not Found` - Session doesn't exist

### `POST /api/v1/sessions/{session_id}/keep`
Keep the current hand and bottom N cards (where N = mulligan count).

**Request Body:**
```json
{
  "cards_to_bottom": ["Lightning Bolt"]
}
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "Red Deck Wins_20251122123456",
  "on_play": true,
  "mulligan_count": 1,
  "current_hand": {
    "cards": [...],
    "size": 6,
    "signature": "..."
  }
}
```

**Errors:**
- `404 Not Found` - Session doesn't exist
- `400 Bad Request` - Wrong number of cards to bottom or card not in hand

### `POST /api/v1/sessions/{session_id}/decision`
Record a mulligan decision for statistics.

**Request Body:**
```json
{
  "decision": "keep"
}
```

Valid decisions: `"keep"` or `"mull"`

**Response (201 Created):**
```json
{
  "message": "Decision recorded successfully"
}
```

**Errors:**
- `404 Not Found` - Session doesn't exist
- `422 Validation Error` - Invalid decision value

### `DELETE /api/v1/sessions/{session_id}`
End a practice session and clean up resources.

**Response:**
- `204 No Content` - Session successfully deleted

**Errors:**
- `404 Not Found` - Session doesn't exist

---

## Statistics

### `GET /api/v1/statistics/hands`
Get statistics for all recorded hand compositions.

**Response (200 OK):**
```json
{
  "hands": [
    {
      "hand_signature": "Lightning Bolt,Lightning Bolt,Mountain,Mountain,Mountain,Mountain,Mountain",
      "times_kept": 8,
      "times_mulled": 2,
      "keep_percentage": 80.0,
      "total_decisions": 10
    }
  ],
  "total": 1
}
```

### `GET /api/v1/statistics/hands/{signature}`
Get statistics for a specific hand composition.

**Example:** `GET /api/v1/statistics/hands/Lightning Bolt,Mountain,Mountain,Mountain,Mountain,Mountain,Mountain`

**Response (200 OK):**
```json
{
  "hand_signature": "Lightning Bolt,Mountain,Mountain,Mountain,Mountain,Mountain,Mountain",
  "times_kept": 5,
  "times_mulled": 1,
  "keep_percentage": 83.33,
  "total_decisions": 6
}
```

**Errors:**
- `404 Not Found` - No statistics found for this hand

### `GET /api/v1/statistics/decks/{deck_id}`
Get aggregated statistics for a specific deck.

**Response (200 OK):**
```json
{
  "deck_id": "Red Deck Wins_20251122123456",
  "total_games": 42,
  "mulligan_distribution": {
    "0": 25,
    "1": 12,
    "2": 4,
    "3": 1
  },
  "average_mulligan_count": 0.64,
  "hands_kept_at_7": 25,
  "hands_kept_at_6": 12,
  "hands_kept_at_5": 4
}
```

**Errors:**
- `404 Not Found` - Deck doesn't exist or no statistics available

---

## Example Usage with cURL

### 1. Upload a deck
```bash
curl -X POST "http://localhost:8000/api/v1/decks" \
  -H "Content-Type: application/json" \
  -d '{
    "deck_text": "4 Brainstorm\n4 Counterspell\n20 Island",
    "deck_name": "Mono U Terror"
  }'
```

### 2. Start a session
```bash
curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "deck_id": "Mono U Terror_20251122123456",
    "on_play": true
  }'
```

### 3. Record a decision
```bash
curl -X POST "http://localhost:8000/api/v1/sessions/{session_id}/decision" \
  -H "Content-Type: application/json" \
  -d '{"decision": "keep"}'
```

### 4. Get statistics
```bash
curl "http://localhost:8000/api/v1/statistics/decks/Mono%20U%20Terror_20251122123456"
```

---

## Example Usage with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Upload deck
deck_response = requests.post(
    f"{BASE_URL}/api/v1/decks",
    json={
        "deck_text": "4 Brainstorm\n4 Counterspell\n20 Island",
        "deck_name": "Mono U Terror"
    }
)
deck_id = deck_response.json()["deck_id"]

# Start session
session_response = requests.post(
    f"{BASE_URL}/api/v1/sessions",
    json={"deck_id": deck_id, "on_play": True}
)
session_data = session_response.json()
session_id = session_data["session_id"]

# View hand
print(f"Opening hand: {session_data['current_hand']['cards']}")

# Make decision
decision = "keep"  # or "mull"
requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/decision",
    json={"decision": decision}
)

# If mulliganing
if decision == "mull":
    mull_response = requests.post(f"{BASE_URL}/api/v1/sessions/{session_id}/mulligan")
    print(f"New hand: {mull_response.json()['current_hand']['cards']}")

# If keeping after mulligan
if session_data["mulligan_count"] > 0:
    cards_to_bottom = [session_data["current_hand"]["cards"][0]["name"]]
    keep_response = requests.post(
        f"{BASE_URL}/api/v1/sessions/{session_id}/keep",
        json={"cards_to_bottom": cards_to_bottom}
    )
    print(f"Final hand: {keep_response.json()['current_hand']['cards']}")

# Get statistics
stats_response = requests.get(f"{BASE_URL}/api/v1/statistics/decks/{deck_id}")
print(f"Deck stats: {stats_response.json()}")

# End session
requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}")
```

---

## OpenAPI Specification

The API automatically generates an OpenAPI 3.x specification available at:

- **JSON:** `http://localhost:8000/openapi.json`
- **Interactive Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative Docs (ReDoc):** `http://localhost:8000/redoc`

The specification is validated using `openapi-spec-validator` in our test suite.

---

## Development

### Running Tests

```bash
# Run all API tests
pytest tests/test_api*.py -v

# Run with coverage
pytest --cov=mtg_keep_or_mull --cov-report=term-missing

# Run OpenAPI spec validation tests
pytest tests/test_api_app.py::test_openapi_spec_validity -v
```

### Test Coverage

Current API test coverage: **96.22%** (well above 80% target)

- `test_api_app.py` - OpenAPI spec validation & basic endpoints
- `test_api_decks.py` - Deck management endpoints
- `test_api_sessions.py` - Practice session endpoints
- `test_api_statistics.py` - Statistics endpoints

---

## Architecture

### Session Management

- **In-Memory Storage:** Sessions are stored in-memory (MVP)
- **UUID-based IDs:** Each session gets a unique UUID
- **Stateful:** Sessions maintain mulligan count and current hand state

### Data Storage

- **MockDataStore:** In-memory implementation for MVP
- **Protocol-based:** Easily swappable with database implementation
- **Future:** SQLite/PostgreSQL backend planned

### Models

All request/response models use Pydantic for:
- Automatic validation
- Type safety
- OpenAPI schema generation
- JSON serialization

---

## Fan Content Notice

**MTG Keep or Mull** is unofficial Fan Content permitted under the [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy). Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.

---

## License

Dual-licensed under:
- **MIT License** - See [LICENSE](LICENSE)
- **VCL-Experimental v0.1** - See [LICENSE-VCL](LICENSE-VCL)

---

**AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0**
