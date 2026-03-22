from game_state import GameState


def main() raises:
    var game = GameState()
    game.reset()

    print("=== Nucleo Game Engine ===")
    print("Initial state after reset:")
    print(game)
    print("Ring size:", game.ring_size)
    print("Current piece:", game.current_piece)
    print("Score:", game.score)
    print("Highest element:", game.highest_element)
    print("Terminal:", game.is_terminal)
