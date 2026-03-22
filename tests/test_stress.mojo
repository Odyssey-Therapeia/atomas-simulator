from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step, update_terminal_state
from nucleo.game_state import EMPTY, GameState
from std.random import random_si64
from std.testing import TestSuite, assert_equal, assert_false, assert_true


comptime STRESS_GAME_COUNT: Int = 10_000
comptime MAX_STEPS_PER_GAME: Int = 5_000


def choose_random_legal_action(
    mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int
) raises -> Int:
    var legal_indices: List[Int] = []

    for index in range(valid_count):
        if mask[index]:
            legal_indices.append(index)

    assert_true(len(legal_indices) > 0)
    var choice = Int(random_si64(0, Int64(len(legal_indices) - 1)))
    return legal_indices[choice]


def positive_count(state: GameState) -> Int:
    var count = 0

    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > 0:
            count += 1

    return count


def expected_highest_atom(state: GameState) -> Int8:
    var highest = EMPTY
    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > highest:
            highest = token

    return highest


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
    assert_true(state.score >= previous_score)
    assert_true(state.score >= 0)
    assert_true(state.current_piece != EMPTY or state.is_terminal)
    var expected_state = state
    update_terminal_state(expected_state)
    assert_equal(state.is_terminal, expected_state.is_terminal)


def test_stress_10k_games_pass_all_invariants() raises:
    for seed_value in range(STRESS_GAME_COUNT):
        var game = GameState(game_seed=seed_value)
        var previous_score = 0
        var step_count = 0

        assert_game_invariants(game, previous_score)

        while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
            var mask_result = legal_actions(game)
            var has_legal_action = False

            for index in range(mask_result[1]):
                if mask_result[0][index]:
                    has_legal_action = True
                    break

            assert_true(has_legal_action)

            var action = choose_random_legal_action(
                mask_result[0], mask_result[1]
            )
            _ = step(game, action)
            assert_game_invariants(game, previous_score)
            previous_score = game.score
            step_count += 1

        assert_true(game.is_terminal)
        assert_false(step_count >= MAX_STEPS_PER_GAME)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
