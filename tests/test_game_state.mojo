from nucleo.game_state import (
    BLACK_PLUS,
    EMPTY,
    GameState,
    HYDROGEN,
    MAX_ATOMS,
    MINUS,
    NEUTRINO,
    PLUS,
)
from std.testing import TestSuite, assert_equal, assert_false, assert_true


def test_reset_produces_seeded_opening_board() raises:
    var game = GameState(game_seed=1234)
    game.reset()

    assert_equal(len(game.pieces), 6)
    assert_equal(game.atom_count, 6)
    assert_equal(game.score, 0)
    assert_equal(game.move_count, 0)
    assert_true(game.highest_atom >= HYDROGEN and game.highest_atom <= 3)
    assert_true(game.current_piece != EMPTY)
    assert_false(game.is_terminal)

    for token in game.pieces:
        assert_true(token >= HYDROGEN and token <= 3)


def test_reset_with_same_seed_is_reproducible() raises:
    var game_one = GameState(game_seed=77)
    var game_two = GameState(game_seed=77)

    assert_equal(len(game_one.pieces), len(game_two.pieces))
    for index in range(len(game_one.pieces)):
        assert_equal(game_one.pieces[index], game_two.pieces[index])

    assert_equal(game_one.current_piece, game_two.current_piece)
    assert_equal(game_one.highest_atom, game_two.highest_atom)


def test_reset_clears_transient_state() raises:
    var game = GameState(game_seed=44)
    game.score = 99
    game.move_count = 12
    game.holding_piece = True
    game.held_piece = 9
    game.held_can_convert = True
    game.is_terminal = True
    game.reset()

    assert_false(game.holding_piece)
    assert_equal(game.held_piece, EMPTY)
    assert_false(game.held_can_convert)
    assert_false(game.is_terminal)
    assert_equal(game.score, 0)
    assert_equal(game.move_count, 0)
    assert_equal(game.atom_count, 6)


def test_seed_argument_is_stored() raises:
    var game = GameState(game_seed=1234)

    assert_equal(game.rng_seed, 1234)


def test_special_item_constants_match_spec() raises:
    assert_equal(MAX_ATOMS, 18)
    assert_equal(PLUS, -1)
    assert_equal(MINUS, -2)
    assert_equal(BLACK_PLUS, -3)
    assert_equal(NEUTRINO, -4)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
