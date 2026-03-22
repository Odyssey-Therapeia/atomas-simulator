from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step
from nucleo.game_state import GameState
from std.testing import TestSuite, assert_equal, assert_true


comptime DETERMINISM_GAME_COUNT: Int = 100
comptime MAX_STEPS_PER_GAME: Int = 5_000


def first_legal_action(
    mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int
) raises -> Int:
    for index in range(valid_count):
        if mask[index]:
            return index

    raise Error("first_legal_action: no legal actions found")


def state_signature(state: GameState) -> List[Int]:
    var signature: List[Int] = []
    signature.append(state.token_count)
    signature.append(state.atom_count)
    signature.append(Int(state.current_piece))
    signature.append(state.score)
    signature.append(state.move_count)
    signature.append(Int(state.highest_atom))
    signature.append(1 if state.holding_piece else 0)
    signature.append(Int(state.held_piece))
    signature.append(1 if state.held_can_convert else 0)
    signature.append(1 if state.is_terminal else 0)
    signature.append(state.moves_since_plus)
    signature.append(state.moves_since_minus)
    signature.append(state.rng_seed)

    for index in range(state.token_count):
        signature.append(Int(state.pieces[index]))

    return signature^


def record_game_trajectory(seed_value: Int) raises -> List[List[Int]]:
    var game = GameState(game_seed=seed_value)
    var trajectory: List[List[Int]] = []
    trajectory.append(state_signature(game))

    var step_count = 0
    while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
        var mask_result = legal_actions(game)
        var action = first_legal_action(mask_result[0], mask_result[1])
        _ = step(game, action)
        trajectory.append(state_signature(game))
        step_count += 1

    assert_true(game.is_terminal)
    assert_true(step_count < MAX_STEPS_PER_GAME)
    return trajectory^


def test_same_seed_produces_identical_trajectories() raises:
    for seed_value in range(DETERMINISM_GAME_COUNT):
        var left_trajectory = record_game_trajectory(seed_value)
        var right_trajectory = record_game_trajectory(seed_value)

        assert_equal(len(left_trajectory), len(right_trajectory))
        for index in range(len(left_trajectory)):
            assert_equal(left_trajectory[index], right_trajectory[index])


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
