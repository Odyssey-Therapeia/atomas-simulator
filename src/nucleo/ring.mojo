from nucleo.game_state import (
    BLACK_PLUS,
    EMPTY,
    GameState,
    HYDROGEN,
    MAX_RING_CAPACITY,
    PLUS,
)


def insert_at(mut state: GameState, position: Int, token: Int8) raises:
    debug_assert(
        position >= 0 and position <= state.token_count,
        "insert_at: position out of range (position=",
        position,
        ", token_count=",
        state.token_count,
        ")",
    )
    if position < 0 or position > state.token_count:
        raise Error("insert_at: position out of range")

    debug_assert(
        state.token_count < MAX_RING_CAPACITY,
        "insert_at: ring overflow at capacity ",
        MAX_RING_CAPACITY,
    )
    if state.token_count >= MAX_RING_CAPACITY:
        raise Error("insert_at: ring overflow at max capacity")

    for index in range(state.token_count, position, -1):
        state.pieces[index] = state.pieces[index - 1]

    state.pieces[position] = token
    state.token_count += 1

    if token > 0:
        state.atom_count += 1
        if token > state.highest_atom:
            state.highest_atom = token


def remove_at(mut state: GameState, position: Int) raises -> Int8:
    debug_assert(
        position >= 0 and position < state.token_count,
        "remove_at: position out of range (position=",
        position,
        ", token_count=",
        state.token_count,
        ")",
    )
    if position < 0 or position >= state.token_count:
        raise Error("remove_at: position out of range")

    var removed = state.pieces[position]

    for index in range(position, state.token_count - 1):
        state.pieces[index] = state.pieces[index + 1]

    state.token_count -= 1
    state.pieces[state.token_count] = EMPTY

    if removed > 0:
        state.atom_count -= 1
        recalculate_highest(state)

    return removed


def left_neighbor(state: GameState, index: Int) -> Int:
    if state.token_count == 0:
        return index

    return (index - 1 + state.token_count) % state.token_count


def right_neighbor(state: GameState, index: Int) -> Int:
    if state.token_count == 0:
        return index

    return (index + 1) % state.token_count


def recalculate_highest(mut state: GameState):
    # An empty ring has no highest atom, so keep the sentinel as EMPTY.
    if state.token_count == 0:
        state.highest_atom = EMPTY
        return

    # When only specials remain on the ring there is no positive atom to track.
    var highest = EMPTY

    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > highest:
            highest = token

    state.highest_atom = highest


def recalculate_atom_count(mut state: GameState):
    var count = 0

    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > 0:
            count += 1

    state.atom_count = count


def effective_value(token: Int8) -> Int8:
    if token > 0:
        return token

    if token == PLUS or token == BLACK_PLUS:
        return HYDROGEN

    return EMPTY


def ccw_distance(from_idx: Int, to_idx: Int, ring_size: Int) -> Int:
    return (from_idx - to_idx + ring_size) % ring_size
