"""Dynamic ring helpers (Mojo ``ring.mojo`` port)."""

from __future__ import annotations

from .constants import BLACK_PLUS, EMPTY, HYDROGEN, PLUS
from .game_state import GameState


def insert_at(state: GameState, position: int, token: int) -> None:
    """Insert ``token`` at ``position`` (0..len); updates atom stats when positive."""
    state.pieces.insert(position, token)
    state.token_count += 1
    if token > 0:
        state.atom_count += 1
        if token > state.highest_atom:
            state.highest_atom = token


def remove_at(state: GameState, position: int) -> int:
    """Remove and return the token at ``position``; may recalculate highest atom."""
    removed = state.pieces.pop(position)
    state.token_count -= 1
    if removed > 0:
        state.atom_count -= 1
        if removed == state.highest_atom:
            recalculate_highest(state)
    return removed


def left_neighbor(state: GameState, index: int) -> int:
    if state.token_count == 0:
        return index
    return (index - 1 + state.token_count) % state.token_count


def right_neighbor(state: GameState, index: int) -> int:
    if state.token_count == 0:
        return index
    return (index + 1) % state.token_count


def recalculate_highest(state: GameState) -> None:
    """Highest positive atom on the ring, or ``EMPTY`` if none (empty ring or specials-only)."""
    if state.token_count == 0:
        state.highest_atom = EMPTY
        return

    highest = EMPTY
    for index in range(state.token_count):
        token = state.pieces[index]
        if token > highest:
            highest = token
    state.highest_atom = highest


def recalculate_atom_count(state: GameState) -> None:
    """Recompute ``atom_count`` from positive tokens."""
    count = 0
    for index in range(state.token_count):
        token = state.pieces[index]
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
