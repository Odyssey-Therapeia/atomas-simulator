"""Board-driven chain reaction resolution (Mojo ``fusion.mojo`` port)."""

from __future__ import annotations

from .constants import BLACK_PLUS, INT8_ATOM_MAX, PLUS
from .game_state import GameState
from .ring import (
    ccw_distance,
    effective_value,
    insert_at,
    left_neighbor,
    recalculate_highest,
    remove_at,
    right_neighbor,
)
from .scoring import (
    black_plus_score,
    chain_reaction_score,
    simple_reaction_score,
)


def _require_int8_merged_atom(value: int, context: str) -> None:
    """
    Ensure a prospective merged atom value falls within the valid 1..INT8_ATOM_MAX range.
    
    Parameters:
        value (int): The prospective merged atom value to validate.
        context (str): Context string used in the error message if validation fails.
    
    Raises:
        ValueError: If `value` is <= 0 or > INT8_ATOM_MAX; message is "<context>: Int8 overflow".
    """
    if value <= 0 or value > INT8_ATOM_MAX:
        raise ValueError(f"{context}: Int8 overflow")


def min3(a: int, b: int, c: int) -> int:
    """
    Return the smallest of three integers.
    
    Returns:
        The smallest value among `a`, `b`, and `c`.
    """
    result = a
    if b < result:
        result = b
    if c < result:
        result = c
    return result


def max3(a: int, b: int, c: int) -> int:
    """
    Get the largest of three integers.
    
    Returns:
        max_value (int): The largest of `a`, `b`, and `c`.
    """
    result = a
    if b > result:
        result = b
    if c > result:
        result = c
    return result


def middle3(a: int, b: int, c: int) -> int:
    """
    Return the middle (median) value among three integers.
    
    If two or three inputs are equal, the repeated value is returned.
    
    Parameters:
        a (int): First integer.
        b (int): Second integer.
        c (int): Third integer.
    
    Returns:
        int: The value that is neither the minimum nor the maximum of the three (the median).
    """
    return a + b + c - min3(a, b, c) - max3(a, b, c)


def plus_can_react(state: GameState, plus_idx: int) -> bool:
    """
    Check whether a PLUS token at the given index can react with its immediate neighbors.
    
    Parameters:
        state (GameState): Current board state containing `pieces`.
        plus_idx (int): Index of the PLUS token to test.
    
    Returns:
        bool: `true` if the ring has at least three pieces, the left and right neighbors are distinct valid indices, both neighbor tokens are greater than zero, and the two neighbor tokens are equal; `false` otherwise.
    """
    if len(state.pieces) < 3:
        return False

    left_idx = left_neighbor(state, plus_idx)
    right_idx = right_neighbor(state, plus_idx)

    if left_idx == plus_idx or right_idx == plus_idx or left_idx == right_idx:
        return False

    left_token = state.pieces[left_idx]
    right_token = state.pieces[right_idx]
    return left_token > 0 and right_token > 0 and left_token == right_token


def black_plus_can_react(state: GameState, bp_idx: int) -> bool:
    """
    Determine whether a BLACK_PLUS at the given index can react with its immediate ring neighbors.
    
    Parameters:
        state (GameState): Current game state containing the circular `pieces` array.
        bp_idx (int): Index of the BLACK_PLUS token to test.
    
    Returns:
        bool: `True` if both neighboring tokens' effective values are greater than zero, `False` otherwise.
    """
    if len(state.pieces) < 3:
        return False

    left_idx = left_neighbor(state, bp_idx)
    right_idx = right_neighbor(state, bp_idx)

    if left_idx == bp_idx or right_idx == bp_idx or left_idx == right_idx:
        return False

    left_value = effective_value(state.pieces[left_idx])
    right_value = effective_value(state.pieces[right_idx])
    return left_value > 0 and right_value > 0


def chain_react(state: GameState, center_idx: int, depth: int) -> tuple[int, int]:
    """
    Perform a symmetric chain reaction centered at a given index, merging matching outer atoms repeatedly and accumulating score.
    
    If the two immediate neighbors of the center are positive and equal, they are removed and the center is replaced by a merged atom; the process then recurses outward while increasing depth, accumulating chain reaction score.
    
    Parameters:
        depth (int): Recursion depth used when computing chain reaction score; increase by 1 for each recursive step.
    
    Returns:
        tuple[int, int]: (total_score_delta, resulting_center_index) where `total_score_delta` is the sum of scores produced by this chain (including nested reactions) and `resulting_center_index` is the index of the merged center in the current board after resolution.
    
    Raises:
        ValueError: If the computed merged atom value is outside the allowed 1..INT8_ATOM_MAX range.
    """
    if len(state.pieces) < 3:
        return (0, center_idx)

    left_idx = left_neighbor(state, center_idx)
    right_idx = right_neighbor(state, center_idx)

    if left_idx == center_idx or right_idx == center_idx or left_idx == right_idx:
        return (0, center_idx)

    left_token = state.pieces[left_idx]
    right_token = state.pieces[right_idx]

    if left_token <= 0 or right_token <= 0 or left_token != right_token:
        return (0, center_idx)

    center_value = state.pieces[center_idx]
    outer_value = left_token
    score = chain_reaction_score(center_value, outer_value, depth)
    new_center_value = int(center_value) + 1

    if outer_value >= center_value:
        new_center_value = int(outer_value) + 2

    _require_int8_merged_atom(new_center_value, "chain_react")
    new_center = int(new_center_value)

    high_idx = left_idx
    low_idx = right_idx
    if left_idx < right_idx:
        high_idx = right_idx
        low_idx = left_idx

    remove_at(state, high_idx)
    remove_at(state, low_idx)

    adjusted_center = center_idx
    if high_idx < adjusted_center:
        adjusted_center -= 1
    if low_idx < adjusted_center:
        adjusted_center -= 1

    state.pieces[adjusted_center] = new_center
    recalculate_highest(state)

    next_score, next_idx = chain_react(state, adjusted_center, depth + 1)
    return (score + next_score, next_idx)


