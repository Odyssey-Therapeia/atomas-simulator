# PRD: Nucleo Performance Engineering & Optimization

**Project:** atomas-simulator (Nucleo Engine)
**Author:** Odyssey Therapeia — Nautilus Research Lab
**Internal Code:** OT-NAU [CC-900] — EXP-1-26
**Status:** Draft
**Version:** 1.0
Status : in progress

---

## 1. Vision & Purpose

### 1.1 What We're Building

A high-performance Atomas game simulator that serves as the foundational environment for Stochastic MuZero / ReZero reinforcement learning research. The engine must be fast enough to support real-time MCTS planning (800+ simulations per move in under 100ms) and large-scale RL training (millions of environment steps per hour on a single Apple Silicon Mac).

### 1.2 Why Performance Matters

Reinforcement learning with tree search (MuZero, AlphaZero, ReZero) is uniquely bottlenecked by environment simulation speed. Unlike supervised learning where you process a fixed dataset, RL generates its own training data through environment interaction. Every training step requires simulating hundreds or thousands of game rollouts. The math is unforgiving:

A typical Stochastic MuZero training configuration uses 800 MCTS simulations per move. Each simulation plays out the game for ~20 steps on average. A single training game lasts ~100 moves. That means one training game requires `800 × 20 × 100 = 1.6 million` environment steps just for MCTS, plus the actual gameplay steps. A training run needs thousands of games. If each environment step takes even 10 microseconds, a single training game's MCTS alone takes 16 seconds. At 1 microsecond per step, it takes 1.6 seconds. At 100 nanoseconds per step, it's 160 milliseconds — fast enough for real-time play with full MCTS.

The target: **10M+ environment steps per second on a single M-series core** for the scalar engine, scaling to **100M+ steps per second** with SIMD vectorization, and **1B+ steps per second** with GPU parallelism across thousands of simultaneous games. These targets would make Nucleo one of the fastest RL environments ever built and a compelling demonstration of Mojo's capabilities.

### 1.3 Why This Is Also A Public Statement

This project is Odyssey Therapeia's first public open-source repository. The performance story is part of the positioning. When the README says "X million steps/second on Apple Silicon, Y× faster than Python," that is a concrete, verifiable claim that demonstrates technical depth. Every benchmark number we publish builds credibility. The optimization work isn't just engineering — it's the artifact that proves we know what we're doing.

### 1.4 The Secondary Goal: A Reference Implementation

By optimizing in stages (compiled → stack-allocated → SIMD → GPU) and measuring at each stage, we create a tutorial-grade reference for how to squeeze performance out of Mojo on Apple Silicon. Each optimization phase is documented, benchmarked, and explained. This makes the repo valuable not just for RL researchers but for anyone learning Mojo performance engineering.

---

## 2. Current State Assessment

### 2.1 What Exists

The engine is functionally complete. All four layers are implemented and tested:

- **Layer 1 (Mojo Engine):** GameState with dynamic `List[Int8]` ring, board-driven fusion with chain reactions, spawn system with Plus guarantee / Minus / Black Plus / Neutrino / pity spawns, full action system with Discrete(19+) action space, integration tests passing 100 seeded games to completion.
- **Layer 2 (Web Interface):** FastAPI server + Canvas-based browser UI, playable at localhost:8080.
- **Layer 3 (RL Wrapper):** Gymnasium-compatible NucleoEnv with padded observation (64 slots) and action masking (65 actions), canonical observation rotation.
- **Layer 4 (LightZero Adapter):** Import-guarded Python wrapper with BaseEnv compatibility.

### 2.2 Known Performance Problems

**Problem 1: Heap allocation on every ring mutation.** `ring.mojo`'s `insert_at` and `remove_at` both construct a brand new `List[Int8]` by iterating through the old list and appending element-by-element. A single chain reaction of depth 4 (common in gameplay) triggers approximately 8 removals and 4 insertions = 12 new list allocations. Each allocation involves a heap malloc, element-by-element copy, and deallocation of the old list. This is the dominant cost in the engine and directly contradicts Mojo's value proposition of stack-allocated, zero-allocation performance.

**Problem 2: No SIMD utilization.** All operations (find highest atom, count atoms, check neighbor matches, scan for reactable Plus tokens) are scalar loops over Int8 arrays. Apple Silicon's NEON SIMD units can process 16 Int8 values per instruction, meaning we're using roughly 1/16th of the available throughput for these operations.

