"""Cross-validation helpers for the Mojo and pure-Python benchmark engines."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = ROOT / "bench"
if str(BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(BENCH_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import python_module  # noqa: E402
from python_engine import GameState as PythonGameState  # noqa: E402
from python_engine import legal_actions as python_legal_actions  # noqa: E402
from python_engine import step as python_step  # noqa: E402


DEFAULT_SEQUENCE_PATH = BENCH_DIR / "sequences" / "game_100_seed42.json"
DEFAULT_GAME_COUNT = 100
DEFAULT_SEED_START = 0
MAX_STEPS_PER_GAME = 5_000


@dataclass
class SequenceRNG:
    seed_value: int
    floats: list[float]
    ints: list[int]
    float_index: int = 0
    int_index: int = 0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SequenceRNG":
        """
        Constructs a SequenceRNG from a serialized payload dictionary.
        
        Parameters:
            payload (dict[str, Any]): Mapping containing keys "seed" (numeric), "floats" (iterable of numeric values), and "ints" (iterable of numeric values). Values will be converted to int/float as appropriate.
        
        Returns:
            SequenceRNG: An instance populated with `seed_value`, `floats`, and `ints` from the payload.
        """
        return cls(
            seed_value=int(payload["seed"]),
            floats=[float(value) for value in payload["floats"]],
            ints=[int(value) for value in payload["ints"]],
        )

    def seed(self, seed_value: int | None = None) -> None:
        """
        Validate an optional seed against the stored seed and reset the internal float and int stream cursors.
        
        Parameters:
        	seed_value (int | None): If provided, must match the SequenceRNG's configured seed.
        
        Raises:
        	ValueError: If `seed_value` is provided and does not equal the instance's `seed_value`.
        """
        if seed_value is not None and seed_value != self.seed_value:
            raise ValueError(
                f"SequenceRNG seed mismatch: expected {self.seed_value}, got {seed_value}"
            )
        self.float_index = 0
        self.int_index = 0

    def random(self) -> float:
        """
        Return the next float from the prerecorded float stream and advance the internal cursor.
        
        Returns:
            float: The next float value from the sequence.
        
        Raises:
            IndexError: If the prerecorded float sequence is exhausted.
        """
        if self.float_index >= len(self.floats):
            raise IndexError("SequenceRNG exhausted float sequence")
        value = self.floats[self.float_index]
        self.float_index += 1
        return value

    def randint(self, lower: int, upper: int) -> int:
        """
        Map the next stored integer from the sequence into the inclusive [lower, upper] range and return it.
        
        Parameters:
        	lower (int): Inclusive lower bound of the target range.
        	upper (int): Inclusive upper bound of the target range.
        
        Returns:
        	int: A value in the range [lower, upper] derived from the next stored integer.
        
        Raises:
        	IndexError: If the pre-generated int sequence is exhausted.
        
        Side effects:
        	Advances the internal int cursor by one.
        """
        if self.int_index >= len(self.ints):
            raise IndexError("SequenceRNG exhausted int sequence")
        raw_value = self.ints[self.int_index]
        self.int_index += 1
        return lower + (raw_value % (upper - lower + 1))


def parse_arg_or_default(index: int, default: int) -> int:
    """
    Read an integer command-line argument at the given argv index, or return a provided fallback.
    
    Parameters:
        index (int): Position in sys.argv to read.
        default (int): Fallback value returned when no argument exists at the given index.
    
    Returns:
        int: The integer parsed from sys.argv[index] if present, otherwise `default`.
    
    Raises:
        ValueError: If the argument is present but cannot be converted to an integer.
    """
    if len(sys.argv) > index:
        return int(sys.argv[index])
    return default


def normalize_python_state(state: PythonGameState) -> dict[str, Any]:
    """
    Convert a PythonGameState into a JSON-serializable dict of core game fields.
    
    Parameters:
        state (PythonGameState): The game state to normalize.
    
    Returns:
        normalized_state (dict[str, Any]): A dict with the normalized fields:
            - pieces (list[int]): Current board pieces as a list of ints.
            - atom_count (int)
            - current_piece (int)
            - score (int)
            - move_count (int)
            - highest_atom (int)
            - holding_piece (bool)
            - held_piece (int)
            - held_can_convert (bool)
            - is_terminal (bool)
            - moves_since_plus (int)
            - moves_since_minus (int)
            - rng_seed (int)
    """
    return {
        "pieces": list(state.pieces),
        "atom_count": int(state.atom_count),
        "current_piece": int(state.current_piece),
        "score": int(state.score),
        "move_count": int(state.move_count),
        "highest_atom": int(state.highest_atom),
        "holding_piece": bool(state.holding_piece),
        "held_piece": int(state.held_piece),
        "held_can_convert": bool(state.held_can_convert),
        "is_terminal": bool(state.is_terminal),
        "moves_since_plus": int(state.moves_since_plus),
        "moves_since_minus": int(state.moves_since_minus),
        "rng_seed": int(state.rng_seed),
    }


def normalize_mojo_state(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a Mojo engine state payload into the module's canonical JSON-serializable state dictionary.
    
    Parameters:
        payload (dict): State payload produced by the Mojo-backed engine; expected keys include
            "pieces", "atom_count", "current_piece", "score", "move_count", "highest_atom",
            "holding_piece", "held_piece", "held_can_convert", "is_terminal",
            "moves_since_plus", "moves_since_minus", and "rng_seed".
    
    Returns:
        dict: A normalized state dictionary with the following fields and concrete Python types:
            - "pieces" (list[int])
            - "atom_count" (int)
            - "current_piece" (int)
            - "score" (int)
            - "move_count" (int)
            - "highest_atom" (int)
            - "holding_piece" (bool)
            - "held_piece" (int)
            - "held_can_convert" (bool)
            - "is_terminal" (bool)
            - "moves_since_plus" (int)
            - "moves_since_minus" (int)
            - "rng_seed" (int)
    """
    return {
        "pieces": [int(token) for token in payload["pieces"]],
        "atom_count": int(payload["atom_count"]),
        "current_piece": int(payload["current_piece"]),
        "score": int(payload["score"]),
        "move_count": int(payload["move_count"]),
        "highest_atom": int(payload["highest_atom"]),
        "holding_piece": bool(payload["holding_piece"]),
        "held_piece": int(payload["held_piece"]),
        "held_can_convert": bool(payload["held_can_convert"]),
        "is_terminal": bool(payload["is_terminal"]),
        "moves_since_plus": int(payload["moves_since_plus"]),
        "moves_since_minus": int(payload["moves_since_minus"]),
        "rng_seed": int(payload["rng_seed"]),
    }


