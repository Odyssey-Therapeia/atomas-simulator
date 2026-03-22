"""Score contributions for reactions and end-game (Mojo ``scoring.mojo`` port)."""

from __future__ import annotations

from .game_state import GameState
from .ring import effective_value


def simple_reaction_score(atom_value: int) -> int:
    """
    Score for the first Plus merge produced by merging a matching pair.
    
    Parameters:
        atom_value (int): Atom's integer value used to compute the merge score.
    
    Returns:
        int: The computed score for that merge.
    """
    return (3 * (atom_value + 1)) // 2


def chain_reaction_score(center: int, outer: int, depth: int) -> int:
    """
    Calculate the score contribution for a single chain reaction step.
    
    The score scales with chain depth and the central atom value; if the outer atom's value is greater than or equal to the center, additional points proportional to their difference are added.
    
    Parameters:
        center (int): Baseline atom value at the reaction center.
        outer (int): Neighbor atom value compared against the center.
        depth (int): Chain depth (non-negative integer) used to scale the score.
    
    Returns:
        int: The computed integer score for this chain step.
    """
    multiplier = depth + 2
    base_score = (multiplier * (int(center) + 1)) // 2
    if outer < center:
        return base_score
    return base_score + multiplier * (int(outer) - int(center) + 1)


def black_plus_score(left: int, right: int) -> int:
    """
    Compute the base Black Plus merge score by averaging the effective values of two neighbor tokens.
    
    Parameters:
        left (int): Left neighbor token value; its effective value is used in the computation.
        right (int): Right neighbor token value; its effective value is used in the computation.
    
    Returns:
        int: The integer average of the two effective neighbor values (computed with floor division).
    """
    left_value = int(effective_value(left))
    right_value = int(effective_value(right))
    return (left_value + right_value) // 2


def end_game_bonus(state: GameState) -> int:
    """
    Compute the end-game bonus by summing positive atom values remaining on the ring.
    
    Parameters:
        state (GameState): Game state containing the ring pieces to evaluate.
    
    Returns:
        total (int): Sum of all positive token values found in state.pieces.
    """
    total = 0
    for token in state.pieces:
        if token > 0:
            total += int(token)
    return total
