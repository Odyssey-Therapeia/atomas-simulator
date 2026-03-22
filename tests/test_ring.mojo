from nucleo.game_state import BLACK_PLUS, EMPTY, GameState, PLUS
from nucleo.ring import (
    ccw_distance,
    effective_value,
    insert_at,
    left_neighbor,
    recalculate_atom_count,
    recalculate_highest,
    remove_at,
    right_neighbor,
)
from std.testing import TestSuite, assert_equal


def test_insert_at_beginning_updates_counts() raises:
    var game = GameState()
    game.pieces = [Int8(2), Int8(3)]
    game.atom_count = 2
    game.highest_atom = 3

    insert_at(game, 0, Int8(1))

    assert_equal(len(game.pieces), 3)
    assert_equal(game.pieces[0], 1)
    assert_equal(game.pieces[1], 2)
    assert_equal(game.pieces[2], 3)
    assert_equal(game.atom_count, 3)
    assert_equal(game.highest_atom, 3)


def test_insert_at_middle_and_end_preserves_order() raises:
    var game = GameState()
    game.pieces = [Int8(1), Int8(4)]
    game.atom_count = 2
    game.highest_atom = 4

    insert_at(game, 1, PLUS)
    insert_at(game, len(game.pieces), BLACK_PLUS)

    assert_equal(len(game.pieces), 4)
    assert_equal(game.pieces[0], 1)
    assert_equal(game.pieces[1], PLUS)
    assert_equal(game.pieces[2], 4)
    assert_equal(game.pieces[3], BLACK_PLUS)
    assert_equal(game.atom_count, 2)
    assert_equal(game.highest_atom, 4)


def test_remove_at_returns_token_and_updates_counts() raises:
    var game = GameState()
    game.pieces = [Int8(1), PLUS, Int8(5), BLACK_PLUS]
    game.atom_count = 2
    game.highest_atom = 5

    var removed = remove_at(game, 2)

    assert_equal(removed, 5)
    assert_equal(len(game.pieces), 3)
    assert_equal(game.pieces[0], 1)
    assert_equal(game.pieces[1], PLUS)
    assert_equal(game.pieces[2], BLACK_PLUS)
    assert_equal(game.atom_count, 1)
    assert_equal(game.highest_atom, 1)


def test_circular_neighbors_wrap_at_edges() raises:
    var game = GameState()
    game.pieces = [Int8(2), PLUS, Int8(7)]

    assert_equal(left_neighbor(game, 0), 2)
    assert_equal(right_neighbor(game, 0), 1)
    assert_equal(left_neighbor(game, 2), 1)
    assert_equal(right_neighbor(game, 2), 0)


def test_recalculate_helpers_ignore_special_tokens() raises:
    var game = GameState()
    game.pieces = [PLUS, Int8(4), BLACK_PLUS, EMPTY, Int8(2)]

    recalculate_atom_count(game)
    recalculate_highest(game)

    assert_equal(game.atom_count, 2)
    assert_equal(game.highest_atom, 4)


def test_effective_value_and_ccw_distance_follow_spec() raises:
    assert_equal(effective_value(Int8(9)), 9)
    assert_equal(effective_value(PLUS), 1)
    assert_equal(effective_value(BLACK_PLUS), 1)
    assert_equal(effective_value(EMPTY), 0)

    assert_equal(ccw_distance(1, 1, 5), 0)
    assert_equal(ccw_distance(1, 0, 5), 1)
    assert_equal(ccw_distance(1, 4, 5), 2)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
