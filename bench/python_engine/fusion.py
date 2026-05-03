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
    if value <= 0 or value > INT8_ATOM_MAX:
        raise ValueError(
            f"{context}: Int8 overflow: value={value}, max={INT8_ATOM_MAX}"
        )


def min3(a: int, b: int, c: int) -> int:
    result = a
    if b < result:
        result = b
    if c < result:
        result = c
    return result


def max3(a: int, b: int, c: int) -> int:
    result = a
    if b > result:
        result = b
    if c > result:
        result = c
    return result


def middle3(a: int, b: int, c: int) -> int:
    return a + b + c - min3(a, b, c) - max3(a, b, c)


def plus_can_react(state: GameState, plus_idx: int) -> bool:
    if state.token_count < 3:
        return False

    left_idx = left_neighbor(state, plus_idx)
    right_idx = right_neighbor(state, plus_idx)

    if left_idx == plus_idx or right_idx == plus_idx or left_idx == right_idx:
        return False

    left_token = state.pieces[left_idx]
    right_token = state.pieces[right_idx]
    return left_token > 0 and right_token > 0 and left_token == right_token


def black_plus_can_react(state: GameState, bp_idx: int) -> bool:
    if state.token_count < 3:
        return False

    left_idx = left_neighbor(state, bp_idx)
    right_idx = right_neighbor(state, bp_idx)

    if left_idx == bp_idx or right_idx == bp_idx or left_idx == right_idx:
        return False

    left_value = effective_value(state.pieces[left_idx])
    right_value = effective_value(state.pieces[right_idx])
    return left_value > 0 and right_value > 0


def chain_react(state: GameState, center_idx: int, depth: int) -> tuple[int, int]:
    """Recursive symmetric chain around a center atom; returns (score_delta, center_index)."""
    if state.token_count < 3:
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
    """Run all reactions CCW from ``placement_idx``; returns (total_score, best_merged_atom_value)."""
    total_score = 0
    reward = 0
    scan_origin = placement_idx
    should_continue = True

    while should_continue:
        should_continue = False
        best_idx = -1
        best_ccw = state.token_count + 1

        for index in range(state.token_count):
            token = state.pieces[index]
            can_react = False

            if token == PLUS:
                can_react = plus_can_react(state, index)
            elif token == BLACK_PLUS:
                can_react = black_plus_can_react(state, index)

            if can_react:
                current_ccw = ccw_distance(scan_origin, index, state.token_count)

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
            if result_idx < state.token_count and int(state.pieces[result_idx]) > reward:
                reward = int(state.pieces[result_idx])
            scan_origin = result_idx
            should_continue = True

    return (total_score, reward)


def resolve_board(state: GameState, placement_idx: int) -> int:
    """Total reaction score from ``placement_idx`` scan (reward discarded)."""
    outcome = resolve_board_outcome(state, placement_idx)
    return outcome[0]
