from nucleo.game_state import BLACK_PLUS, GameState, PLUS
from nucleo.ring import (
    ccw_distance,
    effective_value,
    insert_at,
    left_neighbor,
    recalculate_highest,
    remove_at,
    right_neighbor,
)
from nucleo.scoring import (
    black_plus_score,
    chain_reaction_score,
    simple_reaction_score,
)


def min3(a: Int, b: Int, c: Int) -> Int:
    var result = a

    if b < result:
        result = b

    if c < result:
        result = c

    return result


def max3(a: Int, b: Int, c: Int) -> Int:
    var result = a

    if b > result:
        result = b

    if c > result:
        result = c

    return result


def middle3(a: Int, b: Int, c: Int) -> Int:
    return a + b + c - min3(a, b, c) - max3(a, b, c)


def plus_can_react(state: GameState, plus_idx: Int) -> Bool:
    if len(state.pieces) < 3:
        return False

    var left_idx = left_neighbor(state, plus_idx)
    var right_idx = right_neighbor(state, plus_idx)

    if left_idx == plus_idx or right_idx == plus_idx or left_idx == right_idx:
        return False

    var left_token = state.pieces[left_idx]
    var right_token = state.pieces[right_idx]
    return left_token > 0 and right_token > 0 and left_token == right_token


def black_plus_can_react(state: GameState, bp_idx: Int) -> Bool:
    if len(state.pieces) < 3:
        return False

    var left_idx = left_neighbor(state, bp_idx)
    var right_idx = right_neighbor(state, bp_idx)

    if left_idx == bp_idx or right_idx == bp_idx or left_idx == right_idx:
        return False

    var left_value = effective_value(state.pieces[left_idx])
    var right_value = effective_value(state.pieces[right_idx])
    return left_value > 0 and right_value > 0


def chain_react(
    mut state: GameState, center_idx: Int, depth: Int
) raises -> Tuple[Int, Int]:
    if len(state.pieces) < 3:
        return (0, center_idx)

    var left_idx = left_neighbor(state, center_idx)
    var right_idx = right_neighbor(state, center_idx)

    if (
        left_idx == center_idx
        or right_idx == center_idx
        or left_idx == right_idx
    ):
        return (0, center_idx)

    var left_token = state.pieces[left_idx]
    var right_token = state.pieces[right_idx]

    if left_token <= 0 or right_token <= 0 or left_token != right_token:
        return (0, center_idx)

    var center_value = state.pieces[center_idx]
    var outer_value = left_token
    var score = chain_reaction_score(center_value, outer_value, depth)
    var new_center_value = Int(center_value) + 1

    if outer_value >= center_value:
        new_center_value = Int(outer_value) + 2

    debug_assert(
        new_center_value > 0 and new_center_value <= 127,
        "chain_react: Int8 overflow for merged atom value ",
        new_center_value,
    )
    if new_center_value <= 0 or new_center_value > 127:
        raise Error("chain_react: Int8 overflow")

    var new_center = Int8(new_center_value)

    var high_idx = left_idx
    var low_idx = right_idx

    if left_idx < right_idx:
        high_idx = right_idx
        low_idx = left_idx

    debug_assert(
        high_idx > low_idx,
        "chain_react: removal order invariant violated (high_idx=",
        high_idx,
        ", low_idx=",
        low_idx,
        ")",
    )

    _ = remove_at(state, high_idx)
    _ = remove_at(state, low_idx)

    var adjusted_center = center_idx
    if high_idx < adjusted_center:
        adjusted_center -= 1
    if low_idx < adjusted_center:
        adjusted_center -= 1

    state.pieces[adjusted_center] = new_center
    recalculate_highest(state)

    var next_result = chain_react(state, adjusted_center, depth + 1)
    return (score + next_result[0], next_result[1])


