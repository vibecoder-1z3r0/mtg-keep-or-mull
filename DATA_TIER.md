# Data Tier Implementation

## Overview

The MTG Keep or Mull application now includes a comprehensive data persistence layer with multiple storage backend options. The data tier provides flexible storage implementations through a protocol-based interface, allowing you to choose the best storage solution for your needs.

## Available Storage Backends

### 1. MockDataStore (In-Memory)
**Use Case:** Testing, development, ephemeral sessions

- **Type:** In-memory storage
- **Persistence:** No (data lost when process ends)
- **Dependencies:** None (built-in)
- **Best For:** Unit tests, development, demos

```python
from mtg_keep_or_mull.datastore import MockDataStore

datastore = MockDataStore()
```

### 2. JSONDataStore (File-Based)
**Use Case:** Simple persistence, human-readable data, local development

- **Type:** JSON file storage
- **Persistence:** Yes (files on disk)
- **Dependencies:** None (built-in)
- **Best For:** Simple deployments, local use, debugging

```python
from mtg_keep_or_mull.datastore import JSONDataStore
from pathlib import Path

# Default: ./data directory
datastore = JSONDataStore()

# Custom path
datastore = JSONDataStore(base_path=Path("/path/to/data"))
```

**File Structure:**
```
data/
  decks/
    mono_u_terror.json         # Deck information
    elves.json
  decisions/
    mono_u_terror.json         # Hand decisions for deck
    elves.json
```

### 3. SQLiteDataStore (Embedded Database)
**Use Case:** Production-ready, single-user, local deployment

- **Type:** SQLite embedded database
- **Persistence:** Yes (SQLite .db file)
- **Dependencies:** None (SQLite built into Python)
- **Best For:** Desktop apps, single-user deployments, mobile apps

```python
from mtg_keep_or_mull.datastore import SQLiteDataStore
from pathlib import Path

# Default: ./data/mtg_keep_or_mull.db
datastore = SQLiteDataStore()

# Custom database path
datastore = SQLiteDataStore(db_path=Path("/path/to/database.db"))
```

**Features:**
- ACID transactions
- Fast queries with indexes
- No server required
- Portable single-file database

### 4. PostgreSQLDataStore (Server Database)
**Use Case:** Production deployment, multi-user, enterprise

- **Type:** PostgreSQL client-server database
- **Persistence:** Yes (PostgreSQL server)
- **Dependencies:** `psycopg2-binary>=2.9.0`
- **Best For:** Web applications, multi-user systems, production deployments

**Installation:**
```bash
pip install mtg-keep-or-mull[postgres]
```

**Usage:**
```python
from mtg_keep_or_mull.datastore import PostgreSQLDataStore

datastore = PostgreSQLDataStore(
    host="localhost",
    port=5432,
    database="mtg_keep_or_mull",
    user="postgres",
    password="your_password"
)
```

**Features:**
- Enterprise-grade reliability
- Advanced query optimization
- Concurrent multi-user access
- Replication and backup support
- JSONB support for efficient document storage

### 5. MariaDBDataStore (MySQL-Compatible)
**Use Case:** Production deployment with MySQL ecosystem

- **Type:** MariaDB/MySQL client-server database
- **Persistence:** Yes (MariaDB/MySQL server)
- **Dependencies:** `mysql-connector-python>=8.0.0`
- **Best For:** MySQL ecosystem integration, shared hosting

**Installation:**
```bash
pip install mtg-keep-or-mull[mysql]
```

**Usage:**
```python
from mtg_keep_or_mull.datastore import MariaDBDataStore

datastore = MariaDBDataStore(
    host="localhost",
    port=3306,
    database="mtg_keep_or_mull",
    user="root",
    password="your_password"
)
```

**Features:**
- MySQL ecosystem compatibility
- Wide hosting availability
- Good performance for read-heavy workloads
- Familiar to many developers

## Database Schema

All SQL-based datastores (SQLite, PostgreSQL, MariaDB) share a common schema:

### Decks Table
```sql
CREATE TABLE decks (
    deck_id VARCHAR(255) PRIMARY KEY,
    deck_name VARCHAR(255) NOT NULL DEFAULT '',
    main_deck TEXT NOT NULL,        -- JSON array of card names
    sideboard TEXT NOT NULL,        -- JSON array of card names
    total_games INTEGER NOT NULL DEFAULT 0
);
```

