from nucleo.actions import legal_actions, step
from nucleo.game_state import EMPTY, GameState, MAX_ATOMS
from std.random import random_si64
from std.testing import TestSuite, assert_equal, assert_true


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


def max_positive(pieces: List[Int8]) -> Int8:
    var highest = Int8(1)

    for token in pieces:
        if token > highest:
            highest = token

    return highest


def test_seeded_games_run_to_completion_without_breaking_invariants() raises:
    for seed_value in range(100):
        var game = GameState(game_seed=seed_value)
        var turn_limit = 2000

        while not game.is_terminal and game.move_count < turn_limit:
            var mask = legal_actions(game)
            var action = choose_random_legal_action(mask)
            _ = step(game, action)

            assert_equal(game.atom_count, positive_count(game.pieces))
            assert_equal(game.highest_atom, max_positive(game.pieces))
            assert_true(game.current_piece != EMPTY or game.is_terminal)
            assert_true(game.atom_count <= MAX_ATOMS or game.is_terminal)

        assert_true(game.is_terminal)
        assert_true(game.move_count < turn_limit)
        assert_true(game.score >= 0)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