**Problem 3: No parallelism.** The engine runs one game at a time on one core. For MCTS, we need thousands of simultaneous rollouts. For training, we need tens of thousands of parallel games. The current architecture has no path to GPU execution because `List[Int8]` is not GPU-compatible (dynamic heap allocation is not supported on GPUs).

**Problem 4: No benchmarks exist.** We have no measurements of current performance, no comparison baseline against Python, and no way to verify whether optimizations actually help. We cannot credibly claim "high performance" without numbers.

**Problem 5: Python equivalent doesn't exist.** Without a pure-Python implementation of the same game logic, we have no baseline for Mojo's speedup. The `web/bridge.py` wraps the Mojo engine via shared library, so it measures Mojo-through-Python, not Python itself.

### 2.3 What's Working Well

The game logic is correct and well-tested. The architecture separates concerns cleanly (game_state / ring / fusion / scoring / spawn / actions). The board-driven reaction scan with counter-clockwise precedence is algorithmically correct. The RL wrapper properly handles observation encoding, action masking, and canonical rotation. These don't need to be rewritten — they need to be made faster while preserving their correctness.

---

## 3. Optimization Phases

The optimization work is structured in four phases (A through D), each building on the previous. Every phase includes its own benchmarks so we can measure the impact of each change independently. The phases are ordered by impact-to-effort ratio: Phase A and B deliver the biggest gains with the least architectural change, while C and D are more ambitious.

### Phase A: Correctness, Safety, and Compiled Code Baseline

**What:** Establish the performance baseline, build the Python comparison, add safety assertions, and create the benchmarking infrastructure.

**Why:** Before optimizing anything, we need to know where we stand. We also need to verify that the current code is actually correct under stress (the integration test runs 100 games, but we need thousands to catch rare edge cases). And we need the Python baseline because "X× faster than Python" is the headline number everyone understands.

**Deliverables:**

A.1 — **`bench/bench_throughput.mojo`**: Core benchmark harness. Plays N complete random games with seeded RNG, measures wall-clock time using `time.now()`, reports total games completed, total environment steps taken, total elapsed nanoseconds, steps per second, average steps per game, and average game duration. Runs a warmup pass (100 games, discarded) before the measurement pass (1000 games). Accepts command-line arguments for game count and seed. Outputs results in both human-readable format and machine-parseable JSON for CI tracking.

A.2 — **`bench/bench_python.py`**: Pure Python implementation of the complete Atomas game engine (not the Mojo bridge — actual Python code implementing the same game logic). This must be a faithful port: same spawn algorithm, same chain reaction math, same action space, same terminal conditions. The benchmark plays the same N seeded games and reports the same metrics. This is the baseline that Mojo's speedup is measured against. The implementation should be idiomatic Python (using lists, random module, dataclasses) — not NumPy-optimized Python, because the point is to show what Mojo gives you over standard Python for this kind of workload.

A.3 — **`bench/bench_allocation.mojo`**: Allocation-focused benchmark. Wraps the ring mutation operations (`insert_at`, `remove_at`) in a tight loop, measuring operations per second. This isolates the allocation bottleneck from the rest of the game logic. Before and after Phase B, this benchmark shows the exact impact of the data structure change.

A.4 — **`tests/test_stress.mojo`**: Extended stress test. Plays 10,000 seeded games to completion, asserting all invariants on every step: `atom_count` matches actual count of positive values in pieces, `highest_atom` matches actual maximum, no index out of bounds, score is monotonically non-decreasing, terminal condition is correctly detected. This catches rare edge cases that the 100-game integration test misses (race conditions in chain reaction index arithmetic, overflow at Int8 boundaries, degenerate spawn sequences).

A.5 — **`tests/test_determinism.mojo`**: Determinism verification. Plays the same seeded game twice and asserts that every intermediate state is identical. This verifies that the RNG seeding is truly deterministic, which is critical for reproducible benchmarks and reproducible RL training.

A.6 — **Safety audit of existing code.** Review and add bounds checks or debug assertions for: Int8 overflow when chain reactions produce elements > 127, index arithmetic in `chain_react` after element removal, `pick_straggler_spawn` when `atom_count` is 0, action masking edge cases when token count is 0 or 1. Each finding becomes either a code fix or a documented assumption with a `debug_assert`.

**Measurements produced:**
- Baseline steps/second (Mojo, current code)
- Baseline steps/second (Python)
- Mojo/Python speedup ratio
- Ring mutation operations/second (allocation benchmark)
- Stress test pass/fail over 10,000 games
- Determinism verification pass/fail

