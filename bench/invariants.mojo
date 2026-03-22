from nucleo.game_state import EMPTY, GameState, MAX_ATOMS, MAX_RING_CAPACITY
from std.testing import assert_equal, assert_true


def expected_highest_atom(state: GameState) -> Int8:
    var highest = EMPTY
    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > highest:
            highest = token

    return highest


def expected_terminal_state(state: GameState) -> Bool:
    if state.atom_count > MAX_ATOMS:
        return True

    if state.atom_count < MAX_ATOMS:
        return False

    if state.holding_piece:
        return False

    return state.current_piece > 0


def assert_game_invariants(state: GameState, previous_score: Int) raises:
    var actual_atom_count = 0
    var has_only_valid_tokens = True

    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > 0:
            actual_atom_count += 1

        if token < -4 or token > 127:
            has_only_valid_tokens = False

    assert_equal(state.atom_count, actual_atom_count)
    assert_equal(state.highest_atom, expected_highest_atom(state))
    assert_true(has_only_valid_tokens)
    assert_true(state.atom_count >= 0)
    assert_true(state.token_count >= state.atom_count)
    assert_true(state.token_count <= MAX_RING_CAPACITY)
    assert_true(state.score >= previous_score)
    assert_true(state.score >= 0)
    assert_true(state.current_piece != EMPTY or state.is_terminal)
    assert_equal(state.is_terminal, expected_terminal_state(state))
