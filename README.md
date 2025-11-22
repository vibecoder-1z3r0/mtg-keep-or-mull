# MTG Keep or Mull

A mulligan practice simulator for Magic: The Gathering that helps players train their mulligan decisions and track statistics.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: VCL](https://img.shields.io/badge/License-VCL%20v0.1-purple.svg)](LICENSE-VCL)

## ⚠️ Important Notices

### Fan Content Policy

**MTG Keep or Mull** is unofficial Fan Content permitted under the [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy). Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.

### AI Attribution

**AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0**

This work was primarily AI-generated. AI was prompted for its contributions, or AI assistance was enabled. AI-generated content was reviewed and approved. The following model(s) or application(s) were used: Claude Code Web [Sonnet 4.5].

**Attribution URL:** https://aiattribution.github.io/statements/AIA-PAI-Hin-R-?model=Claude%20Code%20Web%20%5BSonnet%204.5%5D-v1.0

## 🎯 Project Status

**Current Phase:** Business Logic Layer (MVP)

This repository contains the core business logic for mulligan simulation. Future sessions will add:
- CLI interface
- REST API
- Database persistence (SQLite/PostgreSQL)
- Text User Interface (TUI)
- Sideboarding support (Games 2-3)

## 🃏 Features

### London Mulligan Rules (2019+)

Implements current competitive mulligan rules:
1. Always draw 7 cards
2. Decide to keep or mulligan
3. If mulligan: shuffle hand back, draw 7 again
4. When keeping: put N cards on bottom (where N = mulligan count)
5. Final hand size: 7 - N cards

### Core Components

- **Card**: Represents individual Magic cards
- **Hand**: Manages hand composition with normalization for statistics
- **Deck**: MTGO-format deck list parsing with quantity expansion
- **MulliganSimulator**: Orchestrates the London Mulligan process
- **DataStore**: Abstract storage interface with mock implementation
- **Pydantic Models**: Validated data structures for decisions and statistics

### Hand Normalization

Hands are normalized for statistical analysis:
- **Display Order**: Shown to user in randomized draw order (prevents bias)
- **Normalized Signature**: Alphabetically sorted card names for statistics
- Identical hand compositions produce identical signatures regardless of order

**Example:**
```
Display:    [Island] [Brainstorm] [Counterspell] [Island] [Mental Note]
Normalized: Brainstorm,Counterspell,Island,Island,Mental Note
```

## 🛠️ Tech Stack

**Language:** Python 3.10-3.13

**Core Dependencies:**
- `pydantic>=2.0.0` - Data validation and models

**Development Tools:**
- `pytest` + `pytest-cov` - Testing framework with coverage
- `black` - Code formatter
- `flake8` + `pylint` - Linters
- `mypy` - Static type checking
- `pre-commit` - Git hooks for code quality

**Development Approach:**
- Test-Driven Development (TDD)
- Red-Green-Refactor cycle
- 80%+ code coverage target
- Type hints throughout

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/vibecoder-1z3r0/mtg-keep-or-mull.git
cd mtg-keep-or-mull

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🧪 Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_card.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html
```

**Current Test Coverage:**
- Card: 100%
- Hand: 95.45%
- Deck: 93.75%
- MockDataStore: 97.92%
- MulliganSimulator: 85.19%

## 📚 Usage Example

```python
from mtg_keep_or_mull.deck import Deck
from mtg_keep_or_mull.mulligan import MulliganSimulator
from mtg_keep_or_mull.datastore import MockDataStore

# Load a deck
deck = Deck.from_file("tests/fixtures/decks/mono_u_terror.txt")

# Create simulator
sim = MulliganSimulator(deck, on_play=True)

# Draw opening hand
hand = sim.start_game()
print(f"Opening hand ({hand.size()} cards):")
for card in hand.get_cards():
    print(f"  - {card.name}")

# Mulligan
if should_mulligan(hand):  # Your decision logic
    hand = sim.mulligan()
    print(f"After mulligan ({hand.size()} cards)")

# Keep and bottom cards
if sim.get_mulligan_count() > 0:
    cards_to_bottom = select_cards_to_bottom(hand, sim.get_mulligan_count())
    final_hand = sim.keep(cards_to_bottom)
else:
    final_hand = sim.keep()

print(f"Final hand: {final_hand.size()} cards")
print(f"Hand signature: {final_hand.get_signature()}")
```

## 🗂️ Project Structure

```
mtg-keep-or-mull/
├── src/
│   └── mtg_keep_or_mull/
│       ├── __init__.py
│       ├── card.py           # Card representation
│       ├── hand.py           # Hand management
│       ├── deck.py           # Deck parsing and manipulation
│       ├── mulligan.py       # Mulligan simulator
│       ├── datastore.py      # Storage interface + MockDataStore
│       └── models.py         # Pydantic data models
├── tests/
│   ├── fixtures/
│   │   └── decks/           # Real tournament deck lists
│   ├── test_card.py
│   ├── test_hand.py
│   ├── test_deck.py
│   ├── test_mulligan_simulator.py
│   └── test_mock_datastore.py
├── pyproject.toml           # Project configuration
├── LICENSE                  # MIT License
├── LICENSE-VCL              # VCL-Experimental v0.1
├── CLAUDE.md               # AI context document
├── REQUIREMENTS.md          # Detailed requirements
└── README.md               # This file
```

## 🤝 Contributing

This project follows Test-Driven Development practices:

1. **Write tests first** (Red phase)
2. **Implement minimal code** to pass (Green phase)
3. **Refactor** while keeping tests passing

**Code Quality Requirements:**
- All tests must pass
- 80%+ code coverage
- Type hints required (`mypy` checks)
- Formatted with `black`
- Passes `flake8` and `pylint`
- Pre-commit hooks must pass

**AI Contributions:**
All AI-assisted contributions must include proper AIA attribution in commit messages.

## 📄 Licenses

This project uses **dual licensing**:

### MIT License

Copyright (c) 2025 Vibe-Coder 1.z3r0

See [LICENSE](LICENSE) file for full MIT License text.

### VCL-Experimental v0.1 (Vibe-Coder License)

A novelty license for fun and cultural purposes (**NO LEGAL BEARING**).

Key principle: *"All use, modification, and distribution must serve the vibe."*

See [LICENSE-VCL](LICENSE-VCL) file for full VCL text.

**Source:** https://github.com/tyraziel/vibe-coder-license/

## 🔗 Links

- **Repository:** https://github.com/vibecoder-1z3r0/mtg-keep-or-mull
- **Issues:** https://github.com/vibecoder-1z3r0/mtg-keep-or-mull/issues
- **Fan Content Policy:** https://company.wizards.com/en/legal/fancontentpolicy
- **AIA Attribution:** https://aiattribution.github.io/

## ✨ Acknowledgments

- **Wizards of the Coast** - Magic: The Gathering IP
- **Anthropic** - Claude Code Web (Sonnet 4.5)
- **Vibe-Coder Community** - VCL-Experimental license
- **Python Community** - Excellent development tools

---

**Co-authored-by:**
- Claude (AI Assistant) <claude@anthropic.com>
- Vibe-Coder 1.z3r0 <vibecoder.1.z3r0@gmail.com>

**AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0**
