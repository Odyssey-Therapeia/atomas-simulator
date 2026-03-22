"""Dynamic ring helpers (Mojo ``ring.mojo`` port)."""

from __future__ import annotations

from .constants import BLACK_PLUS, EMPTY, HYDROGEN, PLUS
from .game_state import GameState


def insert_at(state: GameState, position: int, token: int) -> None:
    """
    Insert a token into the game state's pieces at the given position and update derived atom statistics.
    
    Inserts `token` into `state.pieces` at `position` (0 through len(state.pieces)). If `token` is greater than zero, increments `state.atom_count` and updates `state.highest_atom` when `token` exceeds the current highest value.
    
    Parameters:
        state (GameState): The game state to modify.
        position (int): Index at which to insert the token (0..len).
        token (int): Token value to insert; values greater than zero are treated as atoms.
    """
    state.pieces.insert(position, token)
    if token > 0:
        state.atom_count += 1
        if token > state.highest_atom:
            state.highest_atom = token


def remove_at(state: GameState, position: int) -> int:
    """
    Remove and return the token at the given position and update derived state if the removed token is an atom.
    
    Parameters:
        state (GameState): The game state whose pieces will be modified; if the removed token is > 0 this will decrement `state.atom_count` and recompute `state.highest_atom`.
        position (int): Index in `state.pieces` of the token to remove.
    
    Returns:
        int: The token value that was removed from `state.pieces`.
    """
    removed = state.pieces.pop(position)
    if removed > 0:
        state.atom_count -= 1
        recalculate_highest(state)
    return removed


def left_neighbor(state: GameState, index: int) -> int:
    """
    Return the index of the left (counter-clockwise) neighbor of a given position on the ring.
    
    Parameters:
        state (GameState): Game state containing the circular `pieces` sequence.
        index (int): Current position index in `state.pieces`.
    
    Returns:
        int: The index of the left neighbor wrapped around the ring; if `state.pieces` is empty, returns `index` unchanged.
    """
    if len(state.pieces) == 0:
        return index
    return (index - 1 + len(state.pieces)) % len(state.pieces)


def right_neighbor(state: GameState, index: int) -> int:
    """
    Compute the index of the right neighbor on the ring, wrapping to the start when needed.
    
    Parameters:
        state (GameState): Game state whose `pieces` list defines the ring.
        index (int): Current position on the ring.
    
    Returns:
        int: The index one step to the right (clockwise) from `index` modulo the ring size; if `state.pieces` is empty, returns `index` unchanged.
    """
    if len(state.pieces) == 0:
        return index
    return (index + 1) % len(state.pieces)


def recalculate_highest(state: GameState) -> None:
    """
    Update state's highest_atom to the largest positive token present in state.pieces; set to EMPTY if state.pieces is empty or contains no positive tokens.
    """
    if len(state.pieces) == 0:
        state.highest_atom = EMPTY
        return

    highest = EMPTY
    for token in state.pieces:
        if token > highest:
            highest = token
    state.highest_atom = highest


def recalculate_atom_count(state: GameState) -> None:
    """
    Recalculate the GameState's atom_count as the number of tokens in state.pieces greater than zero.
    
    Updates state.atom_count in place.
    """
    count = 0
    for token in state.pieces:
        if token > 0:
            count += 1
    state.atom_count = count


def effective_value(token: int) -> int:
    """
    Map a token to the atom value used for Black Plus neighbor calculations.
    
    Positive tokens return their numeric value; `PLUS` and `BLACK_PLUS` return `HYDROGEN`; all other tokens return `EMPTY`.
    
    Returns:
        int: `HYDROGEN` if `token` is `PLUS` or `BLACK_PLUS`, `token` if `token > 0`, `EMPTY` otherwise.
    """
    if token > 0:
        return token
    if token == PLUS or token == BLACK_PLUS:
        return HYDROGEN
    return EMPTY


def ccw_distance(from_idx: int, to_idx: int, ring_size: int) -> int:
    """Counter-clockwise steps from ``to_idx`` to ``from_idx`` on a ring of ``ring_size``."""
    return (from_idx - to_idx + ring_size) % ring_size
