-- Database schema for MTG Keep or Mull
-- Compatible with SQLite, PostgreSQL, and MariaDB/MySQL

-- Decks table stores deck information
CREATE TABLE IF NOT EXISTS decks (
    deck_id VARCHAR(255) PRIMARY KEY,
    deck_name VARCHAR(255) NOT NULL DEFAULT '',
    main_deck TEXT NOT NULL,  -- JSON array of card names
    sideboard TEXT NOT NULL,  -- JSON array of card names
    total_games INTEGER NOT NULL DEFAULT 0
);

-- Hand decisions table stores individual mulligan decisions
CREATE TABLE IF NOT EXISTS hand_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite
    -- For PostgreSQL use: id SERIAL PRIMARY KEY
    -- For MariaDB/MySQL use: id INT PRIMARY KEY AUTO_INCREMENT
    deck_id VARCHAR(255) NOT NULL,
    hand_signature TEXT NOT NULL,
    hand_display TEXT NOT NULL,  -- JSON array of card names in display order
    mulligan_count INTEGER NOT NULL,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'mull')),
    lands_in_hand INTEGER NOT NULL,
    on_play BOOLEAN NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);

-- Index for faster lookups by deck
CREATE INDEX IF NOT EXISTS idx_hand_decisions_deck_id ON hand_decisions(deck_id);

-- Index for faster lookups by hand signature (for statistics)
CREATE INDEX IF NOT EXISTS idx_hand_decisions_signature ON hand_decisions(hand_signature);

-- Index for faster lookups by timestamp (for chronological queries)
CREATE INDEX IF NOT EXISTS idx_hand_decisions_timestamp ON hand_decisions(timestamp);

-- AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
