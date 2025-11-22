# MTG Keep or Mull - Business Logic Requirements

**Version:** 1.0 MVP (Business Logic Layer)
**Last Updated:** 2025-11-22
**Session:** claude/resume-session-01De2wdbspSyhjECCPBBvpna

---

## Project Overview

MTG mulligan practice simulator that helps players train their mulligan decisions and track statistics.

**MVP Scope:** Business logic layer only (core Python classes/modules). CLI, API, DB, and TUI will be built in future sessions.

---

## Mulligan Rules

**London Mulligan (Current Competitive Standard - 2019+):**

1. Draw 7 cards (always draw 7, regardless of mulligan count)
2. Decide: Keep or Mulligan
3. If mulligan: Shuffle hand back into deck, draw 7 again, increment mulligan counter
4. Repeat until player decides to keep
5. **When keeping:** Player selects N cards to put on bottom of library (where N = mulligan count)
6. **Final hand size:** 7 - N cards

**Example Flow:**
```
Draw 7 → Mulligan → Draw 7 → Mulligan → Draw 7 → Keep → Bottom 2 cards → 5 cards in hand
```

---

## Core Components

### 1. Card Representation

**Card Class:**
- Represents a single Magic card
- Properties:
  - `name: str` - Card name (e.g., "Lightning Bolt")
  - `card_type: str` - Type (e.g., "Instant", "Creature", "Land")
  - `mana_cost: str` - Mana cost (e.g., "R", "{2}{R}")
  - `cmc: int` - Converted mana cost / mana value

**Future Enhancement:** Add more properties (color, rarity, etc.) as needed

### 2. Deck Management

