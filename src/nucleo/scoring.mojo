from nucleo.game_state import GameState
from nucleo.ring import effective_value


def simple_reaction_score(atom_value: Int) -> Int:
    return (3 * (atom_value + 1)) / 2


def chain_reaction_score(center: Int8, outer: Int8, depth: Int) -> Int:
    var multiplier = depth + 2
    var base_score = (multiplier * (Int(center) + 1)) / 2

    if outer < center:
        return base_score

    return base_score + multiplier * (Int(outer) - Int(center) + 1)


def black_plus_score(left: Int8, right: Int8) -> Int:
    var left_value = Int(effective_value(left))
    var right_value = Int(effective_value(right))
    return (left_value + right_value) / 2


def end_game_bonus(state: GameState) -> Int:
    var total = 0

    for token in state.pieces:
        if token > 0:
            total += Int(token)

    return total
