# Feature Roadmap & Design Decisions

This document tracks feature enhancements, open design questions, and future development priorities for MTG Keep or Mull.

**Last Updated:** 2025-11-22

---

## 🚀 Planned Features

### 1. Decision Reasoning Tracking

**Status:** Proposed
**Priority:** High
**Complexity:** Medium

Add optional `reason` field to keep/mulligan decisions to enable pattern analysis and learning.

**Implementation:**
- Add `reason: Optional[str]` to `DecisionRequest` model
- Store in `HandDecisionData`
- Display in statistics views

**Value Proposition:**
- "Most common reasons for mulling 7s"
- "What makes a keepable 6 vs. a mulligan"
- Learning pattern recognition
- Building decision-making intuition

---

### 2. Keep/Mulligan Rate by Mulligan Depth

**Status:** Proposed
**Priority:** High
**Complexity:** Low-Medium

Track and display keep rate statistics segmented by mulligan depth (opening 7, mull to 6, mull to 5, etc.).

**Implementation:**
- Enhance `DeckStatsResponse` with `keep_rate_by_mulligan_count: Dict[int, float]`
- Calculate from existing `HandDecisionData` grouped by `mulligan_count`

**Example Output:**
```json
{
  "keep_rate_by_mulligan_count": {
    "0": 0.65,  // 65% of opening 7s kept
    "1": 0.45,  // 45% of mull-to-6s kept
    "2": 0.85,  // 85% of mull-to-5s kept (desperation keeps!)
    "3": 0.95   // 95% of mull-to-4s kept
  }
}
```

**Value Proposition:**
- Understand mulligan thresholds (when do I get desperate?)
- Compare hand quality expectations at different depths
- Identify if you're too aggressive/conservative at specific depths

---

### 3. Track Cards Bottomed (London Mulligan)

**Status:** Proposed
**Priority:** Medium
**Complexity:** Medium

Record which cards were put on the bottom during London mulligan keep decisions.

**Implementation:**
- Add `cards_bottomed: List[str]` to `HandDecisionData`
- Populate from `KeepHandRequest.cards_to_bottom` when recording decisions
- Add endpoint to retrieve bottoming patterns

**Insights Enabled:**
- "Cards most commonly bottomed" (always bottom expensive creatures?)
- "Kept hands with X cards bottomed"
- "Bottom priority by card type" (lands vs. spells vs. creatures)
- Correlate bottomed cards with hand composition

**Example Analysis:**
> "When keeping a mull-to-5, players bottom big threats 78% of the time and keep interaction/cantrips."

---

### 4. Decision History Endpoint

**Status:** Proposed
**Priority:** High
**Complexity:** Medium

Create endpoint(s) to retrieve chronological list of all decision events with full hand details.

**Missing Endpoints:**
```
GET /api/v1/statistics/decisions
GET /api/v1/statistics/decisions?deck_id={deck_id}
GET /api/v1/statistics/decisions?session_id={session_id}
GET /api/v1/sessions/{session_id}/history
```

**Response Schema:**
```json
{
  "decisions": [
    {
      "decision_id": "uuid",
      "timestamp": "2025-11-22T04:36:45",
      "session_id": "c5932a97...",
      "deck_id": "Mono-U Terror_20251122043633",
      "mulligan_count": 0,
      "hand_signature": "Consider,Cryptic Serpent,...",
      "hand_display": ["Island", "Consider", "Cryptic Serpent", ...],
      "decision": "mull",
      "reason": "Only 1 land, no action",  // if tracking reasons
      "cards_bottomed": null,  // only for "keep" decisions
      "on_play": true,
      "lands_in_hand": 1
    },
    {
      "decision_id": "uuid",
      "timestamp": "2025-11-22T04:37:12",
      "mulligan_count": 2,
      "hand_display": ["Mental Note", "Island", "Island", ...],
      "decision": "keep",
      "cards_bottomed": ["Cryptic Serpent", "Tolarian Terror"],
      "reason": "2 lands with cantrip"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

**Value Proposition:**
- Review past decisions
- Learn from patterns over time
- Export decision data for external analysis
- Session replay/review functionality

**Current State:**
- ✓ `/sessions/{id}/decision` - Records decisions to datastore
- ✓ `/statistics/hands` - Aggregated stats per unique hand
- ✓ `/statistics/decks/{id}` - Aggregated deck-level stats
- ✗ **Missing:** Raw decision history retrieval

---

## 🤔 Open Design Questions

### On the Play vs. On the Draw Evaluation

**Status:** Design Discussion
**Decision:** Treat as frontend concern
**Date Discussed:** 2025-11-22

**Question:**
Should the system support evaluating the same hand composition in both "on the play" and "on the draw" scenarios?

**Context:**
- Mulligan decisions often differ based on play/draw position
- Users may want to practice/compare both scenarios for the same hand
- Currently each session is locked to `on_play: true` or `on_play: false`

**Options Presented:**

#### Option 1: Keep Current Design (Separate Sessions)
```
✓ Simple and clean API design
✓ Already works with existing implementation
✓ Statistics already filter by on_play flag
✗ Requires running same deck twice
✗ Can't guarantee same hands will appear
✗ Less convenient for comparative analysis
```

#### Option 2: Add "Compare Mode" Endpoint
```
POST /api/v1/sessions/{session_id}/evaluate-both

