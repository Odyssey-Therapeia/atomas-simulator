from helpers import set_pieces
from nucleo.game_state import BLACK_PLUS, GameState, PLUS
from nucleo.scoring import (
    black_plus_score,
    chain_reaction_score,
    end_game_bonus,
    simple_reaction_score,
)
from std.testing import TestSuite, assert_equal


def test_simple_reaction_score_matches_fluorine_example() raises:
    assert_equal(simple_reaction_score(9), 15)


def test_chain_reaction_score_matches_plus_one_wiki_examples() raises:
    assert_equal(chain_reaction_score(Int8(10), Int8(3), 2), 22)
    assert_equal(chain_reaction_score(Int8(11), Int8(3), 3), 30)


def test_chain_reaction_score_matches_plus_two_case() raises:
    assert_equal(chain_reaction_score(Int8(6), Int8(9), 2), 30)


def test_black_plus_score_uses_average_of_effective_values() raises:
    assert_equal(black_plus_score(Int8(5), Int8(16)), 10)
    assert_equal(black_plus_score(PLUS, BLACK_PLUS), 1)


def test_end_game_bonus_ignores_non_atoms() raises:
    var game = GameState()
    set_pieces(game, [Int8(3), PLUS, Int8(9), BLACK_PLUS])

    assert_equal(end_game_bonus(game), 12)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
