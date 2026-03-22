from game_state import (
    BLACK_PLUS,
    EMPTY,
    GameState,
    MAX_RING_SIZE,
    MINUS,
    PLUS,
)
from std.testing import TestSuite, assert_equal, assert_false, assert_true


def test_reset_produces_valid_state() raises:
    var game = GameState()
    game.reset()

    assert_equal(game.ring_size, 0)
    assert_equal(game.score, 0)
    assert_equal(game.move_count, 0)
    assert_equal(game.highest_element, 1)
    assert_equal(game.absorbed_element, EMPTY)
    assert_false(game.holding_absorbed)
    assert_false(game.is_terminal)


def test_ring_empty_after_reset() raises:
    var game = GameState()
    game.reset()

    for index in range(MAX_RING_SIZE):
        assert_equal(game.ring[index], EMPTY)


def test_current_piece_valid_after_reset() raises:
    var game = GameState()
    game.reset()

    assert_true(game.current_piece > 0)


def test_spawn_piece_respects_value_window_or_special_items() raises:
    var game = GameState()
    game.reset()
    game.highest_element = 6

    for _ in range(256):
        game.spawn_piece()

        var piece = game.current_piece
        var is_special = piece == PLUS or piece == MINUS or piece == BLACK_PLUS
        var is_regular = piece >= 2 and piece <= 5

        assert_true(is_special or is_regular)


def test_special_item_constants_match_spec() raises:
    assert_equal(PLUS, -1)
    assert_equal(MINUS, -2)
    assert_equal(BLACK_PLUS, -3)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
