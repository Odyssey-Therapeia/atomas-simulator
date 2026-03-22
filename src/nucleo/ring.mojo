from nucleo.game_state import (
    BLACK_PLUS,
    EMPTY,
    GameState,
    HYDROGEN,
    PLUS,
)


def insert_at(mut state: GameState, position: Int, token: Int8):
    var new_pieces: List[Int8] = []

    for index in range(len(state.pieces) + 1):
        if index == position:
            new_pieces.append(token)

        if index < len(state.pieces):
            new_pieces.append(state.pieces[index])

    state.pieces = new_pieces^

    if token > 0:
        state.atom_count += 1
        if token > state.highest_atom:
            state.highest_atom = token


def remove_at(mut state: GameState, position: Int) -> Int8:
    var removed = state.pieces[position]
    var new_pieces: List[Int8] = []

    for index in range(len(state.pieces)):
        if index != position:
            new_pieces.append(state.pieces[index])

    state.pieces = new_pieces^

    if removed > 0:
        state.atom_count -= 1
        recalculate_highest(state)

    return removed


def left_neighbor(state: GameState, index: Int) -> Int:
    if len(state.pieces) == 0:
        return index

    return (index - 1 + len(state.pieces)) % len(state.pieces)


def right_neighbor(state: GameState, index: Int) -> Int:
    if len(state.pieces) == 0:
        return index

    return (index + 1) % len(state.pieces)


def recalculate_highest(mut state: GameState):
    var highest = HYDROGEN

    for token in state.pieces:
        if token > highest:
            highest = token

    state.highest_atom = highest


def recalculate_atom_count(mut state: GameState):
    var count = 0

    for token in state.pieces:
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
