"""Dynamic ring helpers (Mojo ``ring.mojo`` port)."""

from __future__ import annotations

from .constants import BLACK_PLUS, EMPTY, HYDROGEN, PLUS
from .game_state import GameState


def insert_at(state: GameState, position: int, token: int) -> None:
    """Insert ``token`` at ``position`` (0..len); updates atom stats when positive."""
    state.pieces.insert(position, token)
    if token > 0:
        state.atom_count += 1
        if token > state.highest_atom:
            state.highest_atom = token


def remove_at(state: GameState, position: int) -> int:
    """Remove and return the token at ``position``; may recalculate highest atom."""
    removed = state.pieces.pop(position)
    if removed > 0:
        state.atom_count -= 1
        recalculate_highest(state)
    return removed


def left_neighbor(state: GameState, index: int) -> int:
    if len(state.pieces) == 0:
        return index
    return (index - 1 + len(state.pieces)) % len(state.pieces)


def right_neighbor(state: GameState, index: int) -> int:
    if len(state.pieces) == 0:
        return index
    return (index + 1) % len(state.pieces)


def recalculate_highest(state: GameState) -> None:
    """Highest positive atom on the ring, or ``EMPTY`` if none (empty ring or specials-only)."""
    if len(state.pieces) == 0:
        state.highest_atom = EMPTY
        return

    highest = EMPTY
    for token in state.pieces:
        if token > highest:
            highest = token
    state.highest_atom = highest


def recalculate_atom_count(state: GameState) -> None:
    """Recompute ``atom_count`` from positive tokens."""
    count = 0
    for token in state.pieces:
        if token > 0:
            count += 1
    state.atom_count = count


def effective_value(token: int) -> int:
    """Value used for Black Plus neighbor math; specials map like Mojo."""
    if token > 0:
        return token
    if token == PLUS or token == BLACK_PLUS:
        return HYDROGEN
    return EMPTY


def ccw_distance(from_idx: int, to_idx: int, ring_size: int) -> int:
    """Counter-clockwise steps from ``to_idx`` to ``from_idx`` on a ring of ``ring_size``."""
    return (from_idx - to_idx + ring_size) % ring_size