Returns: Decision prompts for both scenarios
Records: Two decisions with different on_play values
```

```
✓ Explicit comparison functionality
✓ Backend handles the logic
✗ More complex API surface
✗ Session state becomes more complex
```

#### Option 3: Enhanced Decision Recording
```
POST /api/v1/sessions/{session_id}/decision
{
  "decision_on_play": "keep",
  "decision_on_draw": "mull",
  "reason_on_play": "Fast enough with 7 cards",
  "reason_on_draw": "Want to see more cards since we get 8"
}
```

```
✓ Captures both scenarios in one request
✓ Rich data for analysis
✗ Breaks current API contract
✗ Confusing: which scenario is "active"?
✗ Doesn't match actual game flow (can't be both)
```

#### Option 4: Frontend/UI Handling (RECOMMENDED)
```
Frontend presents the same hand twice in "practice mode"
- Show hand with on_play=true, record decision
- Show same hand with on_play=false, record decision
- API stays simple with boolean on_play field
- Statistics can filter/compare by on_play flag
```

```
✓ API remains simple and clean
✓ Separation of concerns (UI handles UX)
✓ Works with existing API design
✓ Statistics already support filtering by on_play
✓ Flexible - UI can choose when to offer comparison
✗ Requires frontend implementation
✗ Can't guarantee exact same hand in backend (would need seed/replay)
```

**Recommendation:**
Treat as **frontend/UI concern**. The API provides the building blocks (sessions with on_play flag, decision recording, statistics filtering), and the UI orchestrates comparative evaluation when desired.

**Future Enhancement:**
Consider adding a "replay hand" endpoint that accepts a hand signature and creates a new session with that specific hand composition, enabling true comparative evaluation.

---

## 📊 Statistics Enhancements

### Current Statistics Features
- ✓ Hand statistics by signature (times kept/mulled, keep percentage)
- ✓ Deck statistics (total games, mulligan distribution, average mulligan count)
- ✓ Hands kept at each mulligan depth (7, 6, 5)

### Proposed Statistics Enhancements
1. **Keep rate by mulligan depth** (see Feature #2)
2. **Cards bottomed analysis** (see Feature #3)
3. **Decision history** (see Feature #4)
4. **Reason tracking** (see Feature #1)
5. Hand composition analysis (lands in hand distribution)
6. Time-based trends (keep rate over time, learning curve)
7. On the play vs. on the draw comparison statistics

---

## 🛠️ Implementation Priority

**Phase 1: Core Decision Data (High Priority)**
1. Decision history endpoint (#4)
2. Keep/mulligan rate by depth (#2)
3. Decision reasoning tracking (#1)

**Phase 2: Advanced Analytics (Medium Priority)**
4. Cards bottomed tracking (#3)
5. Enhanced statistics views
6. Export functionality

**Phase 3: UX Enhancements (Future)**
7. Hand replay/seed system for on-play/on-draw comparison
8. Session history and review
9. Learning insights and recommendations

---

**AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0**

**Co-authored-by:**
- Claude (AI Assistant) <claude@anthropic.com>
- Vibe-Coder 1.z3r0 <vibecoder.1.z3r0@gmail.com>
