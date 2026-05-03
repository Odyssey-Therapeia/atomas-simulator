from helpers import set_pieces
from nucleo.game_state import BLACK_PLUS, GameState, HYDROGEN, NEUTRINO, PLUS
from nucleo.spawn import spawn_initial_board, spawn_piece
from std.testing import TestSuite, assert_equal, assert_false, assert_true


def test_spawn_initial_board_creates_six_atoms_in_range() raises:
    var game = GameState(game_seed=11)
    spawn_initial_board(game)

    assert_equal(game.token_count, 6)
    assert_equal(game.atom_count, 6)

    for index in range(game.token_count):
        var token = game.pieces[index]
        assert_true(token >= 1 and token <= 3)


def test_plus_is_forced_after_five_non_plus_turns() raises:
    var game = GameState(game_seed=7)
    game.highest_atom = 6
    game.moves_since_plus = 5

    spawn_piece(game)

    assert_equal(game.current_piece, PLUS)
    assert_equal(game.moves_since_plus, 0)


def test_black_plus_never_spawns_below_score_gate() raises:
    var game = GameState(game_seed=17)
    game.highest_atom = 6
    game.score = 749

    for _ in range(256):
        game.moves_since_plus = 0
        spawn_piece(game)
        assert_false(game.current_piece == BLACK_PLUS)


def test_neutrino_never_spawns_below_score_gate() raises:
    var game = GameState(game_seed=29)
    game.highest_atom = 6
    game.score = 1499

    for _ in range(256):
        game.moves_since_plus = 0
        spawn_piece(game)
        assert_false(game.current_piece == NEUTRINO)


def test_pity_spawn_can_emit_straggler_value() raises:
    var game = GameState(game_seed=41)
    set_pieces(game, [Int8(1), Int8(6)])
    var saw_straggler = False

    for _ in range(64):
        game.moves_since_plus = 0
        spawn_piece(game)
        if game.current_piece == 1:
            saw_straggler = True

    assert_true(saw_straggler)


def test_highest_atom_one_always_spawns_hydrogen() raises:
    var game = GameState(game_seed=59)
    game.highest_atom = HYDROGEN
    game.moves_since_plus = 0

    spawn_piece(game)

    assert_equal(game.current_piece, HYDROGEN)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
