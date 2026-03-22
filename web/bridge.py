from __future__ import annotations

import contextlib
import importlib
import io
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
ENGINE_MODULE_NAME = "python_module"
ENGINE_LIB = ROOT / f"{ENGINE_MODULE_NAME}.so"
ENGINE_SOURCE = SRC_DIR / "nucleo" / "python_module.mojo"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_engine_module() -> None:
    subprocess.run(
        [
            "pixi",
            "run",
            "mojo",
            "build",
            "-I",
            str(SRC_DIR),
            str(ENGINE_SOURCE),
            "--emit",
            "shared-lib",
            "-o",
            str(ENGINE_LIB),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def load_engine_module():
    if not ENGINE_LIB.exists() or ENGINE_LIB.stat().st_mtime < ENGINE_SOURCE.stat().st_mtime:
        build_engine_module()
        importlib.invalidate_caches()
        sys.modules.pop(ENGINE_MODULE_NAME, None)

    stderr_buffer = io.StringIO()
    with contextlib.redirect_stderr(stderr_buffer):
        try:
            return importlib.import_module(ENGINE_MODULE_NAME)
        except ModuleNotFoundError:
            build_engine_module()
            importlib.invalidate_caches()
            sys.modules.pop(ENGINE_MODULE_NAME, None)
            return importlib.import_module(ENGINE_MODULE_NAME)


nucleo_engine = load_engine_module()


def normalize_state(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a raw engine state payload for JSON responses."""
    required_keys = [
        "pieces",
        "atom_count",
        "current_piece",
        "score",
        "move_count",
        "highest_atom",
        "holding_piece",
        "held_piece",
        "held_can_convert",
        "is_terminal",
        "moves_since_plus",
        "moves_since_minus",
        "rng_seed",
    ]
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise ValueError(
            f"normalize_state missing required keys: {', '.join(missing_keys)}"
        )

    pieces_payload = payload["pieces"]
    if isinstance(pieces_payload, (str, bytes)) or not isinstance(
        pieces_payload, Iterable
    ):
        raise ValueError("normalize_state expected 'pieces' to be an iterable")

    try:
        pieces = [int(token) for token in pieces_payload]
        atom_count = int(payload["atom_count"])
        current_piece = int(payload["current_piece"])
        score = int(payload["score"])
        move_count = int(payload["move_count"])
        highest_atom = int(payload["highest_atom"])
        holding_piece = bool(payload["holding_piece"])
        held_piece = int(payload["held_piece"])
        held_can_convert = bool(payload["held_can_convert"])
        is_terminal = bool(payload["is_terminal"])
        moves_since_plus = int(payload["moves_since_plus"])
        moves_since_minus = int(payload["moves_since_minus"])
        rng_seed = int(payload["rng_seed"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"normalize_state received invalid payload: {error}") from error

    return {
        "pieces": pieces,
        "atom_count": atom_count,
        "current_piece": current_piece,
        "score": score,
        "move_count": move_count,
        "highest_atom": highest_atom,
        "holding_piece": holding_piece,
        "held_piece": held_piece,
        "held_can_convert": held_can_convert,
        "is_terminal": is_terminal,
        "moves_since_plus": moves_since_plus,
        "moves_since_minus": moves_since_minus,
        "rng_seed": rng_seed,
    }


class NucleoGame:
    """Thin Python wrapper around `nucleo_engine.Game` with normalized state."""

    def __init__(self, seed: int | None = None) -> None:
        """Create a new game instance.

        Args:
            seed: Optional deterministic seed passed to `nucleo_engine.Game`.
        """
        self._game = (
            nucleo_engine.Game(seed)
            if seed is not None
            else nucleo_engine.Game()
        )

    def reset(self) -> dict[str, Any]:
        """Reset the game and return the normalized state payload."""
        return normalize_state(dict(self._game.reset()))

    def step(self, action: int) -> tuple[dict[str, Any], int, bool, dict[str, Any]]:
        """Apply one action and return `(state, reward, done, info)`.

        The returned `info` dict includes `legal_actions`, `score`, and
        `atom_count` for downstream callers.
        """
        payload = dict(self._game.step(action))
        state = normalize_state(dict(payload["state"]))
        reward = int(payload["reward"])
        done = bool(payload["done"])
        info = {
            "legal_actions": self.legal_actions(),
            "score": state["score"],
            "atom_count": state["atom_count"],
        }
        return state, reward, done, info

    def legal_actions(self) -> list[bool]:
        """Return the current legal-action mask as a Python `list[bool]`."""
        return [bool(item) for item in self._game.legal_actions()]

    def get_state(self) -> dict[str, Any]:
        """Return the current normalized game state without mutating it."""
        return normalize_state(dict(self._game.get_state()))
