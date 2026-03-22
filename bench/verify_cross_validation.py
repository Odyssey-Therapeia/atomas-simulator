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
        return cls(
            seed_value=int(payload["seed"]),
            floats=[float(value) for value in payload["floats"]],
            ints=[int(value) for value in payload["ints"]],
        )

    def seed(self, seed_value: int | None = None) -> None:
        if seed_value is not None and seed_value != self.seed_value:
            raise ValueError(
                f"SequenceRNG seed mismatch: expected {self.seed_value}, got {seed_value}"
            )
        self.float_index = 0
        self.int_index = 0

    def random(self) -> float:
        if self.float_index >= len(self.floats):
            raise IndexError("SequenceRNG exhausted float sequence")
        value = self.floats[self.float_index]
        self.float_index += 1
        return value

    def randint(self, lower: int, upper: int) -> int:
        if self.int_index >= len(self.ints):
            raise IndexError("SequenceRNG exhausted int sequence")
        raw_value = self.ints[self.int_index]
        self.int_index += 1
        return lower + (raw_value % (upper - lower + 1))


def parse_arg_or_default(index: int, default: int) -> int:
    if len(sys.argv) > index:
        return int(sys.argv[index])
    return default


def normalize_python_state(state: PythonGameState) -> dict[str, Any]:
    return {
        "pieces": [int(token) for token in state.pieces[: state.token_count]],
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
    pieces_payload = payload["pieces"]
    token_count = int(payload.get("token_count", len(pieces_payload)))
    return {
        "pieces": [int(token) for token in pieces_payload[:token_count]],
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
        self._game = python_module.Game(seed) if seed is not None else python_module.Game()

    def get_state(self) -> dict[str, Any]:
        return normalize_mojo_state(dict(self._game.get_state()))

    def step(self, action: int) -> tuple[dict[str, Any], int, bool]:
        payload = dict(self._game.step(action))
        state = normalize_mojo_state(dict(payload["state"]))
        reward = int(payload["reward"])
        done = bool(payload["done"])
        return state, reward, done

    def legal_actions(self) -> list[bool]:
        return [bool(item) for item in self._game.legal_actions()]


def choose_first_legal_action(mask: list[bool]) -> int:
    for index, is_legal in enumerate(mask):
        if is_legal:
            return index
    raise ValueError("choose_first_legal_action: no legal actions available")


def choose_random_action_from_state_rng(state: PythonGameState, mask: list[bool]) -> int:
    legal_indices = [index for index, is_legal in enumerate(mask) if is_legal]
    if not legal_indices:
        raise ValueError("choose_random_action_from_state_rng: no legal actions available")
    return legal_indices[state.randint(0, len(legal_indices) - 1)]


def record_python_sequence_trajectory(sequence_payload: dict[str, Any]) -> list[dict[str, Any]]:
    game = PythonGameState(rng_seed=int(sequence_payload["seed"]))
    game._rng = SequenceRNG.from_payload(sequence_payload)
    if int(sequence_payload["seed"]) != game.rng_seed:
        raise RuntimeError(
            "record_python_sequence_trajectory: sequence seed does not match "
            f"game seed ({sequence_payload['seed']} != {game.rng_seed})"
        )
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
    report = {
        "sequence_file": str(sequence_path),
        "python_sequence_replay_match": sequence_replay_match,
        "seeded_corpus_size": game_count,
        "exact_seeded_parity_matches": exact_seeded_parity_count,
        "exact_seeded_parity_supported": False,
        "note": "Mojo bridge currently uses internal RNG; pre-generated stream injection is only available in the Python baseline.",
        "mismatch_examples": mismatch_examples,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
