"""Shared engine constants matching ``src/nucleo/game_state.mojo``."""

from typing import Final

MAX_ATOMS: Final[int] = 18

EMPTY: Final[int] = 0
HYDROGEN: Final[int] = 1
PLUS: Final[int] = -1
MINUS: Final[int] = -2
BLACK_PLUS: Final[int] = -3
NEUTRINO: Final[int] = -4

PLUS_SPAWN_RATE: Final[float] = 0.17
MINUS_SPAWN_RATE: Final[float] = 0.05
BLACK_PLUS_SPAWN_RATE: Final[float] = 0.0125
NEUTRINO_SPAWN_RATE: Final[float] = 0.0167

BLACK_PLUS_SCORE_GATE: Final[int] = 750
NEUTRINO_SCORE_GATE: Final[int] = 1500

INT8_ATOM_MAX: Final[int] = 127