**Expected outcomes:** The current Mojo engine should be 10-50× faster than Python due to compiled code alone. The allocation benchmark will show that ring mutations are the dominant cost, setting up the motivation for Phase B.

---

### Phase B: Stack Allocation, Value Semantics & Apple Silicon Memory Architecture

**What:** Replace the heap-allocated `List[Int8]` ring with a stack-allocated fixed-capacity representation, eliminate all dynamic memory allocation from the hot path, and align data structures with Apple Silicon's unified memory architecture.

**Why:** This is the single highest-impact optimization. Apple Silicon's unified memory architecture means CPU, GPU, and Neural Engine all share the same physical RAM with no PCIe bus bottleneck. But you only benefit from this if your data structures are contiguous, predictable, and don't require heap management. Stack-allocated `InlineArray` gives you all three properties. Additionally, stack allocation means the game state lives in CPU registers or L1 cache rather than chasing heap pointers — this alone can deliver 5-10× speedup for tight loops.

**Deliverables:**

B.1 — **New ring representation: `InlineArray[Int8, 36]` + `token_count: Int`**

The current `List[Int8]` is dynamically sized and heap-allocated. The replacement is a fixed-capacity `InlineArray[Int8, 36]` (36 slots because: 18 atom cap + theoretical maximum of ~18 persistent Plus/BlackPlus tokens, rounded to allow headroom). A `token_count` field tracks how many slots are in use. This array lives entirely on the stack — no heap allocation, no pointer indirection, no garbage collection.

The `insert_at` operation becomes: shift elements from `position` to `token_count-1` rightward by one slot (using a reverse loop to avoid overwriting), write the new token at `position`, increment `token_count`. This is an O(N) shift but with no allocation — just register-to-register moves on contiguous memory.

The `remove_at` operation becomes: save the token at `position`, shift elements from `position+1` to `token_count-1` leftward by one slot, decrement `token_count`. Again, O(N) shift with zero allocation.

For the RL observation, the fixed-capacity array maps directly to the observation tensor with no conversion — the first `token_count` slots are the ring, the rest are zero-padded. This eliminates the copy step in `get_observation`.

B.2 — **`GameState` becomes fully stack-allocatable**

With `InlineArray` replacing `List`, the entire `GameState` struct is now a fixed-size value type. Its total size is: 36 bytes (ring) + 4 bytes (ints and Int8 fields) × ~12 fields ≈ ~84 bytes. This fits in a single CPU cache line (Apple Silicon L1 cache line is 128 bytes on performance cores). The entire game state can live in L1 cache, which means every access is a cache hit — no cache misses, no memory latency.