class MojoGame:
    def __init__(self, seed: int | None = None) -> None:
        """
        Initialize the MojoGame wrapper and create the underlying game instance.
        
        Parameters:
        	seed (int | None): Optional RNG seed to initialize the underlying game; if None, the game's default seeding is used.
        """
        self._game = python_module.Game(seed) if seed is not None else python_module.Game()

    def get_state(self) -> dict[str, Any]:
        """
        Retrieve the current game state as a normalized dictionary compatible with the Python engine's state schema.
        
        Returns:
            state (dict[str, Any]): JSON-serializable mapping of the game's observable fields, including piece layout (`pieces` as lists of ints), counters and scores (ints), terminal and held-piece flags (bools), move counters, and `rng_seed`.
        """
        return normalize_mojo_state(dict(self._game.get_state()))

    def step(self, action: int) -> tuple[dict[str, Any], int, bool]:
        """
        Advance the wrapped Mojo-backed game by one action and return the resulting normalized state and outcome.
        
        Parameters:
            action (int): Index of the action to apply.
        
        Returns:
            state (dict[str, Any]): Normalized game state dictionary suitable for JSON comparison.
            reward (int): Integer reward produced by the transition.
            done (bool): `True` if the game reached a terminal state after the step, `False` otherwise.
        """
        payload = dict(self._game.step(action))
        state = normalize_mojo_state(dict(payload["state"]))
        reward = int(payload["reward"])
        done = bool(payload["done"])
        return state, reward, done

    def legal_actions(self) -> list[bool]:
        """
        Return the action legality mask for the wrapped game.
        
        @returns
            list[bool]: A list where each element is `True` if the action at the corresponding index is legal, `False` otherwise.
        """
        return [bool(item) for item in self._game.legal_actions()]


