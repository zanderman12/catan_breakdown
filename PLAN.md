# Catan Settlement Training App — Project Plan

## Context

Build an interactive training tool that helps Catan players practice initial settlement placement. The repo already has a solid analytical foundation (board generator, 54-node settlement graph, resource-scoring formulas, port value modeling). What's missing is the neighbor-constraint logic, snake-draft loop, scoring feedback layer, and an interactive interface.

---

## Existing Code to Reuse

| Component | File | What to Reuse |
|---|---|---|
| Board generator | `scripts/starting_placement_sim.py` → `create_board()` | Tile/number shuffling, resource availability |
| Settlement location graph | `play_one_game()` settlement_dict (54 nodes, tile adjacency) | Node-to-tile mapping |
| Port assignment | `play_one_game()` port_locs / port_types | Port shuffle and node tagging |
| Resource scoring | `calculate_resource_score()`, `calculate_total_pips()` | Raw score per node |
| Resource value model | `resvalue_dict` regression coefficients | Board-adjusted resource weights |
| pip lookup | `pipdict` | Roll-probability lookup |

---

## Checklist

### 1. Board Data Model (`catan/board.py`)

- [ ] Extract `create_board()`, `play_one_game()`, and helpers from `starting_placement_sim.py` into a `CatanBoard` class
- [ ] Add settlement adjacency graph (which of the 54 nodes are neighbors) for distance-rule enforcement
- [ ] Add coordinate system for each node (hex-grid axial or pixel coords) for rendering
- [ ] Implement `valid_placements(placed: list[int]) -> list[int]` — returns all legal nodes given already-placed settlements

### 2. Scoring Engine (`catan/scoring.py`)

- [ ] Implement `score_placement(node_ids, board) -> dict` returning pips, resource score, port value, and diversity score
- [ ] Add diversity bonus: penalize placements generating the same resource from multiple tiles
- [ ] Add port synergy bonus: reward placements near a port for a resource the spots already produce heavily
- [ ] Add percentile ranking via Monte Carlo: run N random-but-legal placements and report where the user's score falls

### 3. Snake Draft Logic (`catan/game_flow.py`)

- [ ] Implement `SnakeDraft` class to manage turn order for 2–4 players (1→2→3→4→4→3→2→1)
- [ ] Track which placement (1st or 2nd) each player is on
- [ ] Enforce distance rule across all players' placements
- [ ] Return starting resources for each player's second settlement

### 4. AI Recommender (`catan/recommender.py`)

- [ ] Implement greedy best-first: score all legal nodes, rank them, return top-N with scores
- [ ] Add optional 2-ply lookahead (best first pick given an anticipated second pick location)
- [ ] Expose `recommend(board, placed_so_far) -> list[(node_id, score)]`

### 5. CLI Training Interface (`scripts/train_cli.py`)

- [ ] Render ASCII hex board with node numbers as labels
- [ ] Prompt user to enter a node number and validate legality
- [ ] After each placement, print: user score, best available score, percentile rank, top-3 alternatives
- [ ] After both settlements placed, show full summary

### 6. Web Interface — stretch goal (`app/`)

- [ ] Choose framework (Streamlit recommended for speed; FastAPI + JS canvas for more control)
- [ ] Render hexagonal board graphically
- [ ] Click to place settlements; color-code nodes by score (green = high, red = low)
- [ ] Side panel: score breakdown, alternatives, historical percentile

### 7. Tests (`tests/`)

- [ ] `test_board.py` — board generation produces correct tile counts; no duplicate numbers on same resource type
- [ ] `test_scoring.py` — known board + placement returns expected pip count and resource score
- [ ] `test_distance_rule.py` — `valid_placements()` correctly excludes adjacent nodes
- [ ] `test_draft.py` — snake draft produces correct turn order for 2, 3, and 4 players

---

## Build Order

1. Board Data Model — everything downstream depends on this
2. Scoring Engine — can be built and tested in isolation
3. Distance rule + `valid_placements`
4. CLI Training Interface — delivers a working product quickly
5. AI Recommender — adds the learning feedback loop
6. Tests — written alongside each module
7. Web UI — stretch goal once core loop is solid

---

## Verification

- Run `pytest tests/` after each module is complete
- Smoke test: `python scripts/train_cli.py` generates a board, accepts two legal placements, prints scores without crashing
- Regression: 10,000 Monte Carlo simulations should produce average pip totals consistent with known Catan statistics (~10–15 pips for a good two-settlement starting position)