def resolve_plus(mut state: GameState, plus_idx: Int) raises -> Tuple[Int, Int]:
    if not plus_can_react(state, plus_idx):
        return (0, plus_idx)

    var left_idx = left_neighbor(state, plus_idx)
    var right_idx = right_neighbor(state, plus_idx)
    var left_value = state.pieces[left_idx]
    var score = simple_reaction_score(Int(left_value))
    var merged_value_int = Int(left_value) + 1

    debug_assert(
        merged_value_int > 0 and merged_value_int <= 127,
        "resolve_plus: Int8 overflow for merged atom value ",
        merged_value_int,
    )
    if merged_value_int <= 0 or merged_value_int > 127:
        raise Error("resolve_plus: Int8 overflow")

    var merged_value = Int8(merged_value_int)

    var low_idx = min3(left_idx, plus_idx, right_idx)
    var mid_idx = middle3(left_idx, plus_idx, right_idx)
    var high_idx = max3(left_idx, plus_idx, right_idx)

    debug_assert(
        high_idx > mid_idx and mid_idx > low_idx,
        "resolve_plus: removal order invariant violated (high_idx=",
        high_idx,
        ", mid_idx=",
        mid_idx,
        ", low_idx=",
        low_idx,
        ")",
    )

    _ = remove_at(state, high_idx)
    _ = remove_at(state, mid_idx)
    _ = remove_at(state, low_idx)
    insert_at(state, low_idx, merged_value)

    var chain_result = chain_react(state, low_idx, 2)
    score += chain_result[0]
    return (score, chain_result[1])


def resolve_black_plus(
    mut state: GameState, bp_idx: Int
) raises -> Tuple[Int, Int]:
    if not black_plus_can_react(state, bp_idx):
        return (0, bp_idx)

    var left_idx = left_neighbor(state, bp_idx)
    var right_idx = right_neighbor(state, bp_idx)
    var left_value = effective_value(state.pieces[left_idx])
    var right_value = effective_value(state.pieces[right_idx])
    var score = black_plus_score(
        state.pieces[left_idx], state.pieces[right_idx]
    )
    var merged_value_int = Int(left_value) + 3

    if right_value > left_value:
        merged_value_int = Int(right_value) + 3

    debug_assert(
        merged_value_int > 0 and merged_value_int <= 127,
        "resolve_black_plus: Int8 overflow for merged atom value ",
        merged_value_int,
    )
    if merged_value_int <= 0 or merged_value_int > 127:
        raise Error("resolve_black_plus: Int8 overflow")

    var merged_value = Int8(merged_value_int)

    var low_idx = min3(left_idx, bp_idx, right_idx)
    var mid_idx = middle3(left_idx, bp_idx, right_idx)
    var high_idx = max3(left_idx, bp_idx, right_idx)

    debug_assert(
        high_idx > mid_idx and mid_idx > low_idx,
        "resolve_black_plus: removal order invariant violated (high_idx=",
        high_idx,
        ", mid_idx=",
        mid_idx,
        ", low_idx=",
        low_idx,
        ")",
    )

    _ = remove_at(state, high_idx)
    _ = remove_at(state, mid_idx)
    _ = remove_at(state, low_idx)
    insert_at(state, low_idx, merged_value)

    var chain_result = chain_react(state, low_idx, 2)
    score += chain_result[0]
    return (score, chain_result[1])


def resolve_board_outcome(
    mut state: GameState, placement_idx: Int
) raises -> Tuple[Int, Int]:
    var total_score = 0
    var reward = 0
    var scan_origin = placement_idx
    var should_continue = True

    while should_continue:
        should_continue = False
        var best_idx = -1
        var best_ccw = len(state.pieces) + 1

        for index in range(len(state.pieces)):
            var token = state.pieces[index]
            var can_react = False

            if token == PLUS:
                can_react = plus_can_react(state, index)
            elif token == BLACK_PLUS:
                can_react = black_plus_can_react(state, index)

            if can_react:
                var current_ccw = ccw_distance(
                    scan_origin, index, len(state.pieces)
                )

                if best_idx < 0 or current_ccw < best_ccw:
                    best_idx = index
                    best_ccw = current_ccw

        if best_idx >= 0:
            var selected_token = state.pieces[best_idx]
            var result: Tuple[Int, Int]
            if selected_token == BLACK_PLUS:
                result = resolve_black_plus(state, best_idx)
            else:
                result = resolve_plus(state, best_idx)

            total_score += result[0]
            if (
                result[1] < len(state.pieces)
                and Int(state.pieces[result[1]]) > reward
            ):
                reward = Int(state.pieces[result[1]])
            scan_origin = result[1]
            should_continue = True

    return (total_score, reward)


def resolve_board(mut state: GameState, placement_idx: Int) raises -> Int:
    var outcome = resolve_board_outcome(state, placement_idx)
    return outcome[0]
