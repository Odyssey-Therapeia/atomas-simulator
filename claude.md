# atomas-simulator
recreate atomas , to use as a simulator for muzero OT-NAU [CC-900] - EXP-1-26

# Nucleo — An Atomas-Style Puzzle Game Engine in Mojo 🔥

## What This Project Is

Nucleo is a high-performance circular-merge puzzle game engine written in Mojo, open-sourced by Odyssey Therapeia. The game mechanics are inspired by Atomas (a proprietary mobile game by Sirnic) — we use original theming, naming, and visual identity. Only the underlying gameplay mechanics (which cannot be copyrighted) are recreated.

The project serves three purposes:

1. **A playable game** — a circular puzzle where players merge numbered elements to create higher-value elements through chain reactions
2. **An RL-ready environment** — the engine exposes a Gymnasium-compatible interface (`step`, `reset`, `legal_actions`, `is_terminal`) designed for reinforcement learning research, specifically Stochastic MuZero and ReZero algorithms
3. **An open-source contribution to the Mojo ecosystem** — one of the first game engines and RL environments built in Mojo, demonstrating the language's capabilities for game logic and hardware-agnostic compute

## Why Mojo

Mojo gives us Python-like readability with C++-level performance, and compiles to NVIDIA, AMD, and Apple Silicon GPUs from a single codebase. This project demonstrates that Mojo is viable for game simulation and RL environment development — not just ML inference. The game engine must be fast enough to run millions of parallel simulations for MCTS-based RL training.

## Game Mechanics (Reverse-Engineered from Atomas)

### Core Loop
- The board is a **circular ring of tokens**
- The gameplay cap is **18 atoms**, not 18 total tokens
- Persistent Plus and Black Plus tokens can remain on the ring, so total token count can exceed 18
- Each turn, the player receives a random element (or special item) in their "hand"
- The player places the element into a gap between existing elements on the ring
- If the placement or a later board change completes symmetry around an existing Plus/Black Plus token, a **chain reaction** starts
- The game starts with a seeded **6-atom opening board** in the range 1-3
- The game ends when the ring has 18 atoms and the next piece is a regular atom that cannot legally be played
- The goal is to achieve the highest possible score

### Elements
- Regular elements are represented as positive integers corresponding to atomic numbers (1 = Hydrogen, 2 = Helium, 3 = Lithium, etc.)
- Special items use negative integers: -1 = Plus, -2 = Minus, -3 = Black Plus, -4 = Neutrino
- Empty slots are represented as 0

### Spawn Algorithm
- **Plus (+):** ~17% chance, guaranteed at least every 5 moves
- **Minus (-):** ~5% chance, roughly every 20 moves
- **Black Plus:** 1/80 chance when score > 750
- **Neutrino:** 1/60 chance when score > 1500
- **Regular elements:** Uniform spawn in range `[max(1, M-4), max(1, M-1)]` where M = highest element on the board
- **Pity spawns:** Low-level straggler elements occasionally force-spawned to help the player clear them

### Chain Reaction Math
When a Plus (+) is placed between two matching elements:
- **First merge:** `result = combining_element + 1` (e.g., 3, +, 3 → 4)
- **Chain reactions (subsequent merges):**
  - If outer matching element Y < center C: `new_center = C + 1`
  - If outer matching element Y >= center C: `new_center = Y + 2`
- Reactions are **recursive** — after a merge, the new center element checks its new neighbors
- The board is **circular** — element at index 0 is adjacent to the last element

### Minus (-) Behavior
- Minus absorbs the element it is placed on (removes it from the ring)
- The absorbed element goes into the player's "hand"
- The player can then place it elsewhere, or convert it to a Plus (+)

### Black Plus Behavior
- Functions like Plus but can merge **any** two adjacent elements, regardless of whether they match
- Result follows the same math as regular Plus merges
- When a Dark Plus fuses a Plus or Black Plus token, treat that special as effective value `1`

### Neutrino Behavior
- Neutrino copies an atom on the ring without removing the original
- The copied atom goes into the player's hand and **cannot** be converted into a Plus
- If played on a full 18-atom board, it can overflow the atom cap and immediately end the game unless a reaction reduces the board

### Scoring
- Raw game scores are exponential (2^X where X is the element number)
- For RL training, use **log2(score)** or **linear element value** as reward to avoid exploding gradients

## Architecture

### Layer 1: Game Engine (Pure Mojo — No Dependencies)

This is the core. Zero UI, zero network, zero Python dependencies. Just game logic.

