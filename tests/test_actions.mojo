from helpers import set_pieces
from nucleo.actions import MAX_ACTION_SLOTS, apply_action, legal_actions, step
from nucleo.game_state import EMPTY, GameState, MAX_RING_CAPACITY, MINUS, NEUTRINO, PLUS
from std.testing import (
    TestSuite,
    assert_equal,
    assert_false,
    assert_raises,
    assert_true,
)


def count_true(mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int) -> Int:
    var total = 0

    for index in range(valid_count):
        if mask[index]:
            total += 1

    return total


def test_legal_actions_for_empty_board_allow_first_insert() raises:
    var game = GameState()
    for index in range(MAX_RING_CAPACITY):
        game.pieces[index] = EMPTY
    game.token_count = 0
    game.atom_count = 0
    game.highest_atom = 1
    game.current_piece = 2

    var mask_result = legal_actions(game)

    assert_equal(mask_result[1], 1)
    assert_true(mask_result[0][0])


def test_legal_actions_for_five_tokens_allow_all_gap_inserts() raises:
    var game = GameState()
    set_pieces(game, [Int8(1), Int8(2), Int8(3), Int8(4), Int8(5)])
    game.current_piece = PLUS

    var mask_result = legal_actions(game)

    assert_equal(mask_result[1], 5)
    assert_equal(count_true(mask_result[0], mask_result[1]), 5)


def test_regular_piece_is_blocked_on_full_board_but_specials_are_playable() raises:
    var game = GameState()
    set_pieces(
        game,
        [
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
            Int8(1),
            Int8(2),
        ],
    )

    game.current_piece = 3
    var regular_mask = legal_actions(game)
    assert_equal(count_true(regular_mask[0], regular_mask[1]), 0)

    game.current_piece = PLUS
    var plus_mask = legal_actions(game)
    assert_equal(count_true(plus_mask[0], plus_mask[1]), 18)

    game.current_piece = MINUS
    var minus_mask = legal_actions(game)
    assert_equal(count_true(minus_mask[0], minus_mask[1]), 18)


def test_apply_action_inserts_regular_atom_and_spawns_next_piece() raises:
    var game = GameState(game_seed=13)
    set_pieces(game, [Int8(2), Int8(3)])
    game.current_piece = 4

    var reward = apply_action(game, 1)

    assert_equal(reward, 0)
    assert_equal(game.token_count, 3)
    assert_equal(game.pieces[0], 2)
    assert_equal(game.pieces[1], 4)
    assert_equal(game.pieces[2], 3)
    assert_equal(game.move_count, 1)
    assert_false(game.holding_piece)
    assert_true(game.current_piece != EMPTY)


def test_apply_action_places_matching_plus_and_resolves() raises:
    var game = GameState(game_seed=7)
    set_pieces(game, [Int8(3), Int8(3)])
    game.current_piece = PLUS

    var reward = apply_action(game, 1)

    assert_equal(reward, 4)
    assert_equal(game.token_count, 1)
    assert_equal(game.pieces[0], 4)
    assert_equal(game.move_count, 1)


def test_apply_action_leaves_non_matching_plus_on_ring() raises:
    var game = GameState(game_seed=19)
    set_pieces(game, [Int8(3), Int8(5)])
    game.current_piece = PLUS

    var reward = apply_action(game, 1)

    assert_equal(reward, 0)
    assert_equal(game.token_count, 3)
    assert_equal(game.pieces[0], 3)
    assert_equal(game.pieces[1], PLUS)
    assert_equal(game.pieces[2], 5)
    assert_equal(game.move_count, 1)


def test_minus_absorb_then_place_flow() raises:
    var game = GameState(game_seed=23)
    set_pieces(game, [Int8(2), Int8(4), Int8(2)])
    game.current_piece = MINUS

    var absorb_reward = apply_action(game, 1)

    assert_equal(absorb_reward, 0)
    assert_true(game.holding_piece)
    assert_equal(game.current_piece, 4)
    assert_equal(game.held_piece, 4)
    assert_true(game.held_can_convert)
    assert_equal(game.move_count, 0)
    assert_equal(game.atom_count, 2)

    var place_reward = apply_action(game, 1)

    assert_equal(place_reward, 0)
    assert_false(game.holding_piece)
    assert_equal(game.move_count, 1)
    assert_equal(game.atom_count, 3)


def test_neutrino_copy_then_place_flow() raises:
    var game = GameState(game_seed=31)
    set_pieces(game, [Int8(2), Int8(4)])
    game.current_piece = NEUTRINO

    var copy_reward = apply_action(game, 1)

    assert_equal(copy_reward, 0)
    assert_true(game.holding_piece)
    assert_equal(game.current_piece, 4)
    assert_equal(game.held_piece, 4)
    assert_false(game.held_can_convert)
    assert_equal(game.atom_count, 2)

    var place_reward = apply_action(game, 1)

    assert_equal(place_reward, 0)
    assert_false(game.holding_piece)
    assert_equal(game.move_count, 1)
    assert_equal(game.atom_count, 3)


def test_convert_action_turns_held_minus_piece_into_plus() raises:
    var game = GameState(game_seed=37)
    set_pieces(game, [Int8(2), Int8(4), Int8(2)])
    game.current_piece = MINUS

    _ = apply_action(game, 1)
    var convert_reward = apply_action(game, 2)

    assert_equal(convert_reward, 0)
    assert_false(game.holding_piece)
    assert_equal(game.current_piece, PLUS)
    assert_equal(game.held_piece, EMPTY)
    assert_equal(game.move_count, 0)

    var plus_reward = apply_action(game, 1)

    assert_equal(plus_reward, 3)
    assert_equal(game.token_count, 1)
    assert_equal(game.pieces[0], 3)
    assert_equal(game.move_count, 1)


def test_step_returns_reward_and_done_flag() raises:
    var game = GameState(game_seed=43)
    set_pieces(game, [Int8(3), Int8(3)])
    game.current_piece = PLUS

    var result = step(game, 1)

    assert_equal(result[0], 4)
    assert_false(result[1])


def test_apply_action_rejects_negative_actions() raises:
    var game = GameState(game_seed=47)
    set_pieces(game, [Int8(2), Int8(4)])
    game.current_piece = PLUS

    with assert_raises(contains="non-negative"):
        _ = apply_action(game, -1)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