def resolve_plus(state: GameState, plus_idx: int) -> tuple[int, int]:
    """
    Resolve a PLUS fusion at the specified index, replace the three involved atoms with the merged atom, and continue any resulting symmetric chain reactions.
    
    Parameters:
    	state (GameState): Current game state containing the circular ring of pieces.
    	plus_idx (int): Index of the PLUS token to resolve.
    
    Returns:
    	result (tuple[int, int]): (total_score, result_index) where `total_score` is the score gained from this resolution including subsequent chain reactions, and `result_index` is the index of the merged atom after all resulting updates.
    """
    if not plus_can_react(state, plus_idx):
        return (0, plus_idx)

    left_idx = left_neighbor(state, plus_idx)
    right_idx = right_neighbor(state, plus_idx)
    left_value = state.pieces[left_idx]
    score = simple_reaction_score(int(left_value))
    merged_value_int = int(left_value) + 1

    _require_int8_merged_atom(merged_value_int, "resolve_plus")
    merged_value = int(merged_value_int)

    low_idx = min3(left_idx, plus_idx, right_idx)
    mid_idx = middle3(left_idx, plus_idx, right_idx)
    high_idx = max3(left_idx, plus_idx, right_idx)

    remove_at(state, high_idx)
    remove_at(state, mid_idx)
    remove_at(state, low_idx)
    insert_at(state, low_idx, merged_value)

    chain_score, chain_idx = chain_react(state, low_idx, 2)
    score += chain_score
    return (score, chain_idx)


def resolve_black_plus(state: GameState, bp_idx: int) -> tuple[int, int]:
    """
    Resolve a reactive BLACK_PLUS token at the given index, merging it with its neighbors and applying any resulting chain reactions.
    
    Parameters:
        state (GameState): Current game ring state.
        bp_idx (int): Index of the BLACK_PLUS token to resolve.
    
    Returns:
        tuple[int, int]: A pair (score, result_idx) where `score` is the total points gained from this resolution including subsequent chain reactions, and `result_idx` is the index of the merged atom after resolution.
    
    Raises:
        ValueError: If the computed merged atom value is outside the allowed int8 range.
    """
    if not black_plus_can_react(state, bp_idx):
        return (0, bp_idx)

    left_idx = left_neighbor(state, bp_idx)
    right_idx = right_neighbor(state, bp_idx)
    left_value = effective_value(state.pieces[left_idx])
    right_value = effective_value(state.pieces[right_idx])
    score = black_plus_score(state.pieces[left_idx], state.pieces[right_idx])
    merged_value_int = int(left_value) + 3

    if right_value > left_value:
        merged_value_int = int(right_value) + 3

    _require_int8_merged_atom(merged_value_int, "resolve_black_plus")
    merged_value = int(merged_value_int)

    low_idx = min3(left_idx, bp_idx, right_idx)
    mid_idx = middle3(left_idx, bp_idx, right_idx)
    high_idx = max3(left_idx, bp_idx, right_idx)

    remove_at(state, high_idx)
    remove_at(state, mid_idx)
    remove_at(state, low_idx)
    insert_at(state, low_idx, merged_value)

    chain_score, chain_idx = chain_react(state, low_idx, 2)
    score += chain_score
    return (score, chain_idx)


def resolve_board_outcome(state: GameState, placement_idx: int) -> tuple[int, int]:
    """
    Scan the board for reactions starting at placement_idx and resolve them until no further reactions occur.
    
    The scan proceeds counter-clockwise from placement_idx, repeatedly selecting the nearest reactable PLUS or BLACK_PLUS token, resolving that reaction (including any resulting chain reactions), accumulating score, and tracking the largest merged-atom value produced.
    
    Parameters:
        placement_idx (int): Index on the ring from which counter-clockwise scanning begins.
    
    Returns:
        total_score (int): Sum of scores from all resolved reactions.
        reward (int): Highest merged-atom value produced during resolution (0 if no merges occurred).
    """
    total_score = 0
    reward = 0
    scan_origin = placement_idx
    should_continue = True

    while should_continue:
        should_continue = False
        best_idx = -1
        best_ccw = len(state.pieces) + 1

        for index in range(len(state.pieces)):
            token = state.pieces[index]
            can_react = False

            if token == PLUS:
                can_react = plus_can_react(state, index)
            elif token == BLACK_PLUS:
                can_react = black_plus_can_react(state, index)

            if can_react:
                current_ccw = ccw_distance(scan_origin, index, len(state.pieces))

                if best_idx < 0 or current_ccw < best_ccw:
                    best_idx = index
                    best_ccw = current_ccw

        if best_idx >= 0:
            selected_token = state.pieces[best_idx]
            if selected_token == BLACK_PLUS:
                result_score, result_idx = resolve_black_plus(state, best_idx)
            else:
                result_score, result_idx = resolve_plus(state, best_idx)

            total_score += result_score
            if result_idx < len(state.pieces) and int(state.pieces[result_idx]) > reward:
                reward = int(state.pieces[result_idx])
            scan_origin = result_idx
            should_continue = True

    return (total_score, reward)


def resolve_board(state: GameState, placement_idx: int) -> int:
    """
    Resolve all chain reactions triggered by a placement and return the accumulated reaction score; the per-placement reward is discarded.
    
    Returns:
        total_score (int): Sum of scores produced by all resolved reactions.
    """
    outcome = resolve_board_outcome(state, placement_idx)
    return outcome[0]