```
src/
├── nucleo/
│   ├── __init__.mojo     # Package root
│   ├── game_state.mojo   # Authoritative gameplay state and reset/spawn helpers
│   ├── ring.mojo         # Circular token-ring operations
│   ├── fusion.mojo       # Board-driven scan + chain reaction resolution
│   ├── spawn.mojo        # Spawn wrappers over GameState spawn methods
│   ├── actions.mojo      # legal_actions(), apply_action(), step()
│   └── scoring.mojo      # Score calculation and reward shaping
└── main.mojo             # Thin CLI entrypoint
```

Key design decisions:
- The engine ring is a **dynamic `List[Int8]` of tokens**, not a fixed-size atom array
- `atom_count <= 18` is the gameplay invariant; token count may exceed 18 because unresolved Plus tokens persist
- Reactions are **board-driven**, not just current-piece-driven: after any placement, scan the ring for reactable Plus/Black Plus tokens
- The RL wrapper canonicalizes the ring by rotating so the highest-value atom is at index 0
- `step(action) -> (observation, reward, done, info)` pattern from day one, even before RL integration
- All new Mojo code should use **`def`**, not deprecated `fn`
- The engine action space is **dynamic** based on token count and held-piece state
- The RL wrapper projects that dynamic action space into a padded `MAX_ACTIONS = 65` mask

### Layer 2: Play Interface (Python + Mojo Interop)

A thin web server that imports the Mojo engine via Python interop and serves a browser-playable frontend.

```
web/
├── server.py             # FastAPI or Flask server
├── static/
│   ├── index.html        # Game UI (vanilla HTML Canvas)
│   └── game.js           # Client-side rendering and input handling
└── bridge.py             # Python wrapper around Mojo engine via interop
```

### Layer 3: RL Interface (Future)

A Gymnasium-compatible wrapper for RL training. Not built initially, but Layer 1 is architected to make this trivial to add.

```
rl/
├── observation.mojo      # Padded observation encoding and canonical rotation
├── env.mojo              # Gymnasium-compatible environment wrapper
├── wrappers.mojo         # Reward shaping and normalization
└── lightzero_env.py      # LightZero adapter
```

## MDP Formulation (For RL — Guides Engine Design)

Even though we're building a faithful playable game first, the RL interface wraps the engine without changing game rules.

- **Observation:** Padded observation tensor with `OBSERVATION_SIZE = 64`, made up of `TOKEN_SLOT_COUNT = 60` token slots plus 4 metadata entries for current piece and held-piece state
- **Action space:** Dynamic in the engine, padded to `MAX_ACTIONS = 65` in the RL wrapper
- **Action masking:** Critical — mask unused padded positions and illegal gap/select/convert actions
- **Reward:** Linear element value of merged atom, NOT raw exponential score
- **Terminal condition:** 18 atoms plus a regular in-hand spawn, or an overflow caused by a Neutrino placement that failed to resolve back under the cap

## Build & Run

```bash
# Install Mojo via pixi
pixi install

# Run the game engine tests
pixi run test

# Run the headless game (CLI mode)
pixi run run

# Start the web interface (requires Python interop layer)
pixi run serve
```

## Testing

- Test chain reactions against known board states
- Key test case: `[9, 3, 3, 3, +, 3, 3, 3, 9]` with Plus at index 4 → should resolve to `[11]`
- Test persistent Plus behavior: unresolved Plus stays on the ring and can react later
- Test counter-clockwise precedence when two Plus tokens could both react
- Test Neutrino copy/place behavior at and below the atom cap
- Test circular wrapping: merges that cross the 0-boundary of the ring
- Test action masking: verify illegal actions are properly masked
- Test spawn distribution: statistical tests over many spawns to verify rates match expected distributions
- Use the `testing` module from Mojo's standard library

## Conventions

- Format all Mojo code with `mojo format`
- Use descriptive variable names — `ring_size` not `rs`, `current_piece` not `cp`
- Every public function gets a docstring
- Commit messages: imperative mood, concise — "Add chain reaction resolver" not "Added chain reaction resolver"
- No secrets, no large binaries, no generated files in git

## Key References

- Atomas Wiki (mechanics): https://atomas.fandom.com/wiki/Atomas_Wiki
- Atomas Atoms and colors: https://atomas.fandom.com/wiki/Atoms
- Stanford CS238 paper: "Searching for a Reaction: MCTS Applied to Atomas"
- TkAtomas Python clone (logic reference): github.com/mattpdl/TkAtomas
- LightZero framework (future RL): github.com/opendilab/LightZero
- Mojo documentation: https://docs.modular.com/mojo/manual/
- Mojo LLM-friendly docs: https://docs.modular.com/llms-mojo.txt

## Who We Are

Odyssey Therapeia (odysseytherapeia.com) is a healthcare AI company. Our R&D team explores cutting-edge AI across domains — from medical devices to reinforcement learning. This project is part of our commitment to open-source contributions and advancing the Mojo ecosystem.