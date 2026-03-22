from std.random import random_si64

from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step
from nucleo.game_state import GameState


def choose_random_legal_action(
    mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int
) raises -> Int:
    var legal_indices: List[Int] = []

    for index in range(valid_count):
        if mask[index]:
            legal_indices.append(index)

    if len(legal_indices) == 0:
        raise Error("No legal actions available for current game state")

    var choice = Int(random_si64(0, Int64(len(legal_indices) - 1)))
    return legal_indices[choice]


def main() raises:
    var game = GameState()

    print("=== Nucleo Game Engine ===")
    print("Opening state:")
    print(game)

    while not game.is_terminal:
        var mask_result = legal_actions(game)
        var action = choose_random_legal_action(mask_result[0], mask_result[1])
        var result = step(game, action)

        print(
            "Move:",
            game.move_count,
            "Action:",
            action,
            "Reward:",
            result[0],
            "Done:",
            result[1],
            "Atom count:",
            game.atom_count,
            "Current piece:",
            game.current_piece,
        )

    print("=== Final State ===")
    print(game)
    print("Final score:", game.score)
    print("Moves played:", game.move_count)
