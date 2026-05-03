from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.real_atomas.parsers import (
    parse_achievement_progress,
    parse_achievements,
    parse_atoms_info,
    parse_gamestate,
    parse_preferences_plist,
    parse_strings_file,
)


FIXTURES = ROOT / "tests" / "fixtures" / "real_atomas"


def test_parse_atoms_info_preserves_order_and_colors() -> None:
    atoms = parse_atoms_info(FIXTURES / "atoms_sample.info")

    assert [atom.atomic_number for atom in atoms] == [1, 2, 3, 4, 5]
    assert atoms[0].symbol == "X"
    assert atoms[0].name == "Testium"
    assert atoms[0].rgb == (10, 20, 30)
    assert atoms[3].symbol == "Q"
    assert atoms[3].name == "Parsium"


def test_parse_achievement_definitions_extracts_nested_records() -> None:
    achievements = parse_achievements(FIXTURES / "achievements_sample.xml")

    score = achievements["score_sample"]
    assert score.title == "Sample score"
    assert score.hidden is False
    assert score.externs["apple"] == "score_sample"
    assert score.rewards["antimatter"] == "1"
    assert score.counters["classic_points"] == "100"
    assert score.info["challenge"] == "1"
    assert achievements["hidden_sample"].hidden is True
    assert achievements["hidden_sample"].counters["highest_element"] == "4"


def test_parse_achievement_progress_extracts_progress_and_counters() -> None:
    progress = parse_achievement_progress(FIXTURES / "ac_save_sanitized.xml")

    assert progress.counters == {"highest_element": 4, "classic_points": 75}
    assert progress.achievements["score_sample"].unlocked is True
    assert progress.achievements["hidden_sample"].progress == 0.75


def test_parse_gamestate_preserves_unknown_scalars_and_bubbles() -> None:
    state = parse_gamestate(FIXTURES / "gss_tutorial_sanitized.sg")

    assert state.scalars["mc"] == 9
    assert state.scalars["hv"] == 4
    assert state.scalars["lc"] == -1
    assert len(state.bubbles) == 18
    assert state.bubbles[0].family == 0
    assert state.bubbles[0].value == 0
    assert state.bubbles[0].raw_attributes["fr"] == "0"
    assert state.center_bubble.family == 1
    assert state.next_atom.family == 0


def test_parse_preferences_plist_keeps_known_and_raw_values() -> None:
    preferences = parse_preferences_plist(FIXTURES / "preferences_sample.plist")

    assert preferences.high_scores["classic"] == 75
    assert preferences.last_elements["classic"] == 3
    assert preferences.selected_main_atom == 3
    assert preferences.values["hide_ads"] is True


def test_parse_strings_file_accepts_simple_key_value_rows() -> None:
    strings = parse_strings_file(FIXTURES / "strings_sample.strings")

    assert strings["sample.rule"] == "Place sample tokens on the ring"
    assert strings["sample.upgrade"] == "10% more Sample Tokens"
    assert strings["sample.no_semicolon"] == "Parser accepts final line without semicolon"
