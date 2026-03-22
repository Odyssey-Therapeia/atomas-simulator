from nucleo.actions import legal_actions, step
from nucleo.game_state import EMPTY, GameState, MAX_ATOMS
from std.random import random_si64
from std.testing import TestSuite, assert_equal, assert_false, assert_true


comptime STRESS_GAME_COUNT: Int = 10_000
comptime MAX_STEPS_PER_GAME: Int = 5_000


def choose_random_legal_action(mask: List[Bool]) raises -> Int:
    var legal_indices: List[Int] = []

    for index in range(len(mask)):
        if mask[index]:
            legal_indices.append(index)

    assert_true(len(legal_indices) > 0)
    var choice = Int(random_si64(0, Int64(len(legal_indices) - 1)))
    return legal_indices[choice]


def positive_count(pieces: List[Int8]) -> Int:
    var count = 0

    for token in pieces:
        if token > 0:
            count += 1

    return count


def expected_highest_atom(pieces: List[Int8]) -> Int8:
    var highest = EMPTY
    for token in pieces:
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

    for token in state.pieces:
        if token > 0:
            actual_atom_count += 1

        if token < -4 or token > 127:
            has_only_valid_tokens = False

    assert_equal(state.atom_count, actual_atom_count)
    assert_equal(state.highest_atom, expected_highest_atom(state.pieces))
    assert_true(has_only_valid_tokens)
    assert_true(state.atom_count >= 0)
    assert_true(len(state.pieces) >= state.atom_count)
    assert_true(state.score >= previous_score)
    assert_true(state.score >= 0)
    assert_true(state.current_piece != EMPTY or state.is_terminal)
    assert_equal(state.is_terminal, expected_terminal_state(state))


def test_stress_10k_games_pass_all_invariants() raises:
    for seed_value in range(STRESS_GAME_COUNT):
        var game = GameState(game_seed=seed_value)
        var previous_score = 0
        var step_count = 0

        assert_game_invariants(game, previous_score)

        while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
            var mask = legal_actions(game)
            var has_legal_action = False

            for item in mask:
                if item:
                    has_legal_action = True
                    break

            assert_true(has_legal_action)

            var action = choose_random_legal_action(mask)
            _ = step(game, action)
            assert_game_invariants(game, previous_score)
            previous_score = game.score
            step_count += 1

        assert_true(game.is_terminal)
        assert_false(step_count >= MAX_STEPS_PER_GAME)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
