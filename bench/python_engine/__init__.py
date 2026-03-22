"""
Pure-Python Nucleo engine for benchmarking and cross-validation against Mojo.

Import from a script under ``bench/`` with that directory on ``sys.path``, e.g.::

    from python_engine import GameState, apply_action, step
"""

from .actions import (
    apply_action,
    finish_placement_turn,
    gap_action_count,
    legal_actions,
    step,
    update_terminal_state,
)
from .constants import (
    BLACK_PLUS,
    BLACK_PLUS_SCORE_GATE,
    BLACK_PLUS_SPAWN_RATE,
    EMPTY,
    HYDROGEN,
    INT8_ATOM_MAX,
    MAX_ATOMS,
    MINUS,
    MINUS_SPAWN_RATE,
    NEUTRINO,
    NEUTRINO_SCORE_GATE,
    NEUTRINO_SPAWN_RATE,
    PLUS,
    PLUS_SPAWN_RATE,
)
from .fusion import (
    black_plus_can_react,
    chain_react,
    plus_can_react,
    resolve_black_plus,
    resolve_board,
    resolve_board_outcome,
    resolve_plus,
)
from .game_state import GameState
from .ring import (
    ccw_distance,
    effective_value,
    insert_at,
    left_neighbor,
    recalculate_atom_count,
    recalculate_highest,
    remove_at,
    right_neighbor,
)
from .scoring import black_plus_score, chain_reaction_score, end_game_bonus, simple_reaction_score
from .spawn import spawn_initial_board, spawn_piece

__all__ = [
    "BLACK_PLUS",
    "BLACK_PLUS_SCORE_GATE",
    "BLACK_PLUS_SPAWN_RATE",
    "EMPTY",
    "HYDROGEN",
    "INT8_ATOM_MAX",
    "MAX_ATOMS",
    "MINUS",
    "MINUS_SPAWN_RATE",
    "NEUTRINO",
    "NEUTRINO_SCORE_GATE",
    "NEUTRINO_SPAWN_RATE",
    "PLUS",
    "PLUS_SPAWN_RATE",
    "GameState",
    "apply_action",
    "black_plus_can_react",
    "black_plus_score",
    "ccw_distance",
    "chain_reaction_score",
    "chain_react",
    "effective_value",
    "end_game_bonus",
    "finish_placement_turn",
    "gap_action_count",
    "insert_at",
    "legal_actions",
    "left_neighbor",
    "plus_can_react",
    "recalculate_atom_count",
    "recalculate_highest",
    "remove_at",
    "resolve_black_plus",
    "resolve_board",
    "resolve_board_outcome",
    "resolve_plus",
    "right_neighbor",
    "simple_reaction_score",
    "spawn_initial_board",
    "spawn_piece",
    "step",
    "update_terminal_state",
]