### Hand Decisions Table
```sql
CREATE TABLE hand_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- or SERIAL/AUTO_INCREMENT
    deck_id VARCHAR(255) NOT NULL,
    hand_signature TEXT NOT NULL,
    hand_display TEXT NOT NULL,     -- JSON array in display order
    mulligan_count INTEGER NOT NULL,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'mull')),
    lands_in_hand INTEGER NOT NULL,
    on_play BOOLEAN NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);

CREATE INDEX idx_hand_decisions_deck_id ON hand_decisions(deck_id);
CREATE INDEX idx_hand_decisions_signature ON hand_decisions(hand_signature);
CREATE INDEX idx_hand_decisions_timestamp ON hand_decisions(timestamp);
```

## DataStore Protocol

All storage implementations conform to the `DataStore` protocol, ensuring interface compatibility:

```python
class DataStore(Protocol):
    def save_hand_decision(self, decision: HandDecisionData) -> None: ...
    def get_hand_statistics(self, hand_signature: str) -> Optional[HandStats]: ...
    def get_all_hand_statistics(self) -> List[HandStats]: ...
    def save_deck(self, deck: DeckData) -> str: ...
    def load_deck(self, deck_id: str) -> Optional[DeckData]: ...
    def list_decks(self) -> List[str]: ...
    def get_decisions_for_deck(self, deck_id: str) -> List[HandDecisionData]: ...
```

## Choosing a Storage Backend

| Backend | Persistence | Multi-User | Setup Complexity | Performance | Best Use Case |
|---------|-------------|------------|------------------|-------------|---------------|
| **MockDataStore** | ❌ No | ❌ No | ⭐ Trivial | ⚡ Fastest | Testing |
| **JSONDataStore** | ✅ Yes | ❌ No | ⭐ Trivial | 🐢 Slow | Local development |
| **SQLiteDataStore** | ✅ Yes | ⚠️ Limited | ⭐ Trivial | ⚡ Fast | Desktop apps |
| **PostgreSQLDataStore** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Complex | ⚡⚡ Very Fast | Production web |
| **MariaDBDataStore** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Complex | ⚡ Fast | MySQL hosting |

## Installation Guide

### Basic Installation (JSON + SQLite)
```bash
pip install mtg-keep-or-mull
```

### With PostgreSQL Support
```bash
pip install mtg-keep-or-mull[postgres]
```

### With MySQL/MariaDB Support
```bash
pip install mtg-keep-or-mull[mysql]
```

### With All Database Backends
```bash
pip install mtg-keep-or-mull[databases]
```

### Development Installation
```bash
pip install -e ".[dev,databases]"
```

## Migration Between Backends

Since all datastores implement the same protocol, you can migrate data by:

1. Read from source datastore
2. Write to destination datastore

```python
from mtg_keep_or_mull.datastore import JSONDataStore, SQLiteDataStore

# Source: JSON files
source = JSONDataStore()

# Destination: SQLite database
dest = SQLiteDataStore()

# Migrate decks
for deck_id in source.list_decks():
    deck = source.load_deck(deck_id)
    if deck:
        dest.save_deck(deck)

        # Migrate decisions for this deck
        decisions = source.get_decisions_for_deck(deck_id)
        for decision in decisions:
            dest.save_hand_decision(decision)

print("Migration complete!")
```

## Testing

The project includes comprehensive tests for each datastore:

- `tests/test_mock_datastore.py` - MockDataStore tests
- `tests/test_json_datastore.py` - JSONDataStore tests
- `tests/test_sqlite_datastore.py` - SQLiteDataStore tests

PostgreSQL and MariaDB tests require running database servers and are considered integration tests.

## Performance Considerations

### MockDataStore
- **Reads:** O(n) for statistics, O(1) for deck lookups
- **Writes:** O(1) append operations
- **Memory:** All data in RAM

### JSONDataStore
- **Reads:** O(n) - must parse entire JSON file
- **Writes:** O(n) - must rewrite entire file
- **Disk:** Human-readable, easy to inspect

### SQLiteDataStore
- **Reads:** O(log n) with indexes
- **Writes:** O(log n) with B-tree indexes
- **Disk:** Efficient binary format

### PostgreSQL/MariaDB
- **Reads:** O(log n) with indexes, supports query optimization
- **Writes:** O(log n), supports concurrent writes
- **Network:** Add network latency considerations

## Future Enhancements

- Connection pooling for SQL databases
- Caching layer for frequently accessed data
- Async database operations
- Database migration scripts
- Read replicas for scaling
- Sharding for massive datasets

---

**AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0**
