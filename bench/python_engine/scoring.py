"""Score contributions for reactions and end-game (Mojo ``scoring.mojo`` port)."""

from __future__ import annotations

from .game_state import GameState
from .ring import effective_value


def simple_reaction_score(atom_value: int) -> int:
    """Score for the first Plus merge from a matching pair."""
    return (3 * (atom_value + 1)) // 2


def chain_reaction_score(center: int, outer: int, depth: int) -> int:
    """Score for a chain step; uses integer division like Mojo ``Int``."""
    multiplier = depth + 2
    base_score = (multiplier * (int(center) + 1)) // 2
    if outer < center:
        return base_score
    return base_score + multiplier * (int(outer) - int(center) + 1)


def black_plus_score(left: int, right: int) -> int:
    """Black Plus merge base score from effective neighbor values."""
    left_value = int(effective_value(left))
    right_value = int(effective_value(right))
    return (left_value + right_value) // 2


def end_game_bonus(state: GameState) -> int:
    """Sum of positive atom values still on the ring."""
    total = 0
    for token in state.pieces:
        if token > 0:
            total += int(token)
    return total
