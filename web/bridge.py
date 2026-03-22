from __future__ import annotations

import contextlib
import importlib
import io
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
ENGINE_MODULE_NAME = "python_module"
ENGINE_LIB = ROOT / f"{ENGINE_MODULE_NAME}.so"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_engine_module():
    stderr_buffer = io.StringIO()
    with contextlib.redirect_stderr(stderr_buffer):
        try:
            return importlib.import_module(ENGINE_MODULE_NAME)
        except ModuleNotFoundError:
            subprocess.run(
                [
                    "pixi",
                    "run",
                    "mojo",
                    "build",
                    "-I",
                    str(SRC_DIR),
                    str(SRC_DIR / "nucleo" / "python_module.mojo"),
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
            return importlib.import_module(ENGINE_MODULE_NAME)


nucleo_engine = load_engine_module()


def normalize_state(payload: dict[str, Any]) -> dict[str, Any]:
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


class NucleoGame:
    def __init__(self, seed: int | None = None) -> None:
        self._game = (
            nucleo_engine.Game(seed)
            if seed is not None
            else nucleo_engine.Game()
        )

    def reset(self) -> dict[str, Any]:
        return normalize_state(dict(self._game.reset()))

    def step(self, action: int) -> tuple[dict[str, Any], int, bool, dict[str, Any]]:
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
        return [bool(item) for item in self._game.legal_actions()]

    def get_state(self) -> dict[str, Any]:
        return normalize_state(dict(self._game.get_state()))