**Deck Class:**
- Load deck from MTGO-format text file
- Parse deck list format: `<quantity> <card name>` per line
- Parse sideboard (store but don't use in MVP)
- Store main deck as list of Card objects (quantity expanded)
- Shuffle deck (randomize order)
- Draw N cards from top
- Return cards to deck

**Deck List Format (MTGO-style):**
```
4 Lightning Bolt
3 Monastery Swiftspear
20 Mountain

SIDEBOARD:
3 Pyroblast
2 Smash to Smithereens
```

**Parsing Behavior:**
- Lines before "SIDEBOARD:" → main deck (expanded by quantity)
- Lines after "SIDEBOARD:" → sideboard (stored, not used in MVP)
- Empty lines and "SIDEBOARD:" line are ignored
- Each card is expanded: `4 Lightning Bolt` → 4 Card objects

*(Note: No validation of card names against MTG database in MVP - deferred to future session)*

**Methods:**
- `load_from_file(filepath: str) -> None` - Parse and load deck
- `shuffle() -> None` - Randomize deck order
- `draw(n: int) -> List[Card]` - Draw N cards from top
- `return_cards(cards: List[Card]) -> None` - Return cards to deck
- `put_on_bottom(cards: List[Card]) -> None` - Put cards on bottom
- `size() -> int` - Current deck size

### 3. Hand Representation

**Hand Class:**
- Represents current cards in hand
- Track which cards are in hand
- Analyze hand composition

**Methods:**
- `add_card(card: Card) -> None`
- `remove_card(card: Card) -> None`
- `count_lands() -> int` - Count land cards
- `get_mana_curve() -> Dict[int, int]` - CMC distribution
- `size() -> int` - Cards in hand

### 4. Mulligan Simulator

**MulliganSimulator Class:**
- Orchestrate mulligan process
- Track mulligan count
- Handle London Mulligan rules
- Record decisions for statistics

**Properties:**
- `deck: Deck`
- `current_hand: Hand`
- `mulligan_count: int`
- `on_play: bool` - True if on the play, False if on the draw

**Methods:**
- `start_game(on_play: bool) -> Hand` - Begin new game, draw opening 7
- `mulligan() -> Hand` - Shuffle back, draw 7, increment counter
- `keep(cards_to_bottom: List[Card]) -> Hand` - Finalize hand, bottom N cards
- `get_mulligan_count() -> int`

### 5. Statistics Tracking

**StatisticsTracker Class:**
- Track mulligan decisions per deck
- Store statistics to JSON file
- Aggregate data

**Data to Track (MVP):**
- Deck identifier (hash or filename)
- Total games played
- Mulligan decisions:
  - Kept at 7 (no mulligan)
  - Kept at 6 (1 mulligan)
  - Kept at 5 (2 mulligans)
  - etc.
- Per-hand data:
  - Hand size when kept
  - Number of lands in hand
  - On play or on draw
  - Timestamp

**Storage Format (JSON):**
```json
{
  "deck_id": "deck_12345.txt",
  "total_games": 42,
  "mulligan_distribution": {
    "0": 25,
    "1": 12,
    "2": 4,
    "3": 1
  },
  "hands": [
    {
      "mulligan_count": 1,
      "final_hand_size": 6,
      "lands_in_hand": 3,
      "on_play": true,
      "timestamp": "2025-11-22T10:30:00"
    }
  ]
}
```

**Methods:**
- `record_hand(mulligan_count, hand, on_play) -> None`
- `save_to_file(filepath: str) -> None`
- `load_from_file(filepath: str) -> None`
- `get_summary() -> Dict` - Aggregate statistics

---

## Development Approach

### Test-Driven Development (TDD)

**Red-Green-Refactor Cycle:**
1. ✍️ Write failing test (Red)
2. ✅ Implement minimal code to pass (Green)
3. 🔧 Refactor while keeping tests passing

**Coverage Target:** 80% minimum code coverage

**Testing Tools:**
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting

### Code Quality Tools

- **Formatting:** `black` (auto-formatter)
- **Linting:** `flake8` + `pylint`
- **Type Checking:** `mypy` (static type analysis)
- **Pre-commit Hooks:** Auto-run checks before commits

---

## Project Structure

```
mtg-keep-or-mull/
├── src/
│   └── mtg_keep_or_mull/
│       ├── __init__.py
│       ├── card.py              # Card class
│       ├── deck.py              # Deck class
│       ├── hand.py              # Hand class
│       ├── mulligan.py          # MulliganSimulator class
│       └── statistics.py        # StatisticsTracker class
├── tests/
│   ├── __init__.py
│   ├── test_card.py
│   ├── test_deck.py
│   ├── test_hand.py
│   ├── test_mulligan.py
│   └── test_statistics.py
├── pyproject.toml               # Project config (PEP 621)
├── .pre-commit-config.yaml      # Pre-commit hooks
├── LICENSE                      # MIT License
├── LICENSE-VCL                  # VCL-Experimental v0.1
├── CLAUDE.md                    # AI context document
├── REQUIREMENTS.md              # This file
└── README.md                    # Project documentation
```

---

## Out of Scope for MVP

These features are deferred to future sessions:

- ❌ CLI interface (future: CLI session)
- ❌ REST API (future: API session)
- ❌ Database backend (future: DB session)
- ❌ TUI (Text User Interface) (future: TUI session)
- ❌ Sideboarding / Game 2-3 simulation (future: v2.0)
- ❌ AI-powered keep/mulligan recommendations (future: v3.0+)
- ❌ Scryfall API integration for card data (future enhancement)

---

## Success Criteria

MVP is complete when:

- ✅ All 5 core classes implemented with TDD
- ✅ 80%+ test coverage achieved
- ✅ All linting/type-checking passes
- ✅ Can load a 60-card deck from text file
- ✅ Can simulate London Mulligan process
- ✅ Can track and save statistics to JSON
- ✅ Pre-commit hooks configured and working
- ✅ README with proper attributions created

---

## Next Steps

1. Set up Python project structure (`pyproject.toml`, `src/`, `tests/`)
2. Configure testing framework (pytest + coverage)
3. Configure linting tools (black, flake8, pylint, mypy)
4. Set up pre-commit hooks
5. **Begin TDD implementation:**
   - Start with `Card` class (simplest)
   - Then `Hand` class
   - Then `Deck` class
   - Then `MulliganSimulator` class
   - Finally `StatisticsTracker` class

---

*AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0*
