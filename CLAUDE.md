# Claude Context Document

This file contains important context and configuration for AI assistance on this project.

## Project Information

**Repository:** mtg-keep-or-mull
**Current Branch:** claude/init-new-project-01HYnRdHez57Hsv9XkMhgHob
**Main Branch:** (TBD)

## Licensing

This project uses **DUAL LICENSING**:

### 1. MIT License
- Current LICENSE file contains MIT License
- Copyright (c) 2025 Vibe-Coder 1.z3r0

### 2. VCL-Experimental v0.1 (Vibe-Coder License)
- Source: https://github.com/tyraziel/vibe-coder-license/
- Novelty license for fun and cultural purposes (NO LEGAL BEARING)
- Key principle: "All use, modification, and distribution must serve the vibe"
- **TODO:** Add LICENSE-VCL file to project

## AI Attribution (AIA)

All commits and contributions must include proper AI Attribution:

### Short Form
```
AIA Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
```

### Expanded Form
```
This work was primarily AI-generated. AI was prompted for its contributions,
or AI assistance was enabled. AI-generated content was reviewed and approved.
The following model(s) or application(s) were used: Claude Code Web [Sonnet 4.5].
```

### Reference URL
https://aiattribution.github.io/statements/AIA-PAI-Hin-R-?model=Claude%20Code%20Web%20%5BSonnet%204.5%5D-v1.0

## Git Commit Attribution

All commits should include co-author tags:

```
Co-authored-by: Claude (AI Assistant) <claude@anthropic.com>
Co-authored-by: Vibe-Coder 1.z3r0 <vibecoder.1.z3r0@gmail.com>
```

## Magic: The Gathering Fan Content Policy

This project uses Magic: The Gathering intellectual property and must include the following declaration:

### Required Statement
```
MTG Keep or Mull is unofficial Fan Content permitted under the Fan Content Policy.
Not approved/endorsed by Wizards. Portions of the materials used are property of
Wizards of the Coast. ©Wizards of the Coast LLC.
```

### Policy Details
- **Policy URL:** https://company.wizards.com/en/legal/fancontentpolicy
- This is non-commercial fan content
- Cannot include verbatim copying of WotC IP (e.g., creating counterfeit/proxy cards)
- Cannot use WotC patents, game mechanics, logos, or trademarks without permission
- Must include the required fan content statement in README and documentation

## Project Details

### Purpose
MTG mulligan decision helper - helps players analyze opening hands and make keep/mulligan decisions.

### Tech Stack

**Language:** Python
- **Version Matrix:** 3.10, 3.11, 3.12, 3.13
- Minimum: Python 3.10 (3.9 reached EOL October 2025)
- Maximum: Python 3.13 (3.14 too new for production)

**Development Approach:**
- **Test-Driven Development (TDD)** - Red-Green-Refactor cycle
- **Coverage Target:** 80% minimum code coverage
- Write tests first → Show they fail (Red) → Implement → Fix until passing (Green) → Refactor

**Testing & Quality Tools:**
- **Testing:** `pytest` + `pytest-cov` (coverage reporting)
- **Formatting:** `black` (auto-formatter)
- **Linting:** `flake8` + `pylint`
- **Type Checking:** `mypy` (static type analysis)
- **Pre-commit Hooks:** Auto-run linting/formatting before commits

**License Structure Preference:** (TBD - separate files vs combined)

## Next Steps

1. ✅ ~~Determine project scope and purpose~~ (MTG mulligan helper)
2. ✅ ~~Choose tech stack~~ (Python 3.10-3.13, TDD, pytest, etc.)
3. Define detailed application requirements and features
4. Finalize dual licensing structure (separate LICENSE-MIT and LICENSE-VCL files?)
5. Set up Python project structure (pyproject.toml, src/, tests/)
6. Configure testing and linting tools
7. Add VCL license file
8. Create README with all attributions
9. Begin TDD implementation

---

*Last Updated: 2025-11-22*
*Claude Session: claude/init-new-project-01HYnRdHez57Hsv9XkMhgHob*
