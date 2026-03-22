from env import MAX_ACTIONS, NucleoEnv
from observation import (
    OBSERVATION_SIZE,
    TOKEN_SLOT_COUNT,
    get_canonical_observation,
    get_observation,
)
from wrappers import linear_reward, normalized_reward, shaped_reward

from nucleo.game_state import GameState
from nucleo.ring import recalculate_atom_count, recalculate_highest
from std.testing import TestSuite, assert_equal, assert_true


def test_observation_includes_metadata_slots() raises:
    var game = GameState(game_seed=11)
    var observation = get_observation(game)

    assert_equal(observation[TOKEN_SLOT_COUNT], game.current_piece)
    assert_equal(observation[TOKEN_SLOT_COUNT + 1], 0)
    assert_equal(observation[TOKEN_SLOT_COUNT + 2], game.held_piece)
    assert_equal(observation[TOKEN_SLOT_COUNT + 3], 0)


def test_canonical_observation_rotates_highest_atom_to_front() raises:
    var game = GameState()
    game.pieces = [Int8(2), Int8(5), Int8(1)]
    recalculate_atom_count(game)
    recalculate_highest(game)
    game.current_piece = 3

    var observation = get_canonical_observation(game)

    assert_equal(observation[0], 5)
    assert_equal(observation[1], 1)
    assert_equal(observation[2], 2)
    assert_equal(observation[TOKEN_SLOT_COUNT], 3)


def test_env_reset_and_action_mask_are_padded() raises:
    var env = NucleoEnv(13)
    var observation = env.reset()
    var mask = env.legal_actions()
    var legal_count = 0

    for index in range(MAX_ACTIONS):
        if mask[index]:
            legal_count += 1

    assert_equal(env.action_space(), MAX_ACTIONS)
    assert_equal(env.observation_space(), (OBSERVATION_SIZE, -4, 127))
    assert_true(legal_count > 0)
    assert_equal(observation[TOKEN_SLOT_COUNT + 1], 0)


def test_reward_wrappers_shape_and_normalize_values() raises:
    assert_equal(linear_reward(4), 4.0)
    assert_equal(shaped_reward(4, -1), 4.1)
    assert_equal(shaped_reward(4, 1), 3.9)
    assert_equal(normalized_reward(64.0), 1.0)
    assert_equal(normalized_reward(-64.0), -1.0)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
