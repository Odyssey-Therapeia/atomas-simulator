from nucleo.game_state import EMPTY, GameState, MAX_RING_CAPACITY
from nucleo.ring import recalculate_atom_count, recalculate_highest


def set_pieces(mut game: GameState, var pieces: List[Int8]):
    for index in range(MAX_RING_CAPACITY):
        game.pieces[index] = EMPTY

    game.token_count = len(pieces)
    for index in range(game.token_count):
        game.pieces[index] = pieces[index]

    recalculate_atom_count(game)
    recalculate_highest(game)
