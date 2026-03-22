from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step
from nucleo.game_state import EMPTY, GameState, MAX_ATOMS
from std.random import random_si64
from std.testing import TestSuite, assert_equal, assert_true


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


def max_positive(state: GameState) -> Int8:
    var highest = EMPTY

    for index in range(state.token_count):
        var token = state.pieces[index]
        if token > highest:
            highest = token

    return highest


def test_seeded_games_run_to_completion_without_breaking_invariants() raises:
    for seed_value in range(100):
        var game = GameState(game_seed=seed_value)
        var turn_limit = 2000

        while not game.is_terminal and game.move_count < turn_limit:
            var mask_result = legal_actions(game)
            var action = choose_random_legal_action(
                mask_result[0], mask_result[1]
            )
            _ = step(game, action)

            assert_equal(game.atom_count, positive_count(game))
            assert_equal(game.highest_atom, max_positive(game))
            assert_true(game.current_piece != EMPTY or game.is_terminal)
            assert_true(game.atom_count <= MAX_ATOMS or game.is_terminal)

        assert_true(game.is_terminal)
        assert_true(game.move_count < turn_limit)
        assert_true(game.score >= 0)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