This also means `GameState` can be trivially copied (it's just 84 bytes of contiguous memory), which is essential for MCTS: each simulation needs to fork the game state, play out a rollout, and discard it. With the current `List`-based implementation, forking requires a heap allocation for the list copy. With `InlineArray`, forking is a single 84-byte memcpy — essentially free.

B.3 — **Eliminate all remaining heap allocations in the hot path**

Audit every function called during `step()` and ensure none of them allocate heap memory. Specific targets:

- `legal_actions` currently returns `List[Bool]` — replace with `InlineArray[Bool, 36]` or a bitmask `UInt64` (since max actions < 64, a single 64-bit integer can represent the entire action mask, with each bit corresponding to an action's legality — this is both smaller and faster to compare).
- `pick_straggler_spawn` creates a temporary `List[Int8]` of stragglers — replace with a scan that counts stragglers and selects the Nth one without building an intermediate list.
- `resolve_board_outcome` has no heap allocations but verify this.
- `chain_react` is recursive — verify that Mojo's tail-call optimization (if available in 0.26.2) eliminates stack frame accumulation, or convert to an iterative loop with explicit depth tracking.

B.4 — **Apple Silicon memory optimization**

Apple Silicon M-series chips have specific characteristics that we can exploit:

- **L1 cache: 128KB per performance core, 64KB per efficiency core.** Our ~84-byte GameState fits ~1500 states in L1. For MCTS with 800 simulations, all game states live in L1 the entire time — zero cache misses.
- **Unified memory architecture:** CPU and GPU see the same physical memory. When we later move to GPU parallelism (Phase D), the game states won't need to be copied between CPU and GPU memory — they're already there. This is why we want the data structure to be GPU-friendly from Phase B, not retrofitted in Phase D.
- **Memory alignment:** Align `GameState` to 64-byte boundaries using Mojo's alignment attributes (if available). This ensures each state starts at a cache line boundary, preventing false sharing when multiple cores process different game states.
- **Prefetching:** For batch operations (playing many games in sequence), insert prefetch hints so the next game's state is loaded into L1 while the current game's step is executing. Mojo may expose this through LLVM intrinsics.

B.5 — **Benchmark: Before vs After**

Re-run all Phase A benchmarks after the data structure change:
- Steps/second improvement (expected: 3-10× over Phase A baseline)
- Allocation benchmark should show operations/second approaching the theoretical maximum (no allocations means the benchmark measures only the shift arithmetic)
- Memory profile: measure peak heap usage per game (should drop to near-zero for the engine itself, with only the benchmark harness and I/O using heap memory)

**Measurements produced:**
- Steps/second after stack allocation (vs Phase A baseline)
- Ring operation throughput (insert/remove per second, no allocation)
- GameState size in bytes (verify ≤ 128 to fit in cache line)
- Peak heap memory per game (target: 0 bytes from engine operations)
- MCTS fork cost: time to copy GameState (target: < 10 nanoseconds)

**Expected outcomes:** 3-10× speedup over Phase A. The engine should now be 30-500× faster than Python. GameState copying should be nearly free, unblocking efficient MCTS in Phase D.

---

### Phase C: SIMD Vectorization

**What:** Replace scalar loops with SIMD operations wherever the data and operation support it. Leverage Apple Silicon's NEON SIMD units (128-bit registers, processing 16 Int8 values per instruction).

**Why:** After eliminating allocation overhead (Phase B), the remaining cost is in the computational loops themselves: scanning the ring for the highest atom, counting atoms, checking neighbor matches, computing legal actions. These are all "do the same simple operation to every element in a small array" — the exact pattern SIMD was designed for. On Apple Silicon, NEON can process 16 Int8 elements per cycle, so a 36-element ring requires just 3 SIMD operations instead of 36 scalar operations. The theoretical speedup is 10-16× for these operations.

**Deliverables:**

C.1 — **SIMD-accelerated `recalculate_highest`**

Current implementation: scalar loop over `pieces`, tracking max. SIMD version: load the 36-byte ring into three `SIMD[DType.int8, 16]` registers. Use `simd_reduce_max` (or sequential `max` across registers) to find the maximum in 3 instructions instead of 36 comparisons. Mask out slots beyond `token_count` by setting them to `Int8.MIN` before the reduce.

C.2 — **SIMD-accelerated `recalculate_atom_count`**

Current implementation: scalar loop counting `token > 0`. SIMD version: load ring into SIMD registers, compare each element against 0 using SIMD comparison (produces a mask where each lane is all-1s if > 0, all-0s otherwise), popcount the resulting mask to get the count. This replaces 36 branches with 3 comparisons and 3 popcounts.

C.3 — **SIMD-accelerated `legal_actions` computation**

If legal_actions is represented as a bitmask (from Phase B.3), the entire mask can be computed with SIMD comparisons. For the "regular atom on non-full board" case, the mask is simply "all 1s up to token_count" which is a single shift operation: `(1 << token_count) - 1`. For Minus/Neutrino (select positive atoms), compare the ring against 0 with SIMD and extract the comparison mask directly as the action bitmask.

C.4 — **SIMD-accelerated board scan for reactable Plus tokens**

The `resolve_board_outcome` function iterates over all tokens looking for Plus or BlackPlus that can react. This involves checking each token's value and then checking its neighbors. The token-value check can be vectorized: load the ring into SIMD, compare against `PLUS` and `BLACK_PLUS` to produce candidate masks. Then iterate only over the set bits in the mask (which is a much shorter loop when Plus tokens are sparse). This doesn't eliminate the neighbor check, but it eliminates scanning non-Plus tokens.

C.5 — **SIMD batch operations for future MCTS**

Create vectorized versions of key operations that work on multiple game states simultaneously. For example, `batch_recalculate_highest` takes an array of N game states (stored as a struct-of-arrays: one SIMD register per field across N games) and computes all N highest-atom values in parallel. This is preparation for Phase D but can be benchmarked on CPU with SIMD today.

C.6 — **Benchmark: Scalar vs SIMD**

For each SIMD-accelerated function, measure:
- Operations per second (scalar version from Phase B)
- Operations per second (SIMD version)
- Speedup ratio
- Impact on overall steps/second (run the full game benchmark)

Key insight: for a 36-element ring, the SIMD gains on individual operations may be modest (3× for operations that were already L1-cache-friendly). The big SIMD win comes in Phase D when we vectorize across many games simultaneously.

**Measurements produced:**
- Per-function SIMD speedup (recalculate_highest, recalculate_atom_count, legal_actions, board_scan)
- Overall steps/second after SIMD (vs Phase B baseline)
- Batch operation throughput (N games processed per second)

**Expected outcomes:** 1.5-3× speedup on individual functions, 1.2-2× on overall steps/second (because fusion logic and spawn RNG are harder to vectorize and may dominate). The batch operations preview will show much larger gains (10-16× per batch) because SIMD shines when the same operation is applied to many independent data streams.

---

### Phase D: GPU Parallelism

**What:** Run thousands of game instances simultaneously on the Apple Silicon GPU, enabling massively parallel MCTS rollouts and training data generation.

**Why:** This is the endgame. A single M3 Pro GPU has ~18 compute units running at ~1.4 GHz, capable of thousands of simultaneous threads. If each thread runs one game instance, and each game state is ~84 bytes (from Phase B), we can fit millions of game states in the GPU's share of unified memory. The theoretical throughput is billions of environment steps per second — more than enough for any RL training setup.

This is also the phase that validates Mojo's core value proposition for our use case: write the game logic once, run it on CPU or GPU without rewriting. If Phase B produced a clean, allocation-free, fixed-size data structure, the GPU port should require minimal code changes — primarily replacing the random number generation (GPU-compatible RNG) and the game loop orchestration (GPU kernel launch instead of sequential loop).

**Deliverables:**

D.1 — **GPU-compatible GameState**

Verify that the Phase B `GameState` (with `InlineArray[Int8, 36]`) is compatible with GPU execution. Specifically: no heap allocations (verified in Phase B), no dynamic dispatch, no I/O operations, no global mutable state. The `spawn_piece` function uses Mojo's `random_si64` and `random_float64` which may not work on GPU — replace with a GPU-compatible PRNG (e.g., a simple xoshiro256 implemented in Mojo, seeded per game instance).

D.2 — **GPU kernel: parallel random game simulation**

A Mojo GPU kernel that launches N threads, each playing one complete random game. Each thread has its own GameState in local/shared memory, its own PRNG state, and independently plays the game to completion. The kernel collects per-game statistics: final score, total steps, highest element achieved, and terminal atom count. These are written back to a results buffer.

This is the simplest possible GPU workload: embarrassingly parallel, no inter-thread communication, no shared state. It's the ideal first GPU kernel for the project.

D.3 — **GPU kernel: parallel MCTS rollout**

A more sophisticated kernel for MCTS support. Takes as input: an array of N game states (the current positions being evaluated) and an array of N action sequences. Each thread applies its action sequence to its game state copy and plays out to completion (or a fixed depth limit), returning the final value estimate. This is the core primitive that Stochastic MuZero needs: given a position, evaluate many possible futures in parallel.

D.4 — **CPU-GPU hybrid orchestration**

The MCTS tree lives on the CPU (it requires dynamic memory allocation for tree nodes, which GPUs can't do efficiently). The rollouts happen on the GPU. The orchestration loop: CPU selects leaf nodes to expand → copies their game states to GPU → GPU runs parallel rollouts → copies results back to CPU → CPU updates tree statistics. Because Apple Silicon uses unified memory, the "copy" steps are actually zero-copy — just passing pointers. This is the key advantage of building on Apple Silicon.

D.5 — **Benchmark: GPU throughput scaling**

Measure environment steps per second as a function of parallel game count:
- N = 1, 10, 100, 1,000, 10,000, 100,000
- Plot throughput vs N to identify the saturation point (where adding more games stops increasing throughput)
- Compare against CPU-only throughput at the same N (using threading)
- Measure GPU kernel launch overhead (time from CPU dispatch to first thread executing)
- Measure result collection latency (time from last thread finishing to CPU having all results)

D.6 — **Apple Silicon GPU-specific optimizations**

- **Threadgroup memory:** Store frequently accessed game constants (spawn rates, scoring formulas) in threadgroup shared memory rather than per-thread local memory.
- **SIMD-group operations:** Use Apple's SIMD-group (warp-level) primitives for reductions within a group of 32 threads, e.g., finding the highest score across 32 parallel games.
- **Occupancy tuning:** Measure and tune the number of threads per threadgroup and threadgroups per compute unit to maximize GPU occupancy for the ~84-byte-per-thread workload.

**Measurements produced:**
- Steps/second at each parallelism level (N = 1 to 100K)
- GPU saturation point (N at which throughput plateaus)
- GPU vs CPU throughput at equivalent parallelism
- Kernel launch overhead (nanoseconds)
- MCTS rollout throughput (rollouts/second with given depth limit)
- End-to-end MCTS decision time (800 simulations, 20-step rollouts)

**Expected outcomes:** 100-1000× throughput over single-core CPU for large N. The Apple Silicon unified memory advantage should make CPU-GPU communication nearly free. The end-to-end MCTS decision time should be under 50ms for 800 simulations, enabling real-time play with full search.

---

## 4. Benchmarking Infrastructure

### 4.1 Benchmark Harness Design

All benchmarks share a common harness that ensures consistent, reproducible measurement:

- **Warmup phase:** N warmup iterations (discarded) to ensure JIT compilation, cache warming, and steady-state behavior.
- **Measurement phase:** M measured iterations with wall-clock timing via `time.now()` (nanosecond resolution).
- **Statistical rigor:** Report mean, median, min, max, and standard deviation across multiple runs. Flag results with > 10% coefficient of variation as unreliable.
- **Environment recording:** Each benchmark run records: Mojo version, OS version, chip model (M1/M2/M3/M4 and variant), core count, memory size, and thermal state (if detectable). This ensures results are reproducible and comparable across machines.
- **Output format:** Both human-readable table and JSON file. The JSON is designed for CI integration: a GitHub Action can run benchmarks on every PR and flag regressions.

### 4.2 Benchmark Suite

| Benchmark | File | What It Measures | Target Metric |
|-----------|------|-----------------|---------------|
| Game throughput | `bench/bench_throughput.mojo` | Complete random games per second, steps per second | Steps/sec |
| Python baseline | `bench/bench_python.py` | Same as above, pure Python | Steps/sec |
| Ring operations | `bench/bench_ring.mojo` | insert_at + remove_at operations per second | Ops/sec |
| Allocation profile | `bench/bench_allocation.mojo` | Heap allocations per game step (before/after Phase B) | Allocs/step |
| Fork cost | `bench/bench_fork.mojo` | Time to copy a GameState (critical for MCTS) | Nanoseconds |
| SIMD functions | `bench/bench_simd.mojo` | Per-function throughput, scalar vs SIMD | Speedup ratio |
| Batch processing | `bench/bench_batch.mojo` | N games stepped simultaneously (CPU SIMD) | Batch steps/sec |
| GPU throughput | `bench/bench_gpu.mojo` | Parallel games on GPU at various N | Steps/sec vs N |
| MCTS rollout | `bench/bench_mcts.mojo` | Complete MCTS decision (800 sims × 20 depth) | Milliseconds |

### 4.3 Continuous Performance Tracking

After the initial benchmarks are established, add a GitHub Action (`benchmark.yml`) that runs the throughput benchmark on every push to `main` and stores the result as a JSON artifact. A simple Python script compares the latest result against the previous best and posts a comment on PRs that cause > 5% regression. This prevents accidental performance degradation as the codebase evolves.

---

## 5. Python Baseline Implementation

### 5.1 Why A Full Python Port

The Python baseline isn't just for bragging rights. It serves three purposes:

First, it validates correctness. If the Python engine and the Mojo engine produce identical game trajectories for the same seed, we have high confidence that both implementations are correct. Any divergence indicates a bug in one or both.

Second, it provides the speedup number. "Mojo is X× faster than Python for this workload" is the most universally understood performance claim. Every developer has an intuition for how fast Python is — the speedup tells them exactly what Mojo gives them.

Third, it serves as a reference implementation. The Python code is more readable than the Mojo code for most developers (since Mojo is still niche). Contributors can read the Python version to understand the game logic, then look at the Mojo version to understand the optimization.

### 5.2 Scope

The Python baseline must implement: GameState (ring as a Python list), spawn_piece (same algorithm with same probabilities), resolve_fusion (same chain reaction math), legal_actions, apply_action, step. It does NOT need to implement the web interface or the RL wrapper — just the core engine. It should be a single file (`bench/bench_python.py`) or a small package (`bench/python_engine/`).

### 5.3 Correctness Verification

The shipped cross-validation entry point is `bench/verify_cross_validation.py`, not `bench/verify_determinism.py`.

Current verification has two parts:

1. The Python baseline replays a pre-generated random sequence exactly, proving that the Python benchmark engine itself is deterministic under an injected RNG stream.
2. The Python and Mojo engines are compared over a seeded corpus, but exact step-for-step parity is **not yet supported** because the Mojo engine still consumes RNG internally and does not expose an injected random-stream interface.

Because of that limitation, the current correctness story is:

- exact replay within the Python baseline using pre-generated RNG sequences
- honest cross-validation reporting between Python and Mojo via `bench/verify_cross_validation.py`
- no claim of exact seeded parity between the two engines until Mojo exposes shared PRNG / injected-stream support

---

## 6. Measurement & Interpretation Guide

### 6.1 How To Read The Numbers

**Steps per second** is the primary metric. Here's what different ranges mean for the project's goals:

- **< 100K steps/sec:** Too slow for meaningful RL training. Each training run would take days to weeks. Investigate algorithmic issues or excessive allocation.
- **100K - 1M steps/sec:** Usable for small-scale experiments. A training run takes hours. This is where the current code likely sits after Phase A (compiled but unoptimized).
- **1M - 10M steps/sec:** Good for full RL training on CPU. MCTS with 800 simulations at depth 20 takes ~1.6 seconds per move. This is achievable after Phase B (stack allocation).
- **10M - 100M steps/sec:** Excellent. MCTS at 800 simulations takes ~160ms per move, enabling real-time play with search. Achievable after Phase C (SIMD) for batch operations.
- **100M+ steps/sec:** World-class. Achievable only with GPU parallelism (Phase D) running thousands of games simultaneously. Training at this speed completes in minutes.

**Speedup over Python** is the headline number for external communication:

- **10-30×:** Expected for Phase A (compiled code, but same data structures). Typical for "just rewrite it in a compiled language."
- **50-200×:** Expected for Phase B (stack allocation eliminates the overhead that Python-equivalent data structures have). This is where Mojo starts to pull away from what you'd get by "just rewriting in C++."
- **200-1000×:** Expected for Phase C (SIMD). This is difficult to achieve in Python even with NumPy because the operations are too irregular for NumPy's vectorized operations (the ring is small and the operations are branch-heavy).
- **1000×+:** Expected for Phase D (GPU parallelism). This is the "different paradigm" level where the comparison against single-threaded Python becomes somewhat academic.

**Fork cost (GameState copy time)** directly impacts MCTS performance:

- **> 100ns:** MCTS will be bottlenecked by state copying. 800 simulations × 100ns = 80μs just for copying, which is significant.
- **10-100ns:** Acceptable. MCTS overhead from copying is negligible.
- **< 10ns:** Excellent. A single memcpy of an 84-byte struct on Apple Silicon should be in this range.

### 6.2 How To Run Benchmarks

Each benchmark should be runnable via a pixi task:

```bash
pixi run bench-throughput     # Mojo engine throughput
pixi run bench-python         # Python baseline
pixi run bench-allocation     # Ring operation microbenchmark
pixi run bench-fork           # GameState copy cost
pixi run bench-simd           # SIMD vs scalar comparison
pixi run bench-gpu            # GPU parallel throughput
pixi run bench-all            # Run everything, produce summary
```

### 6.3 How To Interpret Regressions

If a code change causes a benchmark regression:

- **< 5% regression:** Noise. Re-run 3 times. If consistently lower, investigate but don't block the change.
- **5-20% regression:** Significant. Profile the change to understand why. Acceptable if it fixes a correctness bug or enables a future optimization.
- **> 20% regression:** Serious. Do not merge without a clear explanation and a plan to recover the performance.

### 6.4 Profiling Tools

- **macOS Instruments (Time Profiler):** Profile the benchmark binary to see function-level time breakdown. Use `xcrun xctrace record --template 'Time Profiler' --launch bench/bench_throughput`.
- **Mojo's built-in profiling:** Check if Mojo 0.26.2 supports `-profile` or equivalent flags on the `mojo run` command.
- **Custom timing:** For micro-benchmarks, use `time.now()` around specific function calls within the Mojo code itself.
- **Memory profiling:** Use `leaks` and `heap` (macOS developer tools) on the benchmark binary to measure heap allocations. After Phase B, the engine should show zero heap allocations during gameplay.

---

## 7. README Roadmap (Public-Facing)

The following should be added to the repository's README.md as a "Roadmap" section. It communicates planned features without committing to timelines.

### 7.1 Proposed README Section

```markdown
## Roadmap

### Shipped
- [x] Complete Atomas Classic Mode engine (all piece types, chain reactions, board-driven fusion)
- [x] Browser-playable interface (Canvas-based UI via FastAPI)
- [x] Gymnasium-compatible RL environment with observation encoding and action masking
- [x] LightZero adapter for Stochastic MuZero integration
- [x] 100-game seeded integration test suite
- [x] Deterministic replay via RNG seeding

### Performance Engineering (In Progress)
- [ ] Benchmarking infrastructure with Python baseline comparison
- [ ] Stack-allocated ring (InlineArray, zero heap allocation in hot path)
- [ ] SIMD-accelerated ring operations (recalculate_highest, atom_count, legal_actions)
- [ ] GameState fork cost < 10ns (critical for MCTS)
- [ ] Published benchmark results on Apple Silicon (M1/M2/M3/M4)

### Planned
- [ ] GPU-parallel game simulation (thousands of simultaneous games on Apple Silicon GPU)
- [ ] MCTS rollout kernel (800 simulations in < 50ms)
- [ ] Stochastic MuZero training pipeline (end-to-end, Apple Silicon native)
- [ ] Multi-GPU and distributed training support
- [ ] Geneva Mode (alternative game mode from Atomas)
- [ ] HuggingFace Spaces deployment (play in browser without local setup)
- [ ] Pre-trained agent weights and evaluation toolkit

### Community Contributions Welcome
- Chain reaction edge case testing
- Apple Silicon benchmark results (especially M4 Pro/Max/Ultra)
- Alternative reward shaping strategies
- Visualization tools for game trajectories and MCTS trees
- Ports to other RL frameworks (CleanRL, RLlib, Sample Factory)
```

---

## 8. Success Criteria

This PRD is complete when:

1. **Phase A delivers:** a baseline benchmark showing current steps/second, a pure-Python comparison showing Mojo speedup, and 10,000-game stress tests passing.

2. **Phase B delivers:** zero heap allocations in the hot path, GameState copy under 10ns, and 3-10× speedup over Phase A baseline.

3. **Phase C delivers:** measurable SIMD speedup on at least 3 ring operations, and overall 1.2-2× improvement over Phase B.

4. **Phase D delivers:** GPU kernel running 10,000+ parallel games with near-linear throughput scaling, and a proof-of-concept MCTS rollout completing 800 simulations in under 50ms.

5. **The README contains:** published benchmark numbers with methodology, a clear roadmap of shipped and planned features, and a "Performance" section that tells the story of Mojo's advantages for RL environment development.

6. **The Notion experiment page is updated** with results from each phase, linking to the benchmark data and any architectural decisions made during optimization.

---

## 9. Non-Goals

- **We are not building a general-purpose game engine framework.** Nucleo is purpose-built for one game (Atomas-style circular merge) and one use case (RL training). Generalization to other games is a future project.
- **We are not optimizing the web interface.** The FastAPI server and Canvas frontend are for human play and demonstration. They don't need to be fast.
- **We are not implementing the full Stochastic MuZero training loop in this PRD.** That's a separate project that depends on this engine being fast. This PRD focuses on making the engine ready for that training loop.
- **We are not targeting x86 or Windows.** Apple Silicon is the primary target. Linux aarch64 is a secondary target (for CI/cloud). x86 and Windows support are welcome community contributions but not our focus.
- **We are not competing with Atari environments.** Atari has pixel-based observation spaces and different performance characteristics. Nucleo's advantage is that it's a pure-logic environment with tiny state, which should be orders of magnitude faster than any pixel-based environment.

---

## 10. References

- Schrittwieser et al., "Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model" (MuZero, Nature 2020)
- Antonoglou et al., "Planning in Stochastic Environments with a Learned Model" (Stochastic MuZero, ICLR 2022)
- Ye et al., "ReZero: Boosting MCTS-based Algorithms by Backward-view Reanalysis" (CoRL 2025)
- LightZero framework: github.com/opendilab/LightZero
- Mojo documentation: docs.modular.com/mojo/manual/
- Mojo SIMD reference: docs.modular.com/mojo/stdlib/builtin/simd/
- Apple Silicon architecture: developer.apple.com/documentation/apple-silicon
- Stanford CS238: "Searching for a Reaction: MCTS Applied to Atomas"
