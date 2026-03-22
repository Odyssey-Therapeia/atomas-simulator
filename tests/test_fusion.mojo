from nucleo.fusion import (
    resolve_black_plus,
    resolve_board,
    resolve_plus,
)
from nucleo.game_state import BLACK_PLUS, GameState, PLUS
from nucleo.ring import recalculate_atom_count, recalculate_highest
from std.testing import TestSuite, assert_equal, assert_raises


def set_state_pieces(mut game: GameState, var pieces: List[Int8]):
    game.pieces = pieces^
    recalculate_atom_count(game)
    recalculate_highest(game)


def test_simple_plus_reaction_creates_single_higher_atom() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(3), PLUS, Int8(3)])

    var result = resolve_plus(game, 1)

    assert_equal(result[0], 6)
    assert_equal(result[1], 0)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 4)


def test_canonical_chain_reaction_collapses_to_eleven() raises:
    var game = GameState()
    set_state_pieces(
        game,
        [
            Int8(9),
            Int8(3),
            Int8(3),
            Int8(3),
            PLUS,
            Int8(3),
            Int8(3),
            Int8(3),
            Int8(9),
        ],
    )

    var result = resolve_plus(game, 4)

    assert_equal(result[0], 76)
    assert_equal(result[1], 0)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 11)


def test_plus_reaction_wraps_across_ring_edges() raises:
    var game = GameState()
    set_state_pieces(game, [PLUS, Int8(3), Int8(3)])

    var result = resolve_plus(game, 0)

    assert_equal(result[0], 6)
    assert_equal(result[1], 0)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 4)


def test_black_plus_fuses_non_matching_neighbors() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(5), BLACK_PLUS, Int8(16)])

    var result = resolve_black_plus(game, 1)

    assert_equal(result[0], 10)
    assert_equal(result[1], 0)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 19)


def test_black_plus_can_fuse_plus_tokens_as_value_one() raises:
    var game = GameState()
    set_state_pieces(game, [PLUS, BLACK_PLUS, PLUS])

    var result = resolve_black_plus(game, 1)

    assert_equal(result[0], 1)
    assert_equal(result[1], 0)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 4)


def test_non_matching_plus_persists_without_reacting() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(3), PLUS, Int8(5)])

    var result = resolve_plus(game, 1)

    assert_equal(result[0], 0)
    assert_equal(result[1], 1)
    assert_equal(len(game.pieces), 3)
    assert_equal(game.pieces[0], 3)
    assert_equal(game.pieces[1], PLUS)
    assert_equal(game.pieces[2], 5)


def test_board_scan_triggers_existing_plus_after_later_change() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(3), PLUS, Int8(5)])
    game.pieces[2] = 3
    recalculate_atom_count(game)
    recalculate_highest(game)

    var score = resolve_board(game, 2)

    assert_equal(score, 6)
    assert_equal(len(game.pieces), 1)
    assert_equal(game.pieces[0], 4)


def test_black_plus_with_single_neighbor_persists() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(2), BLACK_PLUS])

    var score = resolve_board(game, 1)

    assert_equal(score, 0)
    assert_equal(len(game.pieces), 2)
    assert_equal(game.pieces[0], 2)
    assert_equal(game.pieces[1], BLACK_PLUS)


def test_board_scan_prefers_counter_clockwise_plus() raises:
    var game = GameState()
    set_state_pieces(game, [PLUS, Int8(2), PLUS, Int8(2)])

    var score = resolve_board(game, 1)

    assert_equal(score, 4)
    assert_equal(len(game.pieces), 2)
    assert_equal(game.pieces[0], 3)
    assert_equal(game.pieces[1], PLUS)


def test_plus_chain_reaction_raises_on_int8_overflow() raises:
    var game = GameState()
    set_state_pieces(
        game,
        [
            Int8(126),
            Int8(126),
            Int8(126),
            PLUS,
            Int8(126),
            Int8(126),
            Int8(126),
        ],
    )

    with assert_raises(contains="Int8 overflow"):
        _ = resolve_plus(game, 3)


def test_black_plus_raises_on_int8_overflow() raises:
    var game = GameState()
    set_state_pieces(game, [Int8(125), BLACK_PLUS, Int8(125)])

    with assert_raises(contains="Int8 overflow"):
        _ = resolve_black_plus(game, 1)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
