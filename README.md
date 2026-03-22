# atomas-simulator
recreate atomas , to use as a simulator for muzero OT-NAU [CC-900] - EXP-1-26

# Nucleo — An Atomas-Style Puzzle Game Engine in Mojo 

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
- The board is a **circular ring** with a maximum capacity of **18 slots**
- Each turn, the player receives a random element (or special item) in their "hand"
- The player places the element into a gap between existing elements on the ring
- If the placement triggers a **chain reaction** (via Plus atoms), elements merge into higher-value elements
- The game ends when the ring fills to 18 elements and a new element cannot be placed
- The goal is to achieve the highest possible score

### Elements
- Regular elements are represented as positive integers corresponding to atomic numbers (1 = Hydrogen, 2 = Helium, 3 = Lithium, etc.)
- Special items use negative integers: -1 = Plus, -2 = Minus, -3 = Black Plus
- Empty slots are represented as 0

### Spawn Algorithm
- **Plus (+):** ~15-20% chance, roughly every 5-6 moves
- **Minus (-):** ~5% chance, roughly every 20 moves
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

### Scoring
- Raw game scores are exponential (2^X where X is the element number)
- For RL training, use **log2(score)** or **linear element value** as reward to avoid exploding gradients

## Architecture

### Layer 1: Game Engine (Pure Mojo — No Dependencies)

This is the core. Zero UI, zero network, zero Python dependencies. Just game logic.

```
src/
├── game_state.mojo      # GameState struct: the ring, current piece, score, move count
├── ring.mojo             # Circular ring data structure and SIMD operations
├── fusion.mojo           # Chain reaction resolution logic
├── spawn.mojo            # Element spawn RNG and pity system
├── actions.mojo          # Action space: legal_actions(), apply_action()
└── scoring.mojo          # Score calculation and reward shaping
```

Key design decisions:
- The ring is a **fixed-size array of 18 Int8 values** (not a dynamic list)
- The ring should be canonicalized before feeding to a neural network: **rotate so the highest-value element is at index 0** (reduces effective state space by ~18x)
- `step(action) -> (observation, reward, done, info)` pattern from day one, even before RL integration
- All functions should be `fn` (typed, compiled) not `def` (dynamic) for performance
- Action space is `Discrete(19)`: actions 0-17 = insert at gap i, action 18 = convert held element to Plus

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
├── env.mojo              # Gymnasium-compatible environment wrapper
├── observation.mojo      # Observation space encoding
└── wrappers.mojo         # Canonicalization, reward shaping, action masking
```

## MDP Formulation (For RL — Guides Engine Design)

Even though we're building a playable game first, the engine's internal API follows the MDP formulation because the RL interface will wrap it directly later.

- **Observation:** 1D array of length 20 — 18 ring slots (padded with 0 for empty), 1 slot for current_piece, 1 boolean for holding_minus_absorbed_element
- **Action space:** Discrete(19) — actions 0-17 insert at gap i (or absorb at index i for Minus), action 18 converts absorbed element to Plus
- **Action masking:** Critical — disable actions beyond current ring size. MuZero handles masked actions natively.
- **Reward:** Linear element value of merged atom, NOT raw exponential score
- **Terminal condition:** Ring reaches 18 elements and new element cannot be placed

## Build & Run

```bash
# Install Mojo via pixi
pixi install

# Run the game engine tests
pixi run test

# Run the headless game (CLI mode — plays random moves)
pixi run run

# Build a standalone binary
pixi run build

# Format all Mojo source files
pixi run format
```

## Play as a Human

Nucleo includes a browser-based interface for playing the game interactively:

```bash
pixi run serve
```

Then open **http://localhost:8080** in your browser.

### Controls

- **Click a gap** between atoms to place regular atoms and Plus tokens
- **Click an atom** when your current piece is Minus (absorbs it) or Neutrino (copies it)
- **Click the center piece** to convert a held Minus-absorbed atom into a Plus

The sidebar shows live stats (score, moves, atom count, highest element) and a **Reset Game** button.

### How it works

The web interface is a thin Python layer over the Mojo engine:

- `web/server.py` — FastAPI server exposing `/api/reset`, `/api/step`, `/api/state`, and `/api/legal-actions`
- `web/bridge.py` — loads the compiled `python_module.so` shared library and normalizes engine state for JSON
- `web/static/index.html` + `game.js` — canvas-based circular ring renderer with click-to-play interaction

The bridge auto-builds the shared library from `src/nucleo/python_module.mojo` if it doesn't already exist.

## Testing

- Test chain reactions against known board states
- Key test case: `[9, 3, 3, 3, +, 3, 3, 3, 9]` with Plus at index 4 → should resolve to `[11]`
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