def choose_first_legal_action(mask: list[bool]) -> int:
    """
    Selects the first index marked legal in a boolean action mask.
    
    Parameters:
    	mask (list[bool]): A boolean mask where `True` indicates the action at that index is legal.
    
    Returns:
    	index (int): The index of the first `True` entry in `mask`.
    
    Raises:
    	ValueError: If `mask` contains no `True` values.
    """
    for index, is_legal in enumerate(mask):
        if is_legal:
            return index
    raise ValueError("choose_first_legal_action: no legal actions available")


def choose_random_action_from_state_rng(state: PythonGameState, mask: list[bool]) -> int:
    """
    Selects a legal action index using the provided state's RNG.
    
    Parameters:
        state (PythonGameState): Game state whose `_rng` is used to sample the selection.
        mask (list[bool]): Boolean mask where `True` marks a legal action at that index.
    
    Returns:
        int: Index of a randomly chosen legal action.
    
    Raises:
        ValueError: If no actions are legal.
    """
    legal_indices = [index for index, is_legal in enumerate(mask) if is_legal]
    if not legal_indices:
        raise ValueError("choose_random_action_from_state_rng: no legal actions available")
    return legal_indices[state._rng.randint(0, len(legal_indices) - 1)]


def record_python_sequence_trajectory(sequence_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Play back a deterministic action sequence payload against the Python game engine and record the normalized state trajectory including the initial state.
    
    Parameters:
    	sequence_payload (dict[str, Any]): Payload describing a prerecorded sequence. Must include "seed" (numeric) and precomputed RNG streams under "floats" and "ints" in the format produced by SequenceRNG.from_payload.
    
    Returns:
    	trajectory (list[dict[str, Any]]): List of normalized game state dictionaries sampled after each step, with the first element the game's initial state.
    
    Raises:
    	RuntimeError: If the game does not reach a terminal state before MAX_STEPS_PER_GAME steps.
    	IndexError: If the provided sequence RNG exhausts its precomputed float or int streams during replay.
    """
    game = PythonGameState(rng_seed=int(sequence_payload["seed"]))
    game._rng = SequenceRNG.from_payload(sequence_payload)
    game.reset()

    trajectory = [normalize_python_state(game)]
    step_count = 0

    while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
        mask = python_legal_actions(game)
        action = choose_random_action_from_state_rng(game, mask)
        python_step(game, action)
        trajectory.append(normalize_python_state(game))
        step_count += 1

    if not game.is_terminal:
        raise RuntimeError("record_python_sequence_trajectory: exceeded turn limit")

    return trajectory


def record_seeded_python_trajectory(seed_value: int) -> list[dict[str, Any]]:
    """
    Generate a deterministic game trajectory from the Python engine starting from the given RNG seed.
    
    Parameters:
        seed_value (int): RNG seed used to initialize the PythonGameState.
    
    Returns:
        trajectory (list[dict[str, Any]]): Ordered list of normalized game state dictionaries, including the initial state and each subsequent state up to termination.
    
    Raises:
        RuntimeError: If the game does not reach a terminal state before MAX_STEPS_PER_GAME is exceeded.
    """
    game = PythonGameState(rng_seed=seed_value)
    trajectory = [normalize_python_state(game)]
    step_count = 0

    while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
        action = choose_first_legal_action(python_legal_actions(game))
        python_step(game, action)
        trajectory.append(normalize_python_state(game))
        step_count += 1

    if not game.is_terminal:
        raise RuntimeError("record_seeded_python_trajectory: exceeded turn limit")

    return trajectory


def record_seeded_mojo_trajectory(seed_value: int) -> list[dict[str, Any]]:
    """
    Record a full gameplay trajectory from the Mojo-backed engine initialized with a given seed.
    
    Parameters:
    	seed_value (int): RNG seed used to initialize the Mojo-backed game.
    
    Returns:
    	trajectory (list[dict[str, Any]]): Chronological list of normalized state dictionaries, including the initial state and ending with a terminal state.
    
    Raises:
    	RuntimeError: If the game does not reach a terminal state within MAX_STEPS_PER_GAME steps.
    """
    game = MojoGame(seed=seed_value)
    trajectory = [game.get_state()]
    step_count = 0

    while not trajectory[-1]["is_terminal"] and step_count < MAX_STEPS_PER_GAME:
        action = choose_first_legal_action(game.legal_actions())
        state, _reward, _done = game.step(action)
        trajectory.append(state)
        step_count += 1

    if not trajectory[-1]["is_terminal"]:
        raise RuntimeError("record_seeded_mojo_trajectory: exceeded turn limit")

    return trajectory


def main() -> None:
    """
    Run the cross-validation workflow that compares game state trajectories between the Python engine and the Mojo wrapper.
    
    This function:
    - Reads command-line arguments for a sequence JSON path, a number of seeded games to test, and a starting seed (defaults used when args are absent).
    - Validates inputs and loads the pre-generated action sequence payload.
    - Verifies deterministic replay by replaying the payload twice against the Python engine and asserting identical trajectories.
    - For each seed in the configured range, records a seeded trajectory from both the Python engine and the Mojo wrapper, counts exact matches, and collects up to three mismatch examples (initial and final normalized states).
    - Prints a human-readable summary and a JSON-like diagnostics block containing the sequence path, replay-match flag, corpus size, parity match count, and collected mismatch examples.
    
    Raises:
        FileNotFoundError: If the provided sequence file does not exist.
        ValueError: If the requested game_count is not positive.
        AssertionError: If the Python engine's replay of the same sequence payload diverges.
    """
    sequence_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SEQUENCE_PATH
    game_count = parse_arg_or_default(2, DEFAULT_GAME_COUNT)
    seed_start = parse_arg_or_default(3, DEFAULT_SEED_START)

    if not sequence_path.exists():
        raise FileNotFoundError(
            f"Sequence file not found: {sequence_path}. Run bench/generate_sequences.py first."
        )
    if game_count <= 0:
        raise ValueError("game_count must be positive")

    sequence_payload = json.loads(sequence_path.read_text(encoding="utf-8"))
    first_sequence_run = record_python_sequence_trajectory(sequence_payload)
    second_sequence_run = record_python_sequence_trajectory(sequence_payload)
    sequence_replay_match = first_sequence_run == second_sequence_run
    if not sequence_replay_match:
        raise AssertionError("Python sequence replay diverged for the same generated payload")

    exact_seeded_parity_count = 0
    mismatch_examples: list[dict[str, Any]] = []

    for seed_value in range(seed_start, seed_start + game_count):
        python_trajectory = record_seeded_python_trajectory(seed_value)
        mojo_trajectory = record_seeded_mojo_trajectory(seed_value)

        if python_trajectory == mojo_trajectory:
            exact_seeded_parity_count += 1
            continue

        if len(mismatch_examples) < 3:
            mismatch_examples.append(
                {
                    "seed": seed_value,
                    "python_initial": python_trajectory[0],
                    "mojo_initial": mojo_trajectory[0],
                    "python_final": python_trajectory[-1],
                    "mojo_final": mojo_trajectory[-1],
                }
            )

    print("=== Cross Validation ===")
    print(f"Sequence file: {sequence_path}")
    print(f"Python sequence replay match: {sequence_replay_match}")
    print(f"Seeded corpus size: {game_count}")
    print(f"Exact seeded parity matches: {exact_seeded_parity_count}")
    print(
        "Note: exact cross-engine seeded parity is expected to diverge until the Mojo engine "
        "supports injected random streams."
    )
    print("{")
    print(f'  "sequence_file": "{sequence_path}",')
    print(f'  "python_sequence_replay_match": {str(sequence_replay_match).lower()},')
    print(f'  "seeded_corpus_size": {game_count},')
    print(f'  "exact_seeded_parity_matches": {exact_seeded_parity_count},')
    print('  "exact_seeded_parity_supported": false,')
    print('  "note": "Mojo bridge currently uses internal RNG; pre-generated stream injection is only available in the Python baseline.",')
    print(f'  "mismatch_examples": {json.dumps(mismatch_examples)}')
    print("}")


if __name__ == "__main__":
    main()
